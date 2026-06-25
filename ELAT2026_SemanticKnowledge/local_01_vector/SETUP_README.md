# Setup Scripts

This directory contains automated setup scripts for the Chat Application. These scripts will check for prerequisites, install missing components, and start all necessary services.

## Universal Setup (Recommended)

Run this script to automatically detect your OS and run the appropriate setup:

```bash
./setup.sh
```

## Platform-Specific Scripts

### 🍎 macOS
```bash
./setup-macos.sh
```

### 🐧 Linux
```bash
./setup-linux.sh
```

### 🪟 Windows
```batch
setup-windows.bat
```

## What the Scripts Do

All scripts perform the following actions:

1. **Check Prerequisites**
   - ✅ Node.js (v18+)
   - ✅ .NET 9 SDK
   - ✅ Ollama

2. **Install Missing Components**
   - 📦 Uses appropriate package managers (Homebrew, apt, dnf, winget, chocolatey)
   - 🔄 Automatically installs missing prerequisites

3. **Setup Ollama**
   - 🚀 Starts Ollama server
   - 📥 Downloads llama3.2 model

4. **Install Dependencies**
   - 📋 Frontend: `npm install`
   - 🔧 Backend: `dotnet restore`

5. **Start Services**
   - 🌐 Backend server on https://localhost:5001
   - ⚛️ Frontend dev server on http://localhost:5173

## Manual Installation

If the automated scripts don't work for your system, follow the manual setup instructions in the main README.md file.

## Troubleshooting

### Permission Issues (Linux/macOS)
```bash
chmod +x setup.sh setup-linux.sh setup-macos.sh
```

### Windows Execution Policy
If you get execution policy errors on Windows, run PowerShell as Administrator and execute:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Port Conflicts
If ports 5001 or 5173 are already in use:
- Stop existing services using those ports
- Or modify the ports in the application configuration

### Package Manager Issues
- **macOS**: Install Homebrew first: `/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`
- **Linux**: Scripts support Ubuntu/Debian, Fedora, CentOS/RHEL, and Arch Linux
- **Windows**: Scripts will install Chocolatey if WinGet is not available

## Configuration

After running the setup scripts, you'll need to configure:

1. **Azure AD settings** in `elat.local.llm.Server/appsettings.json`
2. **Frontend auth** in `elat.local.llm.client/src/authConfig.ts`

See the main README.md for detailed configuration instructions.
