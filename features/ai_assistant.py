"""
AI Assistant Feature - AI Prompts for developers

Actions:
- code_review: Review code for quality
- explain_code: Explain code in simple terms
- bug_fix: Help debug and fix bugs
- optimize: Optimize code performance
"""

import threading
from pathlib import Path
from typing import Optional
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger
import webbrowser

logger = get_logger(__name__)

# Prompt templates
PROMPTS = {
    "review_secure": """คุณเป็น Senior Developer และ Security Expert ที่มีประสบการณ์ในการ review โค้ด

วิเคราะห์โค้ดต่อไปนี้และให้ feedback ใน 2 มุมมอง:

## Part 1: Code Audit (ตรวจสอบโค้ด)

1. **ความถูกต้อง (Correctness)**
- Logic มีจุดผิดพลาดหรือ edge case ที่พลาดไหม?
- มี bugs ที่ซ่อนอยู่หรือเปล่า?

2. **ความอ่านง่าย (Readability)**
- ตั้งชื่อตัวแปร/function ชัดเจนไหม?
- Code structure เข้าใจง่ายไหม?

3. **Performance**
- มี bottleneck ที่เป็นไปได้ไหม?

## Part 2: Security Hardening (ตรวจสอบความปลอดภัย)

1. **ช่องโหว่ที่พบ:**
- API Key หลุด? Hardcoded secrets?
- SQL Injection / XSS / CSRF?
- ลืมเช็ค Input validation?
- ข้อมูลสำคัญรั่วไหล?

2. **ระดับความเสี่ยง:** 🔴 Critical / 🟡 Medium / 🟢 Low

3. **วิธีแก้ไขเฉพาะจุด:**
- แสดง code ที่ต้องแก้
- อธิบายว่าทำไมต้องแก้

**โค้ดที่ต้องการ Review & Secure:**
```
{code}
```""",

    "explain_code": """คุณเป็น Technical Writer และ Educator ที่เก่งอธิบายเทคนิคให้เข้าใจง่าย

**โค้ดที่ต้องการอธิบาย:**
```
{code}
```

**ระดับความรู้ของผู้อ่าน:** มือใหม่ / มีพื้นฐาน

**ให้ช่วย:**

1. **Overview** (20 คำ):
- โค้ดนี้ทำอะไรโดยรวม?

2. **อธิบายทีละส่วน:**
- แต่ละ function/block ทำอะไร
- ตัวแปรแต่ละตัวคืออะไร
- Logic flow เป็นยังไง

3. **Concepts ที่ใช้:**
- ใช้ pattern/technique อะไรบ้าง
- ทำไมถึงเลือกใช้วิธีนี้

4. **ตัวอย่างการใช้งาน:**
- Input ตัวอย่าง → Output
- Use case จริงๆ ที่เจอได้""",

    "bug_fix": """คุณเป็น Debugging Expert ที่เชี่ยวชาญในการแก้ bug

**สถานการณ์:**
รหัสปัญหาที่เกิดขึ้น: [อธิบายอาการที่เห็น]

**โค้ดที่เกี่ยวข้อง:**
```
{code}
```

**ให้ช่วย:**
1. วิเคราะห์สาเหตุของ bug พร้อมอธิบาย "ทำไม" ถึงเกิด
2. เสนอวิธีแก้ไข 2-3 วิธี (จากง่ายไปยาก)
3. แสดง code ที่แก้ไขแล้วพร้อมอธิบายว่าเปลี่ยนอะไรไปทำไม
4. แนะนำวิธีป้องกันไม่ให้เกิด bug แบบนี้อีกในอนาคต
5. เสนอการเขียน test case เพื่อ catch bug นี้""",

    "refactor": """คุณเป็น Software Architect ที่เชี่ยวชาญการออกแบบโค้ดที่ clean และ maintainable

**โค้ดที่ต้องการ Refactor:**
```
{code}
```

**เป้าหมายของการ Refactor:**
- [ ] ทำให้อ่านง่ายขึ้น
- [ ] ลด complexity
- [ ] แยก concerns ให้ชัดเจน
- [ ] ทำให้ test ง่ายขึ้น
- [ ] เตรียมพร้อมสำหรับ scale ในอนาคต

**ให้ช่วย:**

1. **วิเคราะห์ปัญหาของโค้ดปัจจุบัน (code smells)**
2. **เสนอ refactoring strategy ทีละขั้นตอน**
3. **แสดงโค้ดหลัง refactor พร้อมอธิบายว่าเปลี่ยนอะไรทำไม**
4. **เปรียบเทียบ before/after ให้เห็นความแตกต่าง**
5. **ระบุ trade-offs (ถ้ามี)**

**หลักการ:**
- รักษา functionality เดิมไว้ (behavior ไม่เปลี่ยน)
- ทำทีละก้าวเล็กๆ refactor ได้
- เพิ่ม comments อธิบาย design decisions"""
}


