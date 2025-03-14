"""
Plugin interface for edsl integration
"""
import pluggy
from .conjure import Conjure

# Register with the "edsl" plugin system
hookimpl = pluggy.HookimplMarker("edsl")

class ConjurePlugin:
    """Plugin class for edsl integration"""
    
    @hookimpl
    def conjure_plugin(self):
        """Return the Conjure class for integration with edsl"""
        return Conjure
        
# Create a plugin instance
conjure_plugin = ConjurePlugin()