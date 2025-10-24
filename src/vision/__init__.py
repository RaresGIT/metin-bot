"""Vision layer for screen capture and target detection."""
from .screen_capture import MonitorManager, ScreenCapture
from .image_matcher import ImageMatcher, ImageMatch
from .target_finder import TargetFinder, Target
from .color_detector import ColorBasedDetector, ColorCluster

__all__ = [
    "MonitorManager",
    "ScreenCapture",
    "ImageMatcher",
    "ImageMatch",
    "TargetFinder",
    "Target",
    "ColorBasedDetector",
    "ColorCluster",
]
