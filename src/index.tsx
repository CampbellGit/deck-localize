import {
  ButtonItem,
  definePlugin,
  PanelSection,
  PanelSectionRow,
  ServerAPI,
  staticClasses,
  TextField,
} from "decky-frontend-lib";
import { ReactElement, useEffect, useState } from "react";

type ConfigResult = {
  provider: "gemini" | "claude";
  api_key: string;
  has_api_key: boolean;
  model: string;
  source_language: string;
  target_language: string;
  max_context_items: number;
  overlay_enabled: boolean;
  overlay_mode: "notification" | "persistent";
  overlay_method: "auto" | "notify-send" | "gamescope-notify" | "none";
  persistent_method: "auto" | "yad" | "zenity";
  persistent_preset: "top-bar" | "bottom-subtitles" | "center-box" | "compact-corner";
};

type ContextItem = {
  timestamp: string;
  translation: string;
};

type TranslateResult = {
  ok: boolean;
  translation?: string;
  context?: ContextItem[];
  overlay_shown?: boolean;
  overlay_method?: string;
  error?: string;
};

function TranslationPanel({ serverAPI }: { serverAPI: ServerAPI }): ReactElement {
  const [provider, setProvider] = useState<"gemini" | "claude">("gemini");
  const [apiKey, setApiKey] = useState("");
  const [hasApiKey, setHasApiKey] = useState(false);
  const [model, setModel] = useState("gemini-2.5-flash");
  const [sourceLanguage, setSourceLanguage] = useState("Japanese");
  const [targetLanguage, setTargetLanguage] = useState("English");
  const [maxContextItems, setMaxContextItems] = useState("6");
  const [translation, setTranslation] = useState("No translation yet.");
  const [context, setContext] = useState<ContextItem[]>([]);
  const [error, setError] = useState("");
  const [working, setWorking] = useState(false);
  const [overlayVisible, setOverlayVisible] = useState(true);
  const [overlayEnabled, setOverlayEnabled] = useState(true);
  const [overlayMode, setOverlayMode] = useState<"notification" | "persistent">("notification");
  const [overlayMethod, setOverlayMethod] = useState<"auto" | "notify-send" | "gamescope-notify" | "none">("auto");
  const [persistentMethod, setPersistentMethod] = useState<"auto" | "yad" | "zenity">("auto");
  const [persistentPreset, setPersistentPreset] = useState<"top-bar" | "bottom-subtitles" | "center-box" | "compact-corner">("bottom-subtitles");
  const [overlayStatus, setOverlayStatus] = useState("Overlay idle");

  useEffect(() => {
    (async () => {
      const cfg = await serverAPI.callPluginMethod<unknown, ConfigResult>("get_config", {});
      if (cfg.success && cfg.result) {
        setProvider(cfg.result.provider ?? "gemini");
        setHasApiKey(cfg.result.has_api_key ?? false);
        setModel(cfg.result.model ?? "gemini-2.5-flash");
        setSourceLanguage(cfg.result.source_language ?? "Japanese");
        setTargetLanguage(cfg.result.target_language ?? "English");
        setMaxContextItems(String(cfg.result.max_context_items ?? 6));
        setOverlayEnabled(cfg.result.overlay_enabled ?? true);
        setOverlayMode(cfg.result.overlay_mode ?? "notification");
        setOverlayMethod(cfg.result.overlay_method ?? "auto");
        setPersistentMethod(cfg.result.persistent_method ?? "auto");
        setPersistentPreset(cfg.result.persistent_preset ?? "bottom-subtitles");
      }

      const ctx = await serverAPI.callPluginMethod<unknown, { items: ContextItem[] }>("get_context", {});
      if (ctx.success && ctx.result?.items) {
        setContext(ctx.result.items);
      }
    })();
  }, [serverAPI]);

  async function saveConfig(): Promise<void> {
    setError("");

    const payload: Record<string, unknown> = {
      provider,
      model,
      source_language: sourceLanguage,
      target_language: targetLanguage,
      max_context_items: Number(maxContextItems),
      overlay_enabled: overlayEnabled,
      overlay_mode: overlayMode,
      overlay_method: overlayMethod,
      persistent_method: persistentMethod,
      persistent_preset: persistentPreset,
    };
    if (apiKey) {
      payload.api_key = apiKey;
    }

    const result = await serverAPI.callPluginMethod("set_config", payload);
    if (result.success && apiKey) {
      setHasApiKey(true);
      setApiKey("");
    }
  }

  async function closePersistentOverlay(): Promise<void> {
    await serverAPI.callPluginMethod("close_overlay", {});
    setOverlayStatus("Persistent overlay closed");
  }

  function toastOverlayFallback(text: string): void {
    const maybeToaster = (serverAPI as unknown as {
      toaster?: { toast?: (opts: { title: string; body: string; duration?: number }) => void };
    }).toaster;

    if (typeof maybeToaster?.toast === "function") {
      maybeToaster.toast({
        title: "Deck Localize",
        body: text.length > 300 ? `${text.slice(0, 300)}...` : text,
        duration: 8000,
      });
      setOverlayStatus("Overlay shown with Decky toaster fallback");
      return;
    }

    setOverlayStatus("No system overlay backend found");
  }

  async function translateNow(): Promise<void> {
    setWorking(true);
    setError("");

    try {
      await saveConfig();
      const res = await serverAPI.callPluginMethod<unknown, TranslateResult>("capture_and_translate", {});
      if (!res.success || !res.result?.ok) {
        setError(res.result?.error ?? "Translation failed.");
      } else {
        const translated = res.result.translation ?? "";
        setTranslation(translated);
        setContext(res.result.context ?? []);

        if (overlayEnabled) {
          if (res.result.overlay_shown) {
            setOverlayStatus(`Overlay shown via ${res.result.overlay_method ?? "unknown"}`);
          } else {
            toastOverlayFallback(translated);
          }
        } else {
          setOverlayStatus("Overlay disabled in settings");
        }
      }
    } catch (err) {
      setError(String(err));
    } finally {
      setWorking(false);
    }
  }

  async function clearContext(): Promise<void> {
    await serverAPI.callPluginMethod("clear_context", {});
    setContext([]);
  }

  return (
    <PanelSection title="Deck Localize">
      <PanelSectionRow>
        <div style={{ width: "100%" }}>
          <div style={{ display: "flex", gap: "8px", marginBottom: "8px" }}>
            <ButtonItem layout="below" onClick={() => setProvider("gemini")}>Use Gemini</ButtonItem>
            <ButtonItem layout="below" onClick={() => setProvider("claude")}>Use Claude</ButtonItem>
          </div>

          <div className={staticClasses.FieldLabel}>Provider: {provider}</div>

          <div style={{ display: "flex", gap: "8px", marginBottom: "8px", marginTop: "8px" }}>
            <ButtonItem layout="below" onClick={() => setOverlayEnabled((value: boolean) => !value)}>
              {overlayEnabled ? "On-screen Overlay: On" : "On-screen Overlay: Off"}
            </ButtonItem>
            <ButtonItem layout="below" onClick={() => setOverlayMode("notification")}>Notification Mode</ButtonItem>
            <ButtonItem layout="below" onClick={() => setOverlayMode("persistent")}>Persistent Mode</ButtonItem>
          </div>

          {overlayMode === "notification" ? (
            <>
              <div style={{ display: "flex", gap: "8px", marginBottom: "8px", marginTop: "8px" }}>
                <ButtonItem layout="below" onClick={() => setOverlayMethod("auto")}>Overlay Auto</ButtonItem>
                <ButtonItem layout="below" onClick={() => setOverlayMethod("gamescope-notify")}>Use Gamescope</ButtonItem>
                <ButtonItem layout="below" onClick={() => setOverlayMethod("notify-send")}>Use Notify</ButtonItem>
              </div>
              <div className={staticClasses.FieldLabel}>Overlay mode: notification ({overlayMethod})</div>
            </>
          ) : (
            <>
              <div style={{ display: "flex", gap: "8px", marginBottom: "8px", marginTop: "8px" }}>
                <ButtonItem layout="below" onClick={() => setPersistentMethod("auto")}>Persistent Auto</ButtonItem>
                <ButtonItem layout="below" onClick={() => setPersistentMethod("yad")}>Use Yad</ButtonItem>
                <ButtonItem layout="below" onClick={() => setPersistentMethod("zenity")}>Use Zenity</ButtonItem>
                <ButtonItem layout="below" onClick={closePersistentOverlay}>Close Overlay</ButtonItem>
              </div>
              <div style={{ display: "flex", gap: "8px", marginBottom: "8px", marginTop: "8px" }}>
                <ButtonItem layout="below" onClick={() => setPersistentPreset("top-bar")}>Preset Top Bar</ButtonItem>
                <ButtonItem layout="below" onClick={() => setPersistentPreset("bottom-subtitles")}>Preset Bottom Subs</ButtonItem>
                <ButtonItem layout="below" onClick={() => setPersistentPreset("center-box")}>Preset Center Box</ButtonItem>
                <ButtonItem layout="below" onClick={() => setPersistentPreset("compact-corner")}>Preset Compact Corner</ButtonItem>
              </div>
              <div className={staticClasses.FieldLabel}>Overlay mode: persistent ({persistentMethod}, {persistentPreset})</div>
            </>
          )}

          <TextField
            label={hasApiKey ? "API Key (saved — enter new key to replace)" : "API Key"}
            value={apiKey}
            onChange={setApiKey}
          />

          <TextField
            label="Model"
            value={model}
            onChange={setModel}
          />

          <TextField
            label="Source language"
            value={sourceLanguage}
            onChange={setSourceLanguage}
          />

          <TextField
            label="Target language"
            value={targetLanguage}
            onChange={setTargetLanguage}
          />

          <TextField
            label="Context lines"
            value={maxContextItems}
            onChange={setMaxContextItems}
          />

          <div style={{ display: "flex", gap: "8px", marginTop: "8px" }}>
            <ButtonItem layout="below" onClick={saveConfig}>Save Settings</ButtonItem>
            <ButtonItem layout="below" onClick={translateNow} disabled={working}>
              {working ? "Capturing..." : "Capture + Translate"}
            </ButtonItem>
            <ButtonItem layout="below" onClick={clearContext}>Clear Context</ButtonItem>
          </div>

          <div style={{ marginTop: "12px" }}>
            <ButtonItem layout="below" onClick={() => setOverlayVisible((v) => !v)}>
              {overlayVisible ? "Hide Panel Translation" : "Show Panel Translation"}
            </ButtonItem>
          </div>

          <div style={{ marginTop: "8px", opacity: 0.85 }}>Overlay status: {overlayStatus}</div>

          {error ? (
            <div style={{ marginTop: "12px", color: "#ff8a80", whiteSpace: "pre-wrap" }}>
              Error: {error}
            </div>
          ) : null}

          {overlayVisible ? (
            <div
              style={{
                marginTop: "12px",
                background: "linear-gradient(165deg, rgba(9,10,21,0.88), rgba(27,42,65,0.85))",
                border: "1px solid rgba(150, 220, 255, 0.35)",
                borderRadius: "12px",
                padding: "12px",
                boxShadow: "0 0 24px rgba(34, 198, 255, 0.25)",
              }}
            >
              <div style={{ fontWeight: 700, marginBottom: "8px" }}>Live Translation</div>
              <div style={{ whiteSpace: "pre-wrap", lineHeight: 1.45 }}>{translation}</div>
            </div>
          ) : null}

          <div style={{ marginTop: "12px" }}>
            <div style={{ fontWeight: 700, marginBottom: "6px" }}>Context Memory</div>
            <div style={{ maxHeight: "180px", overflowY: "auto", whiteSpace: "pre-wrap", opacity: 0.9 }}>
              {context.length === 0
                ? "No context captured yet."
                : context.map((item, i) => `${i + 1}. ${item.translation}`).join("\n\n")}
            </div>
          </div>
        </div>
      </PanelSectionRow>
    </PanelSection>
  );
}

export default definePlugin((serverApi: ServerAPI) => {
  return {
    title: <div className={staticClasses.Title}>Deck Localize</div>,
    content: <TranslationPanel serverAPI={serverApi} />,
    onDismount() {
      // No background frontend workers to clean up.
    },
  };
});
