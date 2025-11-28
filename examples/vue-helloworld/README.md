# Test Project for setuptools-nodejs

This is a test project to verify setuptools-nodejs integration.

## Project Structure

- `browser/` - Vue.js frontend project built with Vite
- `src/tests/` - Python package code
- `frontend/` - Built frontend artifacts (generated during build)

## Build Process

When building with `python -m build`:

1. Frontend is built from `browser/` to `browser/dist/`
2. Frontend artifacts are copied to `frontend/`
3. Python package `tests` is built from `src/tests/`
4. All files are packaged into distribution archives
