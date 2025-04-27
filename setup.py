# No longer needed with poetry - kept for backward compatibility
# This file will eventually be removed

from setuptools import setup, find_packages

setup(
    name="conjure",
    version="0.1.0",
    description="A tool that converts survey data files into edsl objects",
    packages=find_packages(),
    python_requires=">=3.11",
    install_requires=[
        "edsl @ git+https://github.com/expectedparrot/edsl.git@3716ac68c474a35b127052a80c9d8757114e3ccf"
    ],
)