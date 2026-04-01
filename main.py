import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
import time
from collections import deque
from pathlib import Path
from typing import Any, Deque, Dict, List
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import decky_plugin


class Plugin:
    def __init__(self) -> None:
        self._config: Dict[str, Any] = {
            "provider": "gemini",
            "api_key": "",
            "model": "gemini-2.5-flash",
            "source_language": "Japanese",
            "target_language": "English",
            "max_context_items": 6,
            "overlay_enabled": True,
            "overlay_mode": "notification",
            "overlay_method": "auto",
            "persistent_method": "auto",
            "persistent_preset": "bottom-subtitles",
        }
        self._context: Deque[Dict[str, str]] = deque(maxlen=6)
        self._persistent_overlay_process: Any = None

    async def _main(self) -> None:
        decky_plugin.logger.info("Deck Localize backend started")
        await self._load_config()

    async def _unload(self) -> None:
        await asyncio.to_thread(self._stop_persistent_overlay)
        decky_plugin.logger.info("Deck Localize backend stopped")

    async def _load_config(self) -> None:
        cfg_path = Path(decky_plugin.DECKY_PLUGIN_SETTINGS_DIR) / "deck-localize.json"
        if not cfg_path.exists():
            return
        try:
            parsed = json.loads(cfg_path.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                self._config.update(parsed)
            self._context = deque(maxlen=int(self._config.get("max_context_items", 6)))
        except Exception as exc:
            decky_plugin.logger.error(f"Could not load config: {exc}")

    async def _save_config(self) -> None:
        cfg_path = Path(decky_plugin.DECKY_PLUGIN_SETTINGS_DIR) / "deck-localize.json"
        cfg_path.parent.mkdir(parents=True, exist_ok=True)
        cfg_path.write_text(json.dumps(self._config, indent=2), encoding="utf-8")

    async def get_config(self) -> Dict[str, Any]:
        return {**self._config, "api_key": "", "has_api_key": bool(self._config.get("api_key"))}

    async def set_config(
        self,
        provider: str,
        api_key: str = "",
        model: str = "",
        source_language: str = "Japanese",
        target_language: str = "English",
        max_context_items: int = 6,
        overlay_enabled: bool = True,
        overlay_mode: str = "notification",
        overlay_method: str = "auto",
        persistent_method: str = "auto",
        persistent_preset: str = "bottom-subtitles",
    ) -> Dict[str, Any]:
        selected_preset = self._sanitize_persistent_preset(persistent_preset)
        update: Dict[str, Any] = {
            "provider": provider,
            "model": model,
            "source_language": source_language,
            "target_language": target_language,
            "max_context_items": max(1, min(20, int(max_context_items))),
            "overlay_enabled": bool(overlay_enabled),
            "overlay_mode": str(overlay_mode or "notification"),
            "overlay_method": str(overlay_method or "auto"),
            "persistent_method": str(persistent_method or "auto"),
            "persistent_preset": selected_preset,
        }
        if api_key:
            update["api_key"] = api_key
        self._config.update(update)
        if not self._config["overlay_enabled"] or self._config["overlay_mode"] != "persistent":
            await asyncio.to_thread(self._stop_persistent_overlay)
        self._context = deque(self._context, maxlen=self._config["max_context_items"])
        await self._save_config()
        return {"ok": True}

    async def clear_context(self) -> Dict[str, Any]:
        self._context.clear()
        return {"ok": True}

    async def get_context(self) -> Dict[str, Any]:
        return {"items": list(self._context)}

    async def close_overlay(self) -> Dict[str, Any]:
        closed = await asyncio.to_thread(self._stop_persistent_overlay)
        return {"ok": True, "closed": closed}

    async def capture_and_translate(self) -> Dict[str, Any]:
        api_key = str(self._config.get("api_key", "")).strip()
        if not api_key:
            return {"ok": False, "error": "API key is required."}

        screenshot = await asyncio.to_thread(self._capture_png_bytes)
        if not screenshot:
            return {
                "ok": False,
                "error": "Failed to capture screenshot. Install grim on Steam Deck or ensure a supported capture tool exists.",
            }

        prompt = self._build_prompt()

        provider = str(self._config.get("provider", "gemini")).lower()
        model = str(self._config.get("model", "")).strip()

        try:
            if provider == "claude":
                translation = await asyncio.to_thread(
                    self._call_claude,
                    api_key,
                    model or "claude-3-7-sonnet-latest",
                    screenshot,
                    prompt,
                )
            else:
                translation = await asyncio.to_thread(
                    self._call_gemini,
                    api_key,
                    model or "gemini-2.5-flash",
                    screenshot,
                    prompt,
                )
        except Exception as exc:
            decky_plugin.logger.error(f"Translation failed: {exc}")
            return {"ok": False, "error": str(exc)}

        context_item = {
            "timestamp": str(int(time.time())),
            "translation": translation,
        }
        self._context.append(context_item)
        overlay_result = await asyncio.to_thread(self._show_overlay, translation)

        return {
            "ok": True,
            "translation": translation,
            "context": list(self._context),
            "overlay_shown": overlay_result["shown"],
            "overlay_method": overlay_result["method"],
        }

    def _capture_png_bytes(self) -> bytes:
        commands: List[List[str]] = [
            ["grim", "-t", "png", "-"],
            ["gamescope-screenshot", "--stdout"],
        ]

        for cmd in commands:
            try:
                res = subprocess.run(cmd, capture_output=True, check=True)
                if res.stdout.startswith(b"\x89PNG\r\n\x1a\n"):
                    return res.stdout
            except Exception:
                continue

        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = Path(tmp.name)
            subprocess.run(["grim", str(tmp_path)], check=True)
            blob = tmp_path.read_bytes()
            tmp_path.unlink(missing_ok=True)
            if blob.startswith(b"\x89PNG\r\n\x1a\n"):
                return blob
        except Exception:
            pass

        return b""

    def _build_prompt(self) -> str:
        source = self._config.get("source_language", "Japanese")
        target = self._config.get("target_language", "English")

        context_lines = []
        for item in self._context:
            context_lines.append(f"- {item['translation']}")

        historical = "\n".join(context_lines) if context_lines else "- No prior context"

        return (
            "You are a game localization assistant. "
            f"Read all visible text from this screenshot in {source}. "
            f"Translate to natural {target}. "
            "If OCR text is uncertain, mark uncertain words with [?]. "
            "Return plain text only. Keep line breaks when useful for dialogue.\n\n"
            "Prior translation context:\n"
            f"{historical}"
        )

    def _show_overlay_notification(self, translation: str) -> Dict[str, Any]:
        if not bool(self._config.get("overlay_enabled", True)):
            return {"shown": False, "method": "disabled"}

        method = str(self._config.get("overlay_method", "auto") or "auto").lower()
        text = translation.strip().replace("\n", " ")
        short = (text[:350] + "...") if len(text) > 350 else text

        # Best effort: try Steam Deck-friendly overlay tools first, then desktop notifications.
        attempts: List[Dict[str, Any]] = []
        if method in ["auto", "gamescope-notify"]:
            attempts.extend(
                [
                    {"name": "gamescope-notify", "cmd": ["gamescope-notify", "Deck Localize", short]},
                    {"name": "gamescope-notify", "cmd": ["gamescope-notify", short]},
                ]
            )
        if method in ["auto", "notify-send"]:
            attempts.append(
                {
                    "name": "notify-send",
                    "cmd": ["notify-send", "Deck Localize", short, "-t", "7000"],
                }
            )

        for attempt in attempts:
            cmd = attempt["cmd"]
            exe = cmd[0]
            if shutil.which(exe) is None:
                continue
            try:
                subprocess.run(cmd, check=True, capture_output=True, timeout=5)
                return {"shown": True, "method": attempt["name"]}
            except Exception as exc:
                decky_plugin.logger.warning(f"Overlay method {attempt['name']} failed: {exc}")

        return {"shown": False, "method": "none"}

    def _show_overlay(self, translation: str) -> Dict[str, Any]:
        if not bool(self._config.get("overlay_enabled", True)):
            return {"shown": False, "method": "disabled"}

        mode = str(self._config.get("overlay_mode", "notification") or "notification").lower()
        if mode == "persistent":
            return self._show_persistent_overlay(translation)
        return self._show_overlay_notification(translation)

    def _show_persistent_overlay(self, translation: str) -> Dict[str, Any]:
        method = str(self._config.get("persistent_method", "auto") or "auto").lower()
        preset = self._sanitize_persistent_preset(self._config.get("persistent_preset", "bottom-subtitles"))
        layout = self._persistent_layout(preset)
        text = translation.strip()
        if not text:
            return {"shown": False, "method": "persistent-empty"}

        self._stop_persistent_overlay()

        attempts: List[Dict[str, Any]] = []
        if method in ["auto", "yad"]:
            attempts.append(
                {
                    "name": "persistent-yad",
                    "cmd": [
                        "yad",
                        "--info",
                        "--undecorated",
                        "--skip-taskbar",
                        "--sticky",
                        "--on-top",
                        "--no-buttons",
                        "--title=Deck Localize",
                        f"--geometry={layout['geometry']}",
                        f"--fontname={layout['font']}",
                        f"--text-align={layout['align']}",
                        f"--text={text}",
                    ],
                }
            )
        if method in ["auto", "zenity"]:
            attempts.append(
                {
                    "name": "persistent-zenity",
                    "cmd": [
                        "zenity",
                        "--info",
                        "--title=Deck Localize",
                        f"--text={text}",
                        f"--width={layout['width']}",
                    ],
                }
            )

        for attempt in attempts:
            cmd = attempt["cmd"]
            exe = cmd[0]
            if shutil.which(exe) is None:
                continue
            try:
                self._persistent_overlay_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                return {"shown": True, "method": f"{attempt['name']}:{preset}"}
            except Exception as exc:
                decky_plugin.logger.warning(f"Persistent overlay method {attempt['name']} failed: {exc}")

        return {"shown": False, "method": "persistent-none"}

    def _stop_persistent_overlay(self) -> bool:
        proc = self._persistent_overlay_process
        if not proc:
            return False
        try:
            if proc.poll() is None:
                proc.terminate()
                proc.wait(timeout=2)
        except Exception:
            try:
                proc.kill()
            except Exception:
                pass
        finally:
            self._persistent_overlay_process = None
        return True

    def _sanitize_persistent_preset(self, preset: Any) -> str:
        allowed = {
            "top-bar",
            "bottom-subtitles",
            "center-box",
            "compact-corner",
        }
        value = str(preset or "bottom-subtitles")
        return value if value in allowed else "bottom-subtitles"

    def _persistent_layout(self, preset: str) -> Dict[str, str]:
        # Layouts are tuned for Steam Deck's 1280x800 display; window managers may adjust slightly.
        layouts: Dict[str, Dict[str, str]] = {
            "top-bar": {
                "geometry": "1220x110+30+24",
                "font": "Monospace 15",
                "align": "center",
                "width": "1220",
            },
            "bottom-subtitles": {
                "geometry": "1220x170+30+600",
                "font": "Monospace 17",
                "align": "center",
                "width": "1220",
            },
            "center-box": {
                "geometry": "1000x220+140+290",
                "font": "Monospace 16",
                "align": "center",
                "width": "1000",
            },
            "compact-corner": {
                "geometry": "620x170+630+610",
                "font": "Monospace 14",
                "align": "left",
                "width": "620",
            },
        }
        return layouts.get(preset, layouts["bottom-subtitles"])

    def _call_gemini(self, api_key: str, model: str, png: bytes, prompt: str) -> str:
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{model}:generateContent?key={api_key}"
        )
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inlineData": {
                                "mimeType": "image/png",
                                "data": base64.b64encode(png).decode("utf-8"),
                            }
                        },
                    ]
                }
            ]
        }

        data = json.dumps(payload).encode("utf-8")
        req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")

        try:
            with urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as err:
            raise RuntimeError(f"Gemini HTTP {err.code}: {err.read().decode('utf-8', errors='ignore')}")
        except URLError as err:
            raise RuntimeError(f"Gemini network error: {err}")

        try:
            return body["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception as exc:
            raise RuntimeError(f"Unexpected Gemini response: {exc}")

    def _call_claude(self, api_key: str, model: str, png: bytes, prompt: str) -> str:
        url = "https://api.anthropic.com/v1/messages"
        payload = {
            "model": model,
            "max_tokens": 1200,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": base64.b64encode(png).decode("utf-8"),
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
        }

        data = json.dumps(payload).encode("utf-8")
        req = Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
            method="POST",
        )

        try:
            with urlopen(req, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except HTTPError as err:
            raise RuntimeError(f"Claude HTTP {err.code}: {err.read().decode('utf-8', errors='ignore')}")
        except URLError as err:
            raise RuntimeError(f"Claude network error: {err}")

        try:
            text_parts = [part["text"] for part in body["content"] if part.get("type") == "text"]
            return "\n".join(text_parts).strip()
        except Exception as exc:
            raise RuntimeError(f"Unexpected Claude response: {exc}")
