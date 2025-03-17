"""
Plugin interface for edsl integration
"""
import sys
import pluggy
from .conjure import Conjure
from typing import Dict, Any, Optional

# Print debug information to stderr
print("Initializing conjure plugin", file=sys.stderr)

# Register with the "edsl" plugin system
hookimpl = pluggy.HookimplMarker("edsl")

class ConjurePlugin:
    """Plugin class for edsl integration"""
    
    def __init__(self):
        print("ConjurePlugin instance created", file=sys.stderr)
    
    @hookimpl
    def plugin_name(self):
        """Return the name of the plugin."""
        print("plugin_name hook called", file=sys.stderr)
        return "Conjure"
    
    @hookimpl
    def get_plugin_methods(self):
        """Return a dictionary of methods provided by this plugin."""
        print("get_plugin_methods hook called", file=sys.stderr)
        return {}
    
    @hookimpl
    def plugin_description(self):
        """Return a description of the plugin."""
        print("plugin_description hook called", file=sys.stderr)
        return "A plugin for edsl that converts survey data files into edsl objects"
    
    @hookimpl
    def edsl_plugin(self, plugin_name=None):
        """Return the Conjure class for integration with edsl"""
        print(f"edsl_plugin hook called with {plugin_name}", file=sys.stderr)
        return Conjure
    
    @hookimpl
    def exports_to_namespace(self) -> Optional[Dict[str, Any]]:
        """
        Define objects that should be exported to the global namespace.
        
        This is the key hook that allows Conjure to be available directly in edsl.
        """
        print("exports_to_namespace hook called", file=sys.stderr)
        exports = {"Conjure": Conjure}
        print(f"Exporting: {exports}", file=sys.stderr)
        return exports
        
# Create a plugin instance
conjure_plugin = ConjurePlugin()
print("conjure_plugin created", file=sys.stderr)