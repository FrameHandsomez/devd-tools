"""
Frontend Runner Feature - Run dev server for frontend projects

Actions:
- run_dev: Run the dev server (first time asks for path, then remembers)
- reset_path: Reset the saved path (triggered by multi-press)
"""

from pathlib import Path
from core.features.base_feature import BaseFeature, FeatureResult, FeatureStatus
from core.events.input_event import InputEvent, PressType
from utils.project_detector import get_dev_command
from utils.logger import get_logger

logger = get_logger(__name__)


class FrontendRunnerFeature(BaseFeature):
    """
    Feature 2: Frontend Project Runner
    
    - Short press: Run dev server (remembers path)
    - Multi-press (3x): Reset saved path
    """
    
    name = "frontend_runner"
    description = "Run frontend dev server with persistent path"
    supported_patterns = [PressType.SHORT, PressType.MULTI]
    
    CONFIG_KEY = "frontend_project"
    
    def execute(self, event: InputEvent, action: str) -> FeatureResult:
        """Execute the run_dev or reset_path action"""
        
        if action == "run_dev":
            return self._run_dev_server()
        elif action == "reset_path":
            return self._reset_path()
        else:
            return FeatureResult(
                status=FeatureStatus.ERROR,
                message=f"Unknown action: {action}"
            )
    
    def _run_dev_server(self) -> FeatureResult:
        """Run the frontend dev server"""
        
        # Check if we have a saved path
        saved_path = self.config_manager.get_saved_path(self.CONFIG_KEY)
        
        if saved_path and Path(saved_path).exists():
            project_path = Path(saved_path)
            logger.info(f"Using saved project path: {project_path}")
        else:
            # Ask for path
            from ui.dialogs import ask_folder_path
            
            project_path = ask_folder_path("Select frontend project folder")
            
            if not project_path:
                return FeatureResult(
                    status=FeatureStatus.CANCELLED,
                    message="User cancelled path selection"
                )
            
            project_path = Path(project_path)
            
            # Save the path
            self.config_manager.set_saved_path(self.CONFIG_KEY, str(project_path))
            logger.info(f"Saved project path: {project_path}")
        
        # Detect dev command
        dev_cmd = get_dev_command(project_path)
        
        if not dev_cmd:
            # Default to npm run dev
            dev_cmd = ["npm", "run", "dev"]
            logger.info("No dev script detected, using 'npm run dev'")
        
        logger.info(f"Running dev server: {' '.join(dev_cmd)}")
        
        # Execute in new terminal
        success = self.command_executor.execute_in_terminal(
            command=dev_cmd,
            cwd=project_path,
            title=f"Dev Server - {project_path.name}",
            keep_open=True
        )
        
        if success:
            return FeatureResult(
                status=FeatureStatus.SUCCESS,
                message=f"Dev server started for {project_path.name}"
            )
        
        return FeatureResult(
            status=FeatureStatus.ERROR,
            message="Failed to start dev server"
        )
    
    def _reset_path(self) -> FeatureResult:
        """Reset the saved path"""
        
        logger.info("Resetting frontend project path")
        
        # Clear saved path
        self.config_manager.set_saved_path(self.CONFIG_KEY, None)
        
        # Immediately ask for new path
        return self._run_dev_server()
