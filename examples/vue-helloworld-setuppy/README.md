# Vue HelloWorld with Traditional setup.py

This is a test project demonstrating the integration of `setuptools-nodejs` with traditional `setup.py` configuration.

## Purpose

This example shows how to use `setuptools-nodejs` with the traditional `setup.py` approach instead of the modern `pyproject.toml` configuration. It's useful for:

1. Testing compatibility with legacy projects
2. Demonstrating alternative configuration methods
3. Providing a reference for projects that cannot migrate to `pyproject.toml`

## Project Structure

```
vue-helloworld-setuppy/
├── browser/                    # Vue.js frontend project
│   ├── package.json
│   ├── vite.config.ts
│   ├── src/
│   └── dist/                  # Built frontend artifacts
├── vue_helloworld_setuppy/    # Python package
│   └── __init__.py
├── setup.py                   # Traditional setup configuration
├── MANIFEST.in                # Manifest for including frontend artifacts
└── README.md                  # This file
```

## Configuration

The key configuration is in `setup.py`:

```python
from setuptools_nodejs import NodeJSExtension

setup(
    # ... other setup arguments ...
    nodejs_extensions=[
        NodeJSExtension(
            target="vue_helloworld_setuppy",
            source_dir="browser",
            artifacts_dir="dist",
        ),
    ],
)
```

## Building and Installation

### 1. Build the frontend

```bash
cd browser
npm install
npm run build
```

### 2. Create source distribution (sdist)

```bash
python setup.py sdist
```

This will create a `.tar.gz` file in the `dist/` directory containing both Python code and frontend build artifacts.

### 3. Install the package

```bash
pip install .
```

During installation, `setuptools-nodejs` will:
1. Detect the `nodejs_extensions` configuration
2. Build the frontend if not already built
3. Include the built artifacts in the installed package

## Testing

This example is used for testing `setuptools-nodejs` functionality with traditional `setup.py` configuration. It helps ensure:

- Proper handling of `nodejs_extensions` in `setup()`
- Correct inclusion of frontend artifacts in sdist
- Successful build and installation workflows

## Comparison with pyproject.toml

| Aspect | setup.py | pyproject.toml |
|--------|----------|----------------|
| Configuration | Python code in `setup()` | TOML in `[tool.setuptools-nodejs]` |
| Flexibility | Full Python programmability | Declarative configuration |
| Modern standards | Legacy approach | PEP 517/518 compliant |
| Integration | Direct import of `NodeJSExtension` | Tool-specific section |

## Notes

- The frontend must be built before creating sdist, or `setuptools-nodejs` will build it during packaging
- `MANIFEST.in` ensures frontend artifacts are included in source distribution
- This example complements the existing `vue-helloworld` example which uses `pyproject.toml`
