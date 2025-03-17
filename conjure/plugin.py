"""
Plugin interface for edsl integration
"""
import pluggy
from .conjure import Conjure
from typing import Dict, Any, Optional

# Register with the "edsl" plugin system
hookimpl = pluggy.HookimplMarker("edsl")

class ConjurePlugin:
    """Plugin class for edsl integration"""
    
    @hookimpl
    def plugin_name(self):
        """Return the name of the plugin."""
        return "Conjure"
    
    @hookimpl
    def get_plugin_methods(self):
        """Return a dictionary of methods provided by this plugin."""
        return {}
    
    @hookimpl
    def plugin_description(self):
        """Return a description of the plugin."""
        return "A plugin for edsl that converts survey data files into edsl objects"
    
    @hookimpl
    def edsl_plugin(self, plugin_name=None):
        """Return the Conjure class for integration with edsl"""
        return Conjure
    
    @hookimpl
    def exports_to_namespace(self) -> Optional[Dict[str, Any]]:
        """
        Define objects that should be exported to the global namespace.
        
        This is the key hook that allows Conjure to be available directly in edsl.
        """
        return {"Conjure": Conjure}
        
# Create a plugin instance
conjure_plugin = ConjurePlugin()