# Developer Macro Engine 🚀

ซอฟต์แวร์ Macro สำหรับ Developer ทำ Workflow Automation บน Windows

## 🎯 Features

| ปุ่ม | กดสั้น | กดค้าง | กด 3 ครั้ง |
|------|--------|--------|------------|
| **F9** | Clone Git Project | Update Project (git pull) | - |
| **F10** | Run Dev Server | - | Reset Path |
| **F11** | Switch Mode | - | - |

## 🛠️ Installation

```powershell
# Clone repo
git clone https://github.com/your-repo/macro-engine.git
cd macro-engine

# Install dependencies (ใช้ uv)
uv venv
uv pip install pynput pystray Pillow pywin32

# หรือใช้ pip
pip install -r requirements.txt
```

## 🚀 Usage

```powershell
# Activate virtual environment
.\.venv\Scripts\activate

# Run
python main.py
```

## 📁 Project Structure

```
macro-engine/
├── main.py              # Entry point
├── runtime/             # Bootstrap layer
├── core/                # Core modules (headless)
│   ├── events/          # Event routing
│   ├── modes/           # Mode manager
│   ├── commands/        # Command executor
│   └── features/        # Feature registry
├── features/            # Feature plugins
├── inputs/              # Input providers
├── ui/                  # Optional UI layer
└── config/
    └── macros.json      # Configuration
```

## ⚙️ Configuration

แก้ไข `config/macros.json` เพื่อ:
- เปลี่ยน key bindings
- เพิ่ม/ลบ modes
- ปรับ timing settings

## 🎮 Modes

- **DEV**: Development workflows
- **GIT**: Git operations
- **AI**: AI assistant (กำลังพัฒนา)
- **SCRIPT**: Custom scripts (กำลังพัฒนา)

## 🔌 Hardware Support

รองรับ USB HID devices:
- Physical Keyboard
- Macro Pad (USB HID)
- Arduino (ATmega32U4)

## 📝 License

MIT
