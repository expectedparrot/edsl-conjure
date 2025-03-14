from setuptools import setup, find_packages

setup(
    name="conjure",
    version="0.1.0",
    description="A plugin for edsl that provides conjure functionality",
    packages=find_packages(),
    install_requires=[
        "pluggy>=1.0.0",
    ],
    entry_points={
        "edsl": [
            "conjure = conjure.plugin:conjure_plugin",
        ],
    },
    python_requires=">=3.11",
)