# CLAUDE.md - Guidelines for Conjure Codebase

## Build & Test Commands
- Run doctests in a file: `python -m doctest filename.py`
- Run doctests with verbose output: `python -m doctest filename.py -v`
- Run module directly (also runs tests): `python filename.py`

## Code Style Guidelines
- **Imports**: Standard library → Third-party → Project imports, grouped with blank lines
- **Formatting**: 4-space indentation, triple quotes for docstrings
- **Types**: Use typing module (List, Dict, Optional, Union, etc.)
- **Naming**: CamelCase classes, snake_case methods/variables, UPPER_CASE constants
- **Error Handling**: Use specific exceptions with descriptive messages
- **Docstrings**: Include examples, parameter descriptions, and doctests
- **Design Patterns**: Use mixins for shared functionality, ABC for interfaces
- **Documentation**: Write docstrings with examples as doctests