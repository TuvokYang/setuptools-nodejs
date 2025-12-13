#!/usr/bin/env python
"""
Traditional setup.py configuration for setuptools-nodejs integration test.
This demonstrates using setuptools-nodejs with traditional setup.py instead of pyproject.toml.
"""

from setuptools import setup, find_packages
from setuptools_nodejs import NodeJSExtension

# Read the README file for long description
try:
    with open("README.md", "r", encoding="utf-8") as fh:
        long_description = fh.read()
except FileNotFoundError:
    long_description = "Test project for setuptools-nodejs integration with traditional setup.py"

setup(
    name="vue-helloworld-setuppy",
    version="0.1.0",
    author="Test User",
    description="Test project for setuptools-nodejs integration with traditional setup.py",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license="MIT",
    packages=find_packages(),
    python_requires=">=3.7",
    install_requires=[],
    extras_require={
        "dev": ["pytest>=6.0"],
    },
    
    # Node.js extension configuration
    # This is the traditional way to configure nodejs_extensions in setup.py
    nodejs_extensions=[
        NodeJSExtension(
            target="vue_helloworld_setuppy",
            source_dir="browser",
            artifacts_dir="dist",
            # Optional: add build arguments
            # args=["--production"],
            # Optional: make extension optional
            # optional=True,
        ),
    ],
    
    # Include package data
    include_package_data=True,
    zip_safe=False,
    
    # Classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Build Tools",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    
    # Project URLs
    project_urls={
        "Source": "https://github.com/TuvokYang/setuptools-nodejs",
        "Bug Reports": "https://github.com/TuvokYang/setuptools-nodejs/issues",
    },
)
