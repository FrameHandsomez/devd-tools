from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.logger import get_logger
import webbrowser
import pyperclip
import json

logger = get_logger(__name__)

class SmartTerminal(BaseFeature):
    """
    Smart Terminal (F8 in AI Mode)
    Uses Snippet Selector UI as a Prompt Input.
    """
    name = "smart_terminal"
    description = "AI Smart Prompt Terminal"
    supported_patterns = [PressType.SHORT, PressType.LONG]

    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        if action in ["prompt", "execute"]:
            # Launch UI via bootstrap command
            success = self.command_executor.execute("launch_smart_terminal")
            if success:
                return FeatureResult(FeatureStatus.SUCCESS, "Smart Terminal launched")
            else:
                 return FeatureResult(FeatureStatus.ERROR, "Failed to launch Smart Terminal")
        
        return FeatureResult(FeatureStatus.ERROR, f"Unknown action: {action}")

    @staticmethod
    def process_smart_query(query: str):
        """Called by bootstrap when user submits text in Smart Terminal UI"""
        logger.info(f"Processing Smart Terminal query: {query}")
        
        if not query or not query.strip():
            return
            
        # 1. Format Prompt
        # We assume general question if raw text
        prompt = f"""คุณเป็น AI Assistant (Smart Terminal) ที่เชี่ยวชาญด้าน Programming
        
คำถามจาก Developer:
"{query}"

ช่วยตอบคำถามนี้อย่างกระชับ ตรงประเด็น และถ้ามีโค้ดตัวอย่าง ขอให้เน้น Best Practices:"""

        # 2. Check for clipboard context (optional)
        # If user copied something recently (text/code), we append it?
        # Maybe too intrusive. Let's keep it simple or check length.
        # Flow: User copies code -> F8 -> types "fix this"
        # So we SHOULD check clipboard.
        
        try:
             clip_content = pyperclip.paste()
             # Heuristic: if clipboard has > 5 chars and looks like code or text
             if clip_content and len(clip_content.strip()) > 5:
                 prompt += f"\n\n---\nContext (จาก Clipboard):\n```\n{clip_content[:2000]}\n```\n(Note: Context ตัดมาแค่ 2000 ตัวอักษร)"
        except:
            pass

        # 3. Copy to clipboard
        pyperclip.copy(prompt)
        
        # 4. Open ChatGPT
        webbrowser.open("https://chat.openai.com/")
        
        # 5. Notify (via print/log, main thread handles UI)
        return True
