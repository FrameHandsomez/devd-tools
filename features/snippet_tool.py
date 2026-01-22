from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType

class SnippetTool(BaseFeature):
    name = "snippet_tool"
    description = "Launch Snippet Manager"
    supported_patterns = [PressType.SHORT, PressType.LONG, PressType.DOUBLE]

    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        if action == "execute":
            # Call the command registered in bootstrap.py
            success = self.command_executor.execute("launch_snippets")
            if success:
                 return FeatureResult(FeatureStatus.SUCCESS, "Snippet Manager launched")
            else:
                 return FeatureResult(FeatureStatus.ERROR, "Failed to launch Snippet Manager")
        
        return FeatureResult(FeatureStatus.ERROR, f"Unknown action: {action}")
