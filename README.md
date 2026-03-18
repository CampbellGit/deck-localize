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

## Installation on Steam Deck

### Prerequisites

1. **Decky Loader** installed on your Steam Deck
   - Download from [Decky Loader releases](https://github.com/SteamDeckHomebrew/decky-loader/releases)
   - Follow their installation guide

2. **Screenshot tool** (one of):
   - `grim` (recommended for Game Mode)
   - `gamescope-screenshot` (fallback)

3. **Persistent overlay tools** (for HUD mode):
   - `yad` (recommended) or `zenity`
   - Install via: `sudo pacman -S yad` or `sudo pacman -S zenity`

4. **API Key** from Gemini or Claude:
   - Google Gemini: https://ai.google.dev/
   - Anthropic Claude: https://console.anthropic.com/

### Build & Deploy

**On your development machine** (with Node.js/npm):

```bash
cd /Users/domhnall/dev/deck-localize
npm install
npm run build
```

This creates `dist/index.js` (the compiled frontend).

**Transfer to Steam Deck**:

1. Copy the entire plugin folder to Steam Deck:
   ```bash
   rsync -avz /Users/domhnall/dev/deck-localize/ deck@192.168.X.X:~/.var/app/com.github.Decky/data/decky/plugins/deck-localize/
   ```
   (Replace `192.168.X.X` with your Steam Deck IP, or use `deck@steamdeck` if SSH is configured)

2. On Steam Deck, restart Decky:
   - Power off Decky via the Decky menu
   - Wait a few seconds
   - Re-open Decky

3. Deck Localize should now appear in your Decky plugins list.

### Quick Start

1. Open Decky menu (hold power button on right joystick or press QAM)
2. Navigate to "Plugins" → "Deck Localize"
3. Choose provider: **Gemini** or **Claude**
4. Paste your API key
5. Configure:
   - Model (default: `gemini-2.5-flash` or `claude-3-7-sonnet-latest`)
   - Source language (e.g., Japanese)
   - Target language (e.g., English)
6. Choose overlay mode:
   - **Notification**: Transient toast overlay (via gamescope-notify or notify-send)
   - **Persistent**: Always-on-top HUD window (via yad or zenity)
7. If persistent: select a preset (Top Bar, Bottom Subtitles, Center Box, Compact Corner)
8. Press `Save Settings`
9. Press `Capture + Translate` with your game in focus

Translation appears:
- In the plugin panel (Live Translation box)
- On-screen (via your chosen overlay mode)
- In Context Memory (rolling history for better continuity)

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