class AIAssistantFeature(BaseFeature):
    """
    Feature: AI Assistant for developers
    
    - F9 short: Code Review
    - F9 long: Explain Code
    - F10 short: Bug Fix
    - F10 long: Optimize
    """
    
    name = "ai_assistant"
    description = "AI-powered code assistance"
    supported_patterns = [PressType.SHORT, PressType.LONG]
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the AI assistant action"""
        
        if action == "review_secure":
            return self._run_prompt("review_secure", "🔍 Review & Secure")
        elif action == "explain_code":
            return self._run_prompt("explain_code", "📖 Explain Code")
        elif action == "bug_fix":
            return self._run_prompt("bug_fix", "🪲 Bug Fix")
        elif action == "refactor":
            return self._run_prompt("refactor", "🔄 Refactor")
        elif action == "menu":
            return self._show_ai_menu_async()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _run_dialog_subprocess(self, command, data):
        """Helper to run dialog subprocess"""
        import subprocess
        import sys
        import json
        from pathlib import Path
        
        # Point to ui/dialogs.py relative to this file
        dialog_script = Path(__file__).parent.parent / "ui" / "dialogs.py"
        
        try:
            cmd = [sys.executable, str(dialog_script), command, json.dumps(data)]
            # Run without window creation flag on Windows if possible, but keep simple for now
            creation_flags = 0
            if sys.platform == "win32":
                creation_flags = subprocess.CREATE_NO_WINDOW
                
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                creationflags=creation_flags,
                encoding='utf-8',
                errors='replace'
            )
            
            if result.returncode != 0:
                logger.error(f"Dialog error ({command}): {result.stderr}")
                return None
                
            if not result.stdout.strip():
                return None
                
            return json.loads(result.stdout)
        except Exception as e:
            logger.error(f"Subprocess failed: {e}")
            return None

    def _show_ai_menu_async(self) -> FeatureResult:
        """Show AI menu"""
        def run():
            options = [
                "🔍 Code Review & Security",
                "📖 Explain Code",
                "🪲 Bug Fix",
                "🔄 Refactor Code"
            ]
            
            result_data = self._run_dialog_subprocess("ask_choice", {
                "title": "AI Assistant",
                "message": "Select AI Action (Copy code first!):",
                "choices": options
            })
            
            if not result_data:
                return
                
            idx = result_data.get("result")
            if idx is None:
                return
            
            if idx == 0: self._run_prompt("review_secure", "🔍 Review & Secure")
            elif idx == 1: self._run_prompt("explain_code", "📖 Explain Code")
            elif idx == 2: self._run_prompt("bug_fix", "🪲 Bug Fix")
            elif idx == 3: self._run_prompt("refactor", "🔄 Refactor")
            
        import threading
        threading.Thread(target=run, daemon=True).start()
        return FeatureResult(status=FeatureStatus.SUCCESS, message="Opening AI Menu...")
    
    def _check_connection(self) -> bool:
        """Check internet connection"""
        import socket
        try:
            # Try to connect to Google DNS (fastest check)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _show_notification_async(self, title: str, message: str, duration: int = 3000):
        """Show notification using subprocess"""
        self._run_dialog_subprocess("show_notification", {
            "title": title,
            "message": message,
            "duration": duration
        })

    def _run_prompt(self, prompt_key: str, title: str, include_context: bool = True) -> FeatureResult:
        """Run a prompt with user's code and optional project context"""
        
        import pyperclip
        
        # Check network first
        if not self._check_connection():
            yes_no = self._run_dialog_subprocess("ask_yes_no", {
                "title": "🌐 No Internet",
                "message": "ไม่พบสัญญาณอินเทอร์เน็ต\nต้องการดำเนินการต่อหรือไม่? (Prompt จะถูก copy ไว้)"
            })
            
            if not yes_no or not yes_no.get("result"):
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="Offline - blocked by user check"
                )
        
        try:
            # Get code from clipboard
            code = pyperclip.paste()
            
            if not code or not code.strip():
                self._show_notification_async(
                    "❌ ไม่พบโค้ด",
                    "กรุณา copy โค้ดก่อนกดปุ่ม",
                    3000
                )
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="No code in clipboard"
                )
            
            # Get project context
            context_str = ""
            if include_context:
                try:
                    from utils.context_collector import get_collector
                    
                    # Try to get active project path
                    project_path = None
                    active = self.config_manager.get_active_project("frontend_project")
                    if active:
                        project_path = Path(active["path"])
                    elif self.config_manager.get_active_project("git_project"):
                        active = self.config_manager.get_active_project("git_project")
                        project_path = Path(active["path"])
                    
                    if project_path and project_path.exists():
                        collector = get_collector(project_path)
                        context_str = collector.format_context_for_prompt(include_structure=True)
                        context_str = f"\n\n---\n{context_str}\n---\n"
                        logger.info(f"Collected context from: {project_path}")
                except Exception as e:
                    logger.warning(f"Could not collect context: {e}")
            
            # Format the prompt
            prompt_template = PROMPTS.get(prompt_key, "")
            full_prompt = prompt_template.format(code=code)
            
            # Add context if available
            if context_str:
                full_prompt = f"{context_str}\n\n{full_prompt}"
            
            # Copy formatted prompt to clipboard
            pyperclip.copy(full_prompt)
            
            # Open ChatGPT
            webbrowser.open("https://chat.openai.com/")
            
            # Show notification
            self._show_notification_async(
                f"✅ {title}",
                "Prompt copied! วาง (Ctrl+V) ใน ChatGPT ได้เลย",
                4000
            )
            
            logger.info(f"AI prompt '{prompt_key}' prepared and copied to clipboard")
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"{title} prompt ready",
                data={"prompt_key": prompt_key}
            )
            
        except ImportError:
            self._show_notification_async(
                "❌ ขาด Library",
                "กรุณาติดตั้ง: pip install pyperclip",
                5000
            )
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message="pyperclip not installed"
            )
        except Exception as e:
            logger.error(f"AI prompt error: {e}")
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=str(e)
            )
