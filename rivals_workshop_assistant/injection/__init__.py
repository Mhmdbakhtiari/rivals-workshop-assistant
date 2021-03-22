from pathlib import Path

from .installation import update_injection_library
from .application import apply_injection
from .library import read_injection_library
from ..paths import Scripts


def handle_injection(root_dir: Path, scripts: Scripts):
    """Controller"""
    update_injection_library(root_dir)
    injection_library = read_injection_library(root_dir)
    result_scripts = apply_injection(scripts, injection_library)
    return result_scripts
