# Deck Localize — Quick Reference

## TL;DR Install

**Prerequisites:**
- Decky Loader on Steam Deck
- API key from Gemini or Claude
- `grim` on Steam Deck (`sudo pacman -S grim`)
- `yad` on Steam Deck for persistent HUD (`sudo pacman -S yad`)

**Build & Deploy:**

```bash
# On your dev machine:
cd /Users/domhnall/dev/deck-localize
npm install
npm run build

# Copy to Steam Deck:
rsync -avz . deck@steamdeck:~/.var/app/com.github.Decky/data/decky/plugins/deck-localize/

# On Steam Deck:
# Restart Decky (QAM → Settings → Reload Plugins)
```

**Use:**

1. Open Deck Localize in Decky
2. Pick provider (Gemini or Claude)
3. Paste API key → Save Settings
4. In-game: Capture + Translate
5. See translation on screen (notification or persistent HUD)

## Presets (Persistent Mode)

- **Top Bar**: Translation at screen top
- **Bottom Subs**: Subtitle-style (recommended)
- **Center Box**: Centered popup
- **Compact Corner**: Small bottom-right

## API Keys

- **Gemini**: https://ai.google.dev/ (free tier available)
- **Claude**: https://console.anthropic.com/ (paid)

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Screenshot fails | `sudo pacman -S grim` |
| Overlay not showing | `sudo pacman -S yad` or switch to Notification mode |
| Plugin not found | Check rsync copied to correct path; restart Decky |
| API error | Check key is valid; check API quota on provider dashboard |

## File Structure

```
deck-localize/
├── main.py                 # Backend (screenshot, AI, overlay)
├── src/index.tsx          # Frontend UI
├── plugin.json            # Metadata
├── package.json           # Dependencies
└── dist/index.js          # Built frontend (generated)
```

## Commands

```bash
npm install       # Install dependencies
npm run build     # Build frontend to dist/index.js
npm run watch     # Watch mode (rebuild on file change)
npm run typecheck # Check TypeScript
```
