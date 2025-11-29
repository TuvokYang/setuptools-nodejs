# setuptools-nodejs

A setuptools extension for building Node.js frontend projects and packaging them with Python code, specifically designed for full-stack applications with Python backend frameworks like Flask and FastAPI.

> **Design Inspiration**: This project draws inspiration from [setuptools-rust](https://github.com/PyO3/setuptools-rust) and [setuptools-scm](https://github.com/pypa/setuptools-scm), adopting similar extension patterns and configuration approaches for seamless integration with the Python packaging ecosystem.

[中文文档](README_CN.md) | [English Documentation](README.md)

## Overview

`setuptools-nodejs` extends setuptools to automatically build Node.js frontend projects and include the built artifacts in your Python packages. It's perfect for full-stack Python applications that include frontend components built with frameworks like React, Vue, Angular, etc.

## Project Implementation Entry Points

### Main Entry Files
- `setuptools_nodejs.setuptools_ext.pyprojecttoml_config` - Configuration parsing entry point
- `setuptools_nodejs.build.build_nodejs` - Build command implementation
- `setuptools_nodejs.extension.NodeJSExtension` - Frontend project configuration class

### Project Structure
```
setuptools-nodejs/
├── src/setuptools_nodejs/
│   ├── setuptools_ext.py    # setuptools integration and configuration parsing
│   ├── extension.py         # NodeJSExtension class definition
│   ├── build.py            # Build command implementation
│   ├── command.py          # Command base class
│   ├── clean.py            # Clean command
│   └── _utils.py           # Utility functions
├── examples/vue-helloworld/ # Working example project
│   ├── browser/            # Vue frontend project
│   │   ├── package.json    # Frontend dependency configuration
│   │   ├── vite.config.ts  # Vite build configuration
│   │   └── src/            # Frontend source code
│   ├── python/             # Python package
│   └── pyproject.toml      # Project configuration
└── tests/                  # Test files
```

## Quick Start

### 1. Configure Your Project

Add the following to your `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools", "setuptools-nodejs"]
build-backend = "setuptools.build_meta"

[project]
name = "my-fullstack-app"
version = "0.1.0"

[tool.setuptools-nodejs]
frontend-projects = [
    {target = "my-frontend", source_dir = "frontend", artifacts_dir = "dist"}
]
```

### 2. Build Your Package

```bash
python -m build
```

This will automatically:
1. Build your frontend project using npm (`npm install` and `npm run build`)
2. Copy the build artifacts to the package directory
3. Package everything into a Python wheel or sdist

## Configuration Examples

### Basic Configuration (Based on vue-helloworld example)

```toml
[build-system]
requires = ["setuptools", "setuptools-nodejs"]
build-backend = "setuptools.build_meta"

[project]
name = "vue-helloword"
version = "0.1.0"
description = "Test project for setuptools-nodejs integration"

[tool.setuptools-nodejs]
frontend-projects = [
    {target = "vue-helloword", source_dir = "browser", artifacts_dir = "dist"}
]

[tool.setuptools.packages.find]
where = ["python"]
```

### Multiple Frontend Projects with Output Directories

```toml
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "admin-panel", source_dir = "admin", artifacts_dir = "dist", output_dir = "my_package/admin"},
    {target = "client-app", source_dir = "client", artifacts_dir = "build", output_dir = "my_package/client"}
]
```

### Advanced Configuration

```toml
[tool.setuptools-nodejs]
frontend-projects = [
    {
        target = "my-app",
        source_dir = "frontend",
        artifacts_dir = "dist",
        args = ["--production"],  # Additional npm arguments
        quiet = false,            # Show npm output
        optional = false          # Fail build if frontend build fails
    }
]
```

## Currently Implemented Features

### ✅ Implemented and Working
- **Automatic Frontend Building**: Automatically runs `npm install` and `npm run build`
- **Build Artifact Copying**: Automatically copies frontend build artifacts to Python package
- **Multiple Project Support**: Supports configuring multiple frontend projects
- **Configuration Parsing**: Correctly parses configuration from `pyproject.toml`
- **Vue Project Support**: vue-helloworld example verified to work correctly
- **Basic Error Handling**: Basic build error handling

### Command Line Interface

```bash
# Build frontend using configuration from pyproject.toml
python -m setuptools_nodejs build

# Build without installing dependencies
python -m setuptools_nodejs build --no-install

# Clean output directory before build
python -m setuptools_nodejs build --clean

# Verbose logging
python -m setuptools_nodejs build --verbose
```

## Unimplemented Features and TODO List

### ❌ Code Exists but Untested/Incomplete

1. **Framework Auto-detection Feature**
   - `_detect_artifacts_dir` method exists but not thoroughly tested
   - Vue detection: Only checks config file existence, doesn't parse actual configuration
   - Angular detection: Attempts to parse `angular.json` but error handling is simple
   - React detection: Only checks for "build" script, doesn't parse output directory
   - **Need to add test cases to verify detection logic**

2. **Version Check Feature**
   - `get_node_version()` and `get_npm_version()` methods exist but never called
   - No actual validation of Node.js and npm versions during build process
   - **Need to implement version check logic and add calls**

3. **Dependency Declaration**
   - Version check requires `semantic_version` package but not declared in dependencies
   - **Need to add dependency declaration in pyproject.toml**

### Priority TODO
- [ ] Add test cases for framework auto-detection feature
- [ ] Implement Node.js and npm version check functionality
- [ ] Actually call version check methods during build process
- [ ] Add `semantic_version` dependency declaration
- [ ] Improve error handling and user feedback for framework detection
- [ ] **npm Version Validation**: Add proper npm version checking before build
- [ ] **Framework-Specific Artifacts Detection**: 
  - [ ] Vue.js: Properly parse `vite.config.*` and `vue.config.js` for output directory
  - [ ] Angular: Complete `angular.json` parsing with proper error handling
  - [ ] React: Parse `package.json` build scripts and configuration files for output paths
- [ ] **Enhanced Configuration Validation**: Validate all configuration parameters before build
- [ ] **Better Error Messages**: Provide more informative error messages for common issues

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://github.com/TuvokYang/setuptools-nodejs
cd setuptools-nodejs

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any problems or have questions, please:
1. Check the [documentation](https://github.com/TuvokYang/setuptools-nodejs#readme)
2. Search [existing issues](https://github.com/TuvokYang/setuptools-nodejs/issues)
3. Create a [new issue](https://github.com/TuvokYang/setuptools-nodejs/issues/new)
