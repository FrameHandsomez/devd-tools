"""
Feature Registry - Discovers and manages feature plugins
Drop-in ready: add a new feature file and it's automatically available
"""

import importlib
import pkgutil
from pathlib import Path
from typing import Optional, TYPE_CHECKING
from core.features.base_feature import BaseFeature
from utils.logger import get_logger

if TYPE_CHECKING:
    from core.config.config_manager import ConfigManager
    from core.commands.command_executor import CommandExecutor

logger = get_logger(__name__)


class FeatureRegistry:
    """
    Discovers and manages feature plugins.
    
    Features are automatically discovered from the 'features' package.
    Each feature class that inherits from BaseFeature is registered.
    """
    
    def __init__(
        self,
        config_manager: "ConfigManager",
        command_executor: "CommandExecutor"
    ):
        self.config_manager = config_manager
        self.command_executor = command_executor
        self.features: dict[str, BaseFeature] = {}
    
    def discover_features(self):
        """
        Automatically discover and register all features.
        Scans the 'features' package for classes inheriting from BaseFeature.
        """
        # Get the features package path
        features_path = Path(__file__).parent.parent.parent / "features"
        
        if not features_path.exists():
            logger.warning(f"Features directory not found: {features_path}")
            return
        
        logger.info(f"Discovering features from: {features_path}")
        
        # Import each module in the features package
        for finder, name, ispkg in pkgutil.iter_modules([str(features_path)]):
            if name.startswith("_"):
                continue
            
            try:
                module = importlib.import_module(f"features.{name}")
                
                # Find BaseFeature subclasses in the module
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    
                    if (isinstance(attr, type) and 
                        issubclass(attr, BaseFeature) and 
                        attr is not BaseFeature):
                        
                        self.register_feature(attr)
                        
            except Exception as e:
                logger.error(f"Error loading feature module {name}: {e}")
    
    def register_feature(self, feature_class: type):
        """Register a feature class"""
        try:
            # Instantiate the feature
            feature = feature_class(
                config_manager=self.config_manager,
                command_executor=self.command_executor
            )
            
            self.features[feature.name] = feature
            logger.info(f"Registered feature: {feature.name}")
            
        except Exception as e:
            logger.error(f"Error registering feature {feature_class}: {e}")
    
    def get_feature(self, name: str) -> Optional[BaseFeature]:
        """Get a feature by name"""
        return self.features.get(name)
    
    def list_features(self) -> list[str]:
        """List all registered feature names"""
        return list(self.features.keys())
