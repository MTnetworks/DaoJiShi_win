import sys
import os

def get_resource_path(relative_path):
    """
    Get absolute path to resource.
    Prioritizes local file (allows user override), then bundled file (PyInstaller).
    """
    # Check if file exists locally first (allows override)
    local_path = os.path.join(os.path.abspath("."), relative_path)
    if os.path.exists(local_path):
        return local_path
        
    # If not found locally, and we are frozen, check bundle
    if hasattr(sys, '_MEIPASS'):
        bundled_path = os.path.join(sys._MEIPASS, relative_path)
        if os.path.exists(bundled_path):
            return bundled_path
            
    return local_path
