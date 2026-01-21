# 🎮 Developer Macro Engine (v2.0)

A powerful Python-based macro engine designed to boost developer productivity. Automate repetitive tasks, manage multiple projects, and code faster with AI assistance.

## ✨ Key Features

### 🚀 1. Multi-Project Management
Switch between projects instantly without changing configuration files.
- **Frontend Runner:** Manage multiple `npm run dev` servers.
- **Git Workflow:** Commit & Push to different repositories easily.

### 🖥️ 2. Terminal Quick Actions (NEW!)
Open a terminal at your project's root instantly.
- **Windows Terminal Support:** Opens in a new tab if available.
- **Project Selection:** Choose which project to open using **SCRIPT Mode**.

### 📊 3. Statistics Dashboard (NEW!)
Track your productivity habits.
- **Usage Stats:** Total commits, features used, and session time.
- **Streak Tracker:** Keep your coding streak alive!
- **Dashboard:** View simple graphs in Settings > **📊 Stats**.

### ⌨️ 4. Customizable Hotkeys (NEW!)
Choose which Function keys (F1-F12) to monitor.
- **Configurable:** Enable only the keys you need in **Settings**.
- **Mode Switching:** Use F11 to cycle through modes.

### 🤖 5. AI Assistant
Integrated prompts for ChatGPT to help with:
- **Code Review:** Security & Performance checks.
- **Refactoring:** Clean code suggestions.
- **Bug Fixing:** Smart debugging help.

---

## 🕹️ Modes & Controls

Cycle through modes using **F11**. Show current bindings with **F12**.
*(Default configuration uses F9-F10 for actions)*

### 💻 1. DEV Mode (Frontend Development)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F9** | Short | **Start Dev Server** (npm run dev) |
| **F9** | Long | **Stop Server** |
| **F10** | Short | **Run Active Project** |
| **F10** | Long | **Select Project** (Switch active project) |
| **F10** | 3x Click | **Manage Projects** (Add/Remove) |

### 🐙 2. GIT Mode (Version Control)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F9** | Short | **Git Status** |
| **F9** | Long | **Git Pull** |
| **F10** | Short | **Quick Commit** (Add . + Commit + Push) |
| **F10** | Long | **Select Repository** |
| **F10** | 3x Click | **Manage Repositories** |

### 📜 3. SCRIPT Mode (Terminal & Ops)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F9** | Short | **Open Terminal Here** (Active Project) |
| **F9** | Long | **Select Project** to Open |
| **F10** | Short | **Open Terminal Here** (Active Project) |
| **F10** | Long | **Select Project** to Open |

### 🤖 4. AI Mode (Assistant)
| Key | Press | Action |
| :--- | :--- | :--- |
| **F9** | Short | **Code Review & Secure** |
| **F9** | Long | **Explain Code** |
| **F10** | Short | **Bug Fix** |
| **F10** | Long | **Refactor Code** |
*(Copies code from clipboard -> Formats prompt -> Opens ChatGPT)*

---

## ⚙️ Setup & Installation

1.  **Clone Repository:**
    ```bash
    git clone https://github.com/yourusername/jr-dev.git
    cd jr-dev
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *(Requires: `pynput`, `pyperclip`, `Pillow`, `ttkbootstrap`)*

3.  **Run Application:**
    ```bash
    python main.py
    ```

4.  **Auto-Start:**
    Enable "Start on Boot" in Settings to run automatically with Windows.

---

## 🛠️ Configuration

Right-click the **Tray Icon** (Taskbar) -> **Settings**
- **General:** Customize Monitored Keys (F1-F12), Timing.
- **Active Keys:** Select which Function keys to listen to.
- **Stats:** View your usage statistics.
- **Backup:** Export/Import your settings and project lists.

## 📦 Project Structure

- `core/`: Main engine logic (Events, Modes, Features)
- `features/`: Individual feature implementations (Git, AI, Runner)
- `inputs/`: Keyboard/Input listeners
- `ui/`: Settings dialogs and System Tray
- `utils/`: Helpers (Logger, Statistics, Windows API)
- `config/`: JSON configuration files

---
**Developed by Framex | v2.0.0**
