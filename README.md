# Deck Localize (Decky Plugin)

Deck Localize is a Steam Deck Decky plugin that:

1. Captures a screenshot from the running game.
2. Sends the screenshot to Gemini or Claude.
3. Translates visible text (for example Japanese to English).
4. Keeps recent translations as rolling context.
5. Displays the latest translation in a live overlay panel inside Decky.

## Features

- Provider switch: Gemini or Claude.
- Configurable model name per provider.
- Configurable source and target language.
- Rolling translation context memory for better continuity.
- On-screen notification overlay attempts after each translation.
- Persistent subtitle-style overlay mode (Yad/Zenity based) with close control.
- Persistent overlay layout presets: top bar, bottom subtitles, center box, compact corner.
- One-button "Capture + Translate" flow.

## Project Structure

- `main.py`: Decky backend (screenshot capture, API calls, context memory).
- `src/index.tsx`: Decky frontend UI.
- `plugin.json`: Decky plugin metadata.
- `scripts/build.mjs`: Frontend bundler script (esbuild).

## Build Frontend

```bash
npm install
npm run build
```

This produces `dist/index.js` for Decky.

## Steam Deck Requirements

- Decky Loader installed.
- Internet access for AI API calls.
- `grim` installed for screenshot capture in Game Mode/Desktop Mode. The plugin also attempts `gamescope-screenshot --stdout` as fallback.
- For persistent overlay mode, install one of: `yad` (recommended) or `zenity`.

## Configure In Plugin UI

1. Choose provider (`gemini` or `claude`).
2. Paste API key.
3. Set model (for example `gemini-2.5-flash` or `claude-3-7-sonnet-latest`).
4. Set source and target language.
5. Toggle on-screen overlay and choose mode:
	- Notification mode: `Auto`, `Gamescope`, or `Notify`.
	- Persistent mode: `Auto`, `Yad`, or `Zenity`.
	- Choose preset: `Top Bar`, `Bottom Subs`, `Center Box`, or `Compact Corner`.
6. Press `Save Settings`.
7. Press `Capture + Translate`.

## Notes

- API keys are stored in plugin settings on-device.
- The plugin now attempts an on-screen notification overlay using `gamescope-notify` first, then `notify-send` when available.
- In persistent mode, the plugin keeps an always-on-top translation window and refreshes it on each new translation.
- Presets tune persistent overlay geometry for Steam Deck's 1280x800 screen.
- If backend overlay tools are missing, frontend falls back to a Decky toast notification when possible.
- OCR quality depends on screenshot clarity and game font size.

## Safety / Costs

- Every translation request sends one screenshot to your selected model provider.
- You are responsible for API usage costs and provider policy compliance.
