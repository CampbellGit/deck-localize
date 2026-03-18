# Deck Localize Installation Guide

This guide walks you through getting Deck Localize set up on your Steam Deck for on-the-fly game translation.

## Step 1: Prerequisites

### Install Decky Loader (one-time setup)

If you haven't already, install the Decky Loader plugin framework on your Steam Deck:

1. Visit https://github.com/SteamDeckHomebrew/decky-loader/releases
2. Download the latest `.tar.gz` release
3. Extract and follow their installation instructions (usually a one-click script)
4. Restart your Steam Deck

### Get API Keys

Choose one or both:

- **Google Gemini** (free tier available):
  1. Go to https://ai.google.dev/
  2. Click "Get API Key"
  3. Create a new API key
  4. Copy it (you'll paste it into the plugin)

- **Anthropic Claude**:
  1. Go to https://console.anthropic.com/
  2. Sign up / log in
  3. Create an API key under Account Settings
  4. Copy it

### Install Screenshot Tool (on Steam Deck)

Open a terminal on your Steam Deck and run:

```bash
sudo pacman -S grim
```

Fallback tools (optional, but nice to have):

```bash
sudo pacman -S gamescope
sudo pacman -S yad            # Recommended for persistent HUD overlay
sudo pacman -S zenity         # Alternative to yad
```

## Step 2: Build the Plugin

**On your development machine** (Mac/Linux with Node.js installed):

1. Navigate to the plugin directory:
   ```bash
   cd /Users/domhnall/dev/deck-localize
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the frontend:
   ```bash
   npm run build
   ```

   You should see: `Built dist/index.js`

## Step 3: Deploy to Steam Deck

### Option A: Using rsync (recommended)

On your development machine, copy the entire plugin folder to Steam Deck:

```bash
rsync -avz /Users/domhnall/dev/deck-localize/ deck@steamdeck:~/.var/app/com.github.Decky/data/decky/plugins/deck-localize/
```

(If your Steam Deck is on a different IP, replace `steamdeck` with the IP address, e.g., `deck@192.168.1.100`)

### Option B: Manual SCP copy

```bash
scp -r /Users/domhnall/dev/deck-localize deck@steamdeck:~/.var/app/com.github.Decky/data/decky/plugins/deck-localize
```

### Option C: USB Transfer

1. On your development machine, zip the plugin folder
2. Copy to a USB drive
3. On Steam Deck Desktop Mode, copy to `~/.var/app/com.github.Decky/data/decky/plugins/deck-localize/`

## Step 4: Restart Decky

On your Steam Deck:

1. Open Decky (QAM button or hold power on right joystick)
2. Find the Decky settings
3. Click "Reload Plugins" or restart Decky
4. Close and re-open Decky

You should now see **Deck Localize** in your plugins list.

## Step 5: Configure & Use

1. Open **Deck Localize** from Decky plugins
2. Choose your AI provider:
   - Click **"Use Gemini"** or **"Use Claude"**
3. Paste your API key in the **API Key** field
4. Set your languages:
   - **Source language**: e.g., "Japanese"
   - **Target language**: e.g., "English"
5. Choose **Save Settings**
6. (Optional) Switch to **Persistent Mode** and pick a preset:
   - **Top Bar**: Translation at top of screen
   - **Bottom Subs**: Subtitle-style at bottom (recommended)
   - **Center Box**: Centered dialog box
   - **Compact Corner**: Small bottom-right corner
7. Launch a game
8. When you see text you want translated, press the **Capture + Translate** button
9. Translation appears both in the plugin panel and on your screen!

## Troubleshooting

### "Screenshot capture failed"

- Ensure `grim` is installed: `sudo pacman -S grim`
- Try the alternative: `sudo pacman -S gamescope`

### "API key is required"

- Make sure you pasted your key and clicked **Save Settings**
- Check that your key is valid and not expired

### Persistent overlay not showing

- Install `yad`:
  ```bash
  sudo pacman -S yad
  ```
- Or use `zenity` as fallback:
  ```bash
  sudo pacman -S zenity
  ```
- If still not showing, try **Notification Mode** instead (gamescope-notify or notify-send)

### Plugin doesn't appear after deploy

- Make sure the folder is in the correct location: `~/.var/app/com.github.Decky/data/decky/plugins/deck-localize/`
- Check that `dist/index.js` exists (run `npm run build` again if missing)
- Restart Decky or reboot Steam Deck

### Translations look garbled or are incomplete

- This is an OCR quality issue; try:
  - Increasing graphics settings for clearer text in-game
  - Slowing down or pausing the game before capturing
  - Adjusting game UI scale if possible

### Rate limiting or API errors

- You may have hit an API quota. Check your provider's dashboard:
  - Gemini: https://ai.google.dev/
  - Claude: https://console.anthropic.com/
- Free tiers have usage limits; paid plans offer more

## Support

For issues or features, check the README.md or consider opening an issue on GitHub.

Enjoy translating your games!
