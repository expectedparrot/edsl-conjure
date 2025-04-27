import os
import sys
import importlib
import pkg_resources
from pprint import pprint

# Check current directory
print("Current directory:", os.getcwd())

# Check entry points
print("\nEntry points:")
edsl_entry_points = list(pkg_resources.iter_entry_points('edsl'))
edsl_plugins_entry_points = list(pkg_resources.iter_entry_points('edsl_plugins'))
print("edsl entry points:", edsl_entry_points)
print("edsl_plugins entry points:", edsl_plugins_entry_points)

# Try to load the plugin
try:
    from conjure.plugin import conjure_plugin
    print("\nPlugin imported successfully")
    print("Plugin name:", conjure_plugin.plugin_name())
    
    # Check if exports_to_namespace is implemented
    if hasattr(conjure_plugin, "exports_to_namespace"):
        exports = conjure_plugin.exports_to_namespace()
        print("Exports from plugin:", exports)
    else:
        print("exports_to_namespace not implemented")
except Exception as e:
    print(f"Error importing plugin: {e}")

# Try to import directly from edsl
try:
    import edsl
    print("\nEDSL imported successfully")
    print("Conjure in edsl namespace:", "Conjure" in dir(edsl))
    print("dir(edsl):", dir(edsl))
    
    print("\nChecking edsl.plugins exports:")
    from edsl.plugins import get_exports
    print("Exports from plugins:", get_exports())
except Exception as e:
    print(f"Error importing edsl: {e}")