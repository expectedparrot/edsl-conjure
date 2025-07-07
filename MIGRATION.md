# Migration Guide: From EDSL Plugin to Standalone Package

This document outlines the changes made to migrate Conjure from an EDSL plugin to a standalone package using Poetry.

## What's Changed

1. **Removed Plugin System**
   - Removed `plugin.py` and the plugin registration mechanism
   - Removed pluggy dependency
   - Removed EDSL entry points from configuration files

2. **Package Management**
   - Migrated from setuptools to uv for dependency management
   - Updated `pyproject.toml` for uv compatibility
   - Removed `poetry.lock` file in favor of uv.lock

3. **Installation**
   - Now uses `uv sync` instead of pip install with EDSL plugin registration

## How to Use Conjure

### Before (as EDSL Plugin)

```python
import edsl
# Conjure was automatically available as edsl.Conjure through the plugin system

survey = edsl.Conjure("survey_data.csv").to_survey()
```

### Now (as Standalone Package)

```python
from conjure import Conjure

survey = Conjure("survey_data.csv").to_survey()
```

## Installation

### Install with uv

```bash
cd edsl-conjure
uv sync
```

### Development Installation

```bash
cd edsl-conjure
uv sync --dev
```

## EDSL Compatibility

This package still depends on EDSL for some functionality, but no longer registers as a plugin. You'll need to have EDSL installed in your environment if you're using features that depend on EDSL components.

To update your code to work with the standalone version, replace any references to `edsl.Conjure` with direct imports from `conjure`.