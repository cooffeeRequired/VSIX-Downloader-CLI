# VSIX Downloader CLI

An interactive terminal tool to search for Visual Studio Code extensions using `vsce` and download selected `.vsix` packages.

## Features

- 🔎 Search extensions via `vsce`
- 🎯 Interactive selection using arrow keys
- ✅ Select multiple extensions with spacebar
- ⬇️ Download selected extensions as `.vsix`
- 🧭 Animated progress bar for each download
- 🐞 Optional debug mode with console logging

## Requirements

- Python 3.7+
- Node.js with [`vsce`](https://www.npmjs.com/package/@vscode/vsce)
- `curl` installed and available in your system's PATH

## Installation

1. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```
2. **Install vsce globally (via npm)**

   ```bash
   npm install -g @vscode/vsce
   ```
## Usage
   ```bash
   python index.py
   ```
> You will be prompted to enter a search term. Navigate results with ↑ and ↓, select with Space, confirm with Enter.
### Debug Mode
> To enable verbose logging, set DEBUG = True in index.py. Logs will be printed using Rich's console.log.

### Feel free to fork or contribute. ❤️
