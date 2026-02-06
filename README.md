# 🐿️ Devd-Tools (Developer Everyday Companion)

**Devd-Tools** (formerly JR-Dev) is a powerful, lightweight macro engine designed to be your daily driver for development productivity. It automates repetitive tasks, manages your Docker environment seamlessly, and integrates AI assistance directly into your workflow.

> **"Dev-Ed"** stands for **Dev**eloper **E**very **D**ay - Tools you rely on daily.

---

## ✨ Key Features

### 🚀 1. Multi-Project Management
Switch between projects instantly without changing configuration files.
- **Frontend Runner:** Manage multiple `npm run dev` servers effortlessly.
- **Git Workflow:** Commit & Push to different repositories with quick shortcuts.
- **Quick Launch:** Triple-click **F10** to select and launch projects instantly.

### 🐳 2. Robust Docker Manager
Manage Docker containers directly from your keyboard, with full WSL support.
- **Quick Controls:** Up, Down, Restart, and View Logs.
- **Smart Logging:** View real-time logs for specific services or the entire project in a dedicated window.
- **WSL Integration:** Perfect compatibility with Docker Desktop via WSL 2.

### 🔔 3. Modern UI & Notifications
A visual experience that stays out of your way until you need it.
- **Startup Verification:** "Engine Started & Ready" notification on launch.
- **Borderless Toasts:** clean, modern notifications that don't steal focus.
- **System Tray:** Minimal footprint with quick access to settings.

### 📊 4. Statistics Dashboard
Track your productivity habits.
- **Usage Stats:** Monitor total commits, features used, and coding session time.
- **Streak Tracker:** Keep your coding streak alive!
- **Dashboard:** View simple graphs in **Settings > Stats**.

### ⌨️ 5. Customizable Hotkeys
Choose which Function keys (F1-F12) to monitor.
- **Configurable:** Enable only the keys you need in **Settings**.
- **Mode Switching:** Use **F11** to cycle through modes (DEV, GIT, DOCKER, AI).

### 🤖 6. AI Assistant
Integrated prompts to leverage LLMs like ChatGPT for:
- **Code Review:** Security & Performance checks.
- **Refactoring:** Clean code suggestions.
- **Bug Fixing:** Smart debugging help.

---

## 🕹️ Modes & Controls

Cycle through modes using **F11**. Show current bindings with **F12**.

### 💻 1. DEV Mode (Frontend Development)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F8** | Short | **Snippet Tool** (Paste saved snippets) |
| **F9** | Short | **Dev Menu** (Start/Stop Server, Options) |
| **F10** | Short | **Run Active Project** |
| **F10** | Long | **Select Project** |
| **F10** | 3x Click | **Reset Path** / Manage |

### 🐙 2. GIT Mode (Version Control)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F8** | Short | **Snippet Tool** |
| **F9** | Short | **Git Menu** (Status, Pull, Push, Log) |
| **F10** | Short | **Quick Commit** (Auto-add & commit) |
| **F10** | Long | **Select Repository** |
| **F10** | 3x Click | **Manage Repositories** |

### 🐳 3. DOCKER Mode (Container Ops)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F8** | Short | **Snippet Tool** |
| **F9** | Short | **Docker Menu** (Up, Down, Restart, Services) |
| **F10** | Short | **Select & Launch** (Open Terminal/WSL) |

### 🤖 4. AI Mode (Assistant)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F8** | Short | **Smart Terminal** (Natural Language Cmds) |
| **F8** | Long | **Execute Prompt** |
| **F9** | Short | **AI Menu** (Code Review, Explain, Refactor) |
| **F10** | Short | **Terminal Quick** (Select & Launch) |


---

## ⚙️ Installation & Build

### 1. Requirements
- Python 3.10+
- `pip install -r requirements.txt`

### 2. Run from Source
```bash
python main.py
```

### 3. Build Executable (.exe)
Create a standalone executable with custom icon:
```bash
pyinstaller --clean jr-dev.spec
```
*(Output will be in `dist/devd-tool.exe`)*

---

## 🛠️ Configuration

Right-click the **Tray Icon** (Taskbar) -> **Settings**
- **General:** Customize Monitored Keys (F1-F12), Timing.
- **Active Keys:** Select which Function keys to listen to.
- **Stats:** View your usage statistics.
- **Backup:** Export/Import your settings and project lists.

---

**Developed by Dev everyday team | v2.1.0 (Devd-Tools)**
