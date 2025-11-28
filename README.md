# setuptools-nodejs

A setuptools extension for building Node.js frontend projects and packaging them with Python code.

[中文文档](README_CN.md) | [English Documentation](README.md)

## Overview

`setuptools-nodejs` extends setuptools to automatically build Node.js frontend projects and include the built artifacts in your Python packages. It's perfect for full-stack Python applications that include frontend components built with frameworks like React, Vue, Angular, etc.

## Features

- 🔧 **Automatic Frontend Building**: Builds frontend projects during Python package builds
- 📦 **Seamless Integration**: Works with standard Python packaging tools (`build`, `pip`, `twine`)
- ⚙️ **Simple Configuration**: Configure everything in `pyproject.toml`
- 🛠️ **Flexible Commands**: Standalone CLI for development builds
- 📝 **Structured Logging**: Comprehensive logging using Python's standard logging module
- 🔄 **Incremental Support**: Optional clean builds and dependency skipping
- 🗂️ **Smart File Filtering**: Automatically excludes `node_modules` from source distributions

## Installation

```bash
pip install setuptools-nodejs
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
ext-modules = [
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

## Configuration

### Basic Configuration

```toml
[tool.setuptools-nodejs]
ext-modules = [
    {target = "my-frontend", source_dir = "frontend", artifacts_dir = "dist"}
]
```

### Multiple Frontend Projects

```toml
[tool.setuptools-nodejs]
ext-modules = [
    {target = "admin-panel", source_dir = "admin", artifacts_dir = "dist"},
    {target = "client-app", source_dir = "client", artifacts_dir = "build"}
]
```

### Advanced Configuration

```toml
[tool.setuptools-nodejs]
ext-modules = [
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

## Usage

### Command Line Interface

#### Build Frontend

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

#### Validate Configuration

```bash
python -m setuptools_nodejs validate
```

#### Clean Output

```bash
python -m setuptools_nodejs clean
```

### Python Build Integration

When you build your Python package using standard tools, the frontend build happens automatically:

```bash
# Build wheel (includes frontend)
python -m build --wheel

# Build source distribution (includes frontend)
python -m build --sdist
```

### Build Configuration Settings

You can control the build behavior using configuration settings:

```bash
# Skip frontend build
python -m build --config-setting=skip_frontend_build=true

# Continue build even if frontend fails
python -m build --config-setting=fail_on_frontend_error=false
```

## Project Structure Examples

### Basic Full-Stack App

```
my-app/
├── frontend/              # React/Vue frontend
│   ├── package.json
│   ├── src/
│   └── public/
├── my_app/               # Python package
│   ├── __init__.py
│   └── static/           # ← Built frontend goes here
└── pyproject.toml
```

### Multiple Frontend Projects

```
my-project/
├── admin-frontend/       # Admin dashboard
│   └── package.json
├── client-frontend/      # Client-facing app
│   └── package.json
├── my_package/
│   ├── __init__.py
│   ├── admin/            # ← Admin frontend
│   └── client/           # ← Client frontend
└── pyproject.toml
```

## Error Handling

### Common Issues

1. **Node.js not found**: Make sure Node.js and npm are installed and in your PATH
2. **Missing configuration**: Ensure `[tool.setuptools.nodejs]` section exists in pyproject.toml
3. **Build failures**: Check frontend build logs for specific errors

### Debugging

Enable verbose logging to see detailed build information:

```bash
python -m setuptools_nodejs build --verbose
```

## Development

### Setup Development Environment

```bash
# Clone the repository
git clone https://gitlab.ee-yyk.com/tools/setuptools-nodejs
cd setuptools-nodejs

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov

# Run specific test file
pytest tests/test_config.py
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

If you encounter any problems or have questions, please:

1. Check the [documentation](https://gitlab.ee-yyk.com/tools/setuptools-nodejs#readme)
2. Search [existing issues](https://gitlab.ee-yyk.com/tools/setuptools-nodejs/issues)
3. Create a [new issue](https://gitlab.ee-yyk.com/tools/setuptools-nodejs/issues/new)

## Acknowledgments

- Inspired by the need to simplify full-stack Python application packaging
- Built on top of the excellent setuptools library
- Thanks to all contributors and users
