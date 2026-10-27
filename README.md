# Configurable Browser

A starter desktop browser built with Python + QtWebEngine. It renders real websites using Chromium via QtWebEngine; it is not a custom rendering engine sadly.

## Features
Tabs, address/search bar, back/forward/reload/home
Search engine selector: DuckDuckGo, Google, Bing, Brave, Wikipedia
Five themes, page zoom, JavaScript/images/cookie toggles
Bookmarks bar and bookmark manager
Browsing history and clear-history action
Restore previous tabs, downloads folder shortcut, keyboard shortcuts

## Install
Use Python 3.10+.
### Windows (PowerShell)
```powershell
cd ConfigurableBrowser
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```
### macOS / Linux
```bash
cd ConfigurableBrowser
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```
## Important notes
Cookie setting is present in the configuration UI; QtWebEngine's profile storage configuration is not yet switched to a strict no-cookie profile in this starter build.
Custom CSS is loaded from a URL after pages load; only use CSS sources you trust.
This is an early project, not a hardened privacy browser. It does not include ad blocking, extension support, sync, or its own rendering engine yet.
Settings are in `~/.configurable-browser/settings.json`. Close the browser before editing this file manually.

## Useful shortcuts
- `Ctrl+L`: focus address bar
- `Ctrl+T`: new tab
- `Ctrl+W`: close tab
- `Ctrl+D`: bookmark current page
- `Ctrl+Plus` / `Ctrl+-`: zoom
- `Ctrl+0`: reset zoom
- `F11`: fullscreen
