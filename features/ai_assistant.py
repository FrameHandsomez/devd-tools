"""
AI Assistant Feature - AI Prompts for developers

Actions:
- code_review: Review code for quality
- explain_code: Explain code in simple terms
- bug_fix: Help debug and fix bugs
- optimize: Optimize code performance
"""

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

    "bug_fix": """คุณเป็น Expert Debugger ที่เชี่ยวชาญในการช่วยมือใหม่แก้ปัญหา (Junior-friendly)
คุณได้รับ Error Logs จากเครื่องของผู้ใช้ และโครงสร้างโปรเจค

**ข้อมูลที่สำคัญที่สุด (Error Logs):**
{logs}

**โค้ดที่ผู้ใช้อาจจะแนบมา (ถ้ามี):**
```
{code}
```

**สิ่งที่คุณต้องทำ:**
1. **วิเคราะห์ Logs:** บอกผู้ใช้ว่า Error นี้คืออะไร (แปลเป็นไทยง่ายๆ) และเกิดขึ้นที่ไฟล์ไหน บรรทัดไหน
2. **ตามหาต้นตอ:** ดูจาก Error Traceback และโครงสร้างโปรเจค (ด้านล่าง) เพื่อเดาว่าไฟล์ไหนในโปรเจคที่เป็นตัวปัญหา
3. **สอนวิธีแก้:** 
   - ถ้ามีโค้ดแนบมา: ให้แก้โค้ดนั้น
   - ถ้าไม่มีโค้ดแนบมา: บอกผู้ใช้ว่าต้องไปเปิดไฟล์ไหน และต้องแก้โค้ดประมาณไหน
4. **แนะนำมือใหม่:** บอกขั้นตอนการเช็คเบื้องต้น (เช่น ต้องลง library เพิ่มไหม? หรือพิมพ์ชื่อไฟล์ผิด?)

*หมายเหตุ: ผู้ใช้เป็นมือใหม่อาจจะไม่รู้ว่าต้องก๊อปโค้ดส่วนไหนมาให้คุณ ดังนั้นโปรดพยายามใช้ Logs ให้เกิดประโยชน์สูงสุด*""",

    "analyze_logs": """คุณเป็น System Administrator และ DevOps Expert ที่เชี่ยวชาญการวิเคราะห์ logs

**Logs ที่ต้องการให้ตรวจสอบ:**
```
{logs}
```

**ให้ช่วย:**
1. **สรุปเหตุการณ์:** เกิดอะไรขึ้นในระบบ? (Summary in 2-3 lines)
2. **ค้นหาจุดวิกฤต:** มี Error หรือ Warning ตรงไหนที่ต้องรีบแก้?
3. **วิเคราะห์สาเหตุ:** จาก logs นี้ สาเหตุที่น่าจะเป็นไปได้มากที่สุดคืออะไร?
4. **คำแนะนำการแก้ไข:** ต้องไปเช็คที่ไฟล์ไหน หรือต้องรันคำสั่งอะไรเพื่อแก้ปัญหา?
5. **Security Check:** มีสัญญาณของการถูกโจมตี หรือช่องโหว่ใน logs นี้ไหม?""",

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
            return self._run_prompt("bug_fix", "🪲 Bug Fix (Logs + Code)", include_logs=True, require_code=False)
        elif action == "analyze_logs":
            return self._run_prompt("analyze_logs", "📊 Analyze Logs", include_logs=True, require_code=False)
        elif action == "refactor":
            return self._run_prompt("refactor", "🔄 Refactor")
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _check_connection(self) -> bool:
        """Check internet connection"""
        import socket
        try:
            # Try to connect to Google DNS (fastest check)
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            return True
        except OSError:
            return False

    def _run_prompt(self, prompt_key: str, title: str, include_context: bool = True, include_logs: bool = False, require_code: bool = True) -> FeatureResult:
        """Run a prompt with user's code and optional project context"""
        
        from ui.dialogs import show_notification, ask_yes_no
        import pyperclip
        
        # Check network first
        if not self._check_connection():
            if not ask_yes_no("🌐 No Internet", "ไม่พบสัญญาณอินเทอร์เน็ต\nต้องการดำเนินการต่อหรือไม่? (Prompt จะถูก copy ไว้)"):
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="Offline - blocked by user check"
                )
        
        try:
            # Get code from clipboard
            code = pyperclip.paste()
            
            # Check if code is required but missing
            if require_code and (not code or not code.strip()):
                show_notification(
                    title="❌ ไม่พบโค้ด",
                    message="กรุณา copy โค้ดก่อนกดปุ่ม",
                    duration=3000
                )
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="No code in clipboard"
                )
            
            # If not required and missing, set a placeholder
            if not code or not code.strip():
                code = "(ผู้ใช้ไม่ได้ Copy โค้ดมา - โปรดวิเคราะห์จาก Logs และโครงสร้างโปรเจค)"
            
            # Get project context
            context_str = ""
            logs_str = "ไม่พบข้อมูล Logs"
            
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
                    
                    if include_context:
                        context_str = collector.format_context_for_prompt(include_structure=True, include_logs=include_logs)
                        context_str = f"\n\n---\n{context_str}\n---\n"
                    
                    if include_logs:
                        logs_str = collector.get_recent_logs(30)
                    
                    logger.info(f"Collected context from: {project_path}")
            except Exception as e:
                logger.warning(f"Could not collect context: {e}")
            
            # Format the prompt
            prompt_template = PROMPTS.get(prompt_key, "")
            
            # Specialized formatting based on template requirements
            if prompt_key == "bug_fix":
                full_prompt = prompt_template.format(code=code, logs=logs_str)
            elif prompt_key == "analyze_logs":
                full_prompt = prompt_template.format(logs=logs_str)
            else:
                full_prompt = prompt_template.format(code=code)
            
            # Add context if available
            if context_str:
                full_prompt = f"{context_str}\n\n{full_prompt}"
            
            # Copy formatted prompt to clipboard
            pyperclip.copy(full_prompt)
            
            # Open ChatGPT
            webbrowser.open("https://chat.openai.com/")
            
            # Show notification
            show_notification(
                title=f"✅ {title}",
                message="Prompt copied! วาง (Ctrl+V) ใน ChatGPT ได้เลย",
                duration=4000
            )
            
            logger.info(f"AI prompt '{prompt_key}' prepared and copied to clipboard")
            
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"{title} prompt ready",
                data={"prompt_key": prompt_key}
            )
            
        except ImportError:
            show_notification(
                title="❌ ขาด Library",
                message="กรุณาติดตั้ง: pip install pyperclip",
                duration=5000
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
