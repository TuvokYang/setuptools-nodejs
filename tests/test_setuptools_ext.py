"""
Tests for setuptools_nodejs.setuptools_ext module.
"""

import os
import tempfile
from pathlib import Path
import pytest

from setuptools_nodejs.setuptools_ext import (
    get_nodejs_extensions_from_config,
    _create,
    find_nodejs_source_files,
    pyprojecttoml_config,
    nodejs_extensions,
    add_nodejs_extension,
)
from setuptools_nodejs.extension import NodeJSExtension
from setuptools.dist import Distribution


def create_pyproject_toml(directory: Path, content: str) -> None:
    """Create a pyproject.toml file in the given directory."""
    pyproject_path = directory / "pyproject.toml"
    pyproject_path.write_text(content, encoding="utf-8")


def test_get_nodejs_extensions_from_config_basic():
    """Test parsing basic pyproject.toml configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml with basic config
        pyproject_content = """
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "myapp", source_dir = "frontend", artifacts_dir = "dist"}
]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        # Change to temporary directory to read pyproject.toml
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Verify results
            assert len(extensions) == 1
            ext = extensions[0]
            assert ext.name == "myapp"
            assert ext.source_dir == "frontend"
            assert ext.artifacts_dir == "dist"
            assert ext.package_artifacts_dir == "frontend"  # Default value (output_dir defaults to "frontend")
            assert ext.args == ()  # Default value is empty tuple, not list
            assert ext.env is not None  # env is always an Env object
            assert ext.env.env is None  # But env.env is None by default
            assert ext.node_version is None  # Default value
            assert ext.npm_version is None  # Default value
            assert ext.quiet is False  # Default value
            assert ext.optional is False  # Default value
            # exclude_dirs includes ["node_modules", "dist", "frontend"] (artifacts_dir and package_artifacts_dir are added)
            assert "node_modules" in ext.exclude_dirs
            assert "dist" in ext.exclude_dirs
            assert "frontend" in ext.exclude_dirs
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_multiple():
    """Test parsing multiple frontend projects."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml with multiple projects
        pyproject_content = """
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "app1", source_dir = "frontend1", artifacts_dir = "dist1"},
    {target = "app2", source_dir = "frontend2", artifacts_dir = "dist2"}
]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Verify results
            assert len(extensions) == 2
            
            # Check first extension
            ext1 = extensions[0]
            assert ext1.name == "app1"
            assert ext1.source_dir == "frontend1"
            assert ext1.artifacts_dir == "dist1"
            
            # Check second extension
            ext2 = extensions[1]
            assert ext2.name == "app2"
            assert ext2.source_dir == "frontend2"
            assert ext2.artifacts_dir == "dist2"
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_full():
    """Test parsing all configuration options."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml with full configuration using table array syntax
        # Note: NodeJSExtension uses "output-dir" not "package-artifacts-dir"
        pyproject_content = """
[[tool.setuptools-nodejs.frontend-projects]]
target = "myapp"
source_dir = "frontend"
artifacts_dir = "dist"
output-dir = "static"
args = ["--verbose", "--production"]
node-version = ">=18.0.0"
npm-version = ">=9.0.0"
quiet = true
optional = true
exclude-dirs = ["node_modules", "test", "coverage"]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Verify results
            assert len(extensions) == 1
            ext = extensions[0]
            
            assert ext.name == "myapp"
            assert ext.source_dir == "frontend"
            assert ext.artifacts_dir == "dist"
            assert ext.package_artifacts_dir == "static"  # output-dir maps to package_artifacts_dir
            assert ext.args == ("--verbose", "--production")  # args is a tuple
            assert ext.env is not None
            # env should be None since we didn't specify it
            assert ext.env.env is None
            assert ext.node_version == ">=18.0.0"
            assert ext.npm_version == ">=9.0.0"
            assert ext.quiet is True
            assert ext.optional is True
            # exclude_dirs includes the provided ones plus artifacts_dir and package_artifacts_dir
            assert "node_modules" in ext.exclude_dirs
            assert "test" in ext.exclude_dirs
            assert "coverage" in ext.exclude_dirs
            assert "dist" in ext.exclude_dirs  # artifacts_dir added
            assert "static" in ext.exclude_dirs  # package_artifacts_dir added
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_table_array_syntax():
    """Test parsing table array syntax (not inline tables)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml with table array syntax
        pyproject_content = """
[[tool.setuptools-nodejs.frontend-projects]]
target = "myapp"
source_dir = "frontend"
artifacts_dir = "dist"
output_dir = "static"
node_version = ">=18.0.0"
npm_version = ">=9.0.0"
quiet = true
optional = true
exclude_dirs = ["node_modules", "test", "coverage"]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Verify results
            assert len(extensions) == 1
            ext = extensions[0]
            
            assert ext.name == "myapp"
            assert ext.source_dir == "frontend"
            assert ext.artifacts_dir == "dist"
            assert ext.package_artifacts_dir == "static"
            assert ext.args == ()
            assert ext.env is not None
            assert ext.env.env is None
            assert ext.node_version == ">=18.0.0"
            assert ext.npm_version == ">=9.0.0"
            assert ext.quiet is True
            assert ext.optional is True
            # exclude_dirs includes the provided ones plus artifacts_dir and package_artifacts_dir
            assert "node_modules" in ext.exclude_dirs
            assert "test" in ext.exclude_dirs
            assert "coverage" in ext.exclude_dirs
            assert "dist" in ext.exclude_dirs
            assert "static" in ext.exclude_dirs
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_multiple_table_array():
    """Test parsing multiple projects using table array syntax."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml with multiple table arrays
        pyproject_content = """
[[tool.setuptools-nodejs.frontend-projects]]
target = "app1"
source_dir = "frontend1"
artifacts_dir = "dist1"
output_dir = "static1"
node_version = ">=18.0.0"

[[tool.setuptools-nodejs.frontend-projects]]
target = "app2"
source_dir = "frontend2"
artifacts_dir = "dist2"
output_dir = "static2"
npm_version = ">=9.0.0"
quiet = true

[[tool.setuptools-nodejs.frontend-projects]]
target = "app3"
source_dir = "frontend3"
artifacts_dir = "dist3"
# No output_dir, should default to "frontend"
optional = true
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Verify results
            assert len(extensions) == 3
            
            # Check first extension
            ext1 = extensions[0]
            assert ext1.name == "app1"
            assert ext1.source_dir == "frontend1"
            assert ext1.artifacts_dir == "dist1"
            assert ext1.package_artifacts_dir == "static1"
            assert ext1.node_version == ">=18.0.0"
            assert ext1.npm_version is None
            assert ext1.quiet is False
            assert ext1.optional is False
            
            # Check second extension
            ext2 = extensions[1]
            assert ext2.name == "app2"
            assert ext2.source_dir == "frontend2"
            assert ext2.artifacts_dir == "dist2"
            assert ext2.package_artifacts_dir == "static2"
            assert ext2.node_version is None
            assert ext2.npm_version == ">=9.0.0"
            assert ext2.quiet is True
            assert ext2.optional is False
            
            # Check third extension
            ext3 = extensions[2]
            assert ext3.name == "app3"
            assert ext3.source_dir == "frontend3"
            assert ext3.artifacts_dir == "dist3"
            assert ext3.package_artifacts_dir == "frontend"  # Default value
            assert ext3.node_version is None
            assert ext3.npm_version is None
            assert ext3.quiet is False
            assert ext3.optional is True
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_no_target():
    """Test parsing configuration without target (should use source_dir as default)."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml without target
        pyproject_content = """
[tool.setuptools-nodejs]
frontend-projects = [
    {source_dir = "frontend", artifacts_dir = "dist"}
]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Verify results - target should default to source_dir
            assert len(extensions) == 1
            ext = extensions[0]
            assert ext.name == "frontend"  # Default to source_dir
            assert ext.source_dir == "frontend"
            assert ext.artifacts_dir == "dist"
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_no_file():
    """Test when pyproject.toml doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Don't create pyproject.toml
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Should return empty list
            assert extensions == []
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_no_section():
    """Test when [tool.setuptools-nodejs] section is missing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml without setuptools-nodejs section
        pyproject_content = """
[project]
name = "test-project"
version = "1.0.0"
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Should return empty list
            assert extensions == []
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_empty_frontend_projects():
    """Test when frontend-projects array is empty."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml with empty frontend-projects
        pyproject_content = """
[tool.setuptools-nodejs]
frontend-projects = []
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Should return empty list
            assert extensions == []
        finally:
            os.chdir(original_cwd)


def test_get_nodejs_extensions_from_config_invalid_toml():
    """Test with invalid TOML syntax."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create invalid pyproject.toml
        pyproject_content = """
[tool.setuptools-nodejs
frontend-projects = [
    {target = "myapp", source_dir = "frontend"}
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            extensions = get_nodejs_extensions_from_config()
            
            # Should return empty list due to parsing error
            assert extensions == []
        finally:
            os.chdir(original_cwd)


def test_create_function():
    """Test the _create helper function."""
    config = {
        "target": "myapp",
        "source_dir": "frontend",
        "artifacts_dir": "dist",
        "output-dir": "static",  # Use output-dir instead of package-artifacts-dir
        "args": ["--verbose"],
        "env": {"NODE_ENV": "production"},
        "node-version": ">=18.0.0",
        "npm-version": ">=9.0.0",
        "quiet": True,
        "optional": True,
        "exclude-dirs": ["node_modules", "test"]
    }
    
    extension = _create(NodeJSExtension, config)
    
    # Verify the extension was created correctly
    assert extension.name == "myapp"
    assert extension.source_dir == "frontend"
    assert extension.artifacts_dir == "dist"
    assert extension.package_artifacts_dir == "static"  # output-dir maps to package_artifacts_dir
    assert extension.args == ("--verbose",)  # args is a tuple
    assert extension.env is not None
    assert extension.env.env == {"NODE_ENV": "production"}
    assert extension.node_version == ">=18.0.0"
    assert extension.npm_version == ">=9.0.0"
    assert extension.quiet is True
    assert extension.optional is True
    # exclude_dirs includes the provided ones plus artifacts_dir and package_artifacts_dir
    assert "node_modules" in extension.exclude_dirs
    assert "test" in extension.exclude_dirs
    assert "dist" in extension.exclude_dirs  # artifacts_dir added
    assert "static" in extension.exclude_dirs  # package_artifacts_dir added


def test_create_function_no_target():
    """Test _create function without target (should use source_dir as default)."""
    config = {
        "source_dir": "frontend",
        "artifacts_dir": "dist"
    }
    
    extension = _create(NodeJSExtension, config)
    
    # target should default to source_dir
    assert extension.name == "frontend"
    assert extension.source_dir == "frontend"
    assert extension.artifacts_dir == "dist"


def test_find_nodejs_source_files():
    """Test find_nodejs_source_files function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml
        pyproject_content = """
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "myapp", source_dir = "frontend", artifacts_dir = "dist"}
]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        # Create source directory structure
        frontend_dir = tmpdir_path / "frontend"
        frontend_dir.mkdir()
        
        # Create some files
        (frontend_dir / "package.json").write_text('{"name": "myapp"}')
        (frontend_dir / "src" / "index.js").parent.mkdir(parents=True)
        (frontend_dir / "src" / "index.js").write_text('console.log("hello")')
        
        # Create node_modules directory (should be excluded)
        node_modules_dir = frontend_dir / "node_modules"
        node_modules_dir.mkdir()
        (node_modules_dir / "some-package" / "package.json").parent.mkdir(parents=True)
        (node_modules_dir / "some-package" / "package.json").write_text('{}')
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            files = find_nodejs_source_files(".")
            
            # Verify files were found (excluding node_modules)
            # Note: find_nodejs_source_files returns absolute paths
            assert len(files) >= 2
            
            # Convert to relative paths for easier checking
            rel_files = [os.path.relpath(f, tmpdir) for f in files]
            
            # Should include frontend files (handle both / and \ path separators)
            # Convert to forward slashes for consistent checking
            rel_files_forward = [f.replace('\\', '/') for f in rel_files]
            assert any("frontend/package.json" in f for f in rel_files_forward)
            assert any("frontend/src/index.js" in f for f in rel_files_forward)
            
            # Should NOT include node_modules files
            assert not any("node_modules" in f for f in rel_files_forward)
        finally:
            os.chdir(original_cwd)


def test_find_nodejs_source_files_no_config():
    """Test find_nodejs_source_files when no configuration exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Don't create pyproject.toml
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            files = find_nodejs_source_files(".")
            
            # Should return empty list
            assert files == []
        finally:
            os.chdir(original_cwd)


def test_pyprojecttoml_config():
    """Test pyprojecttoml_config function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Create pyproject.toml
        pyproject_content = """
[tool.setuptools-nodejs]
frontend-projects = [
    {target = "myapp", source_dir = "frontend", artifacts_dir = "dist"}
]
"""
        create_pyproject_toml(tmpdir_path, pyproject_content)
        
        # Create a mock distribution
        dist = Distribution()
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            # Call pyprojecttoml_config
            pyprojecttoml_config(dist)
            
            # Verify distribution has nodejs_extensions
            assert hasattr(dist, 'nodejs_extensions')
            assert len(dist.nodejs_extensions) == 1
            
            # Verify package_data was added
            assert hasattr(dist, 'package_data')
            assert dist.package_data is not None
            assert "*" in dist.package_data
            assert "frontend/**/*" in dist.package_data["*"]
        finally:
            os.chdir(original_cwd)


def test_pyprojecttoml_config_no_config():
    """Test pyprojecttoml_config when no configuration exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Don't create pyproject.toml
        dist = Distribution()
        
        original_cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            # Call pyprojecttoml_config
            pyprojecttoml_config(dist)
            
            # Distribution should still have nodejs_extensions attribute (empty list)
            assert hasattr(dist, 'nodejs_extensions')
            assert dist.nodejs_extensions == []
            
            # package_data may be set to empty dict by Distribution constructor
            # The important thing is that it doesn't have the frontend/**/* pattern
            if hasattr(dist, 'package_data') and dist.package_data:
                assert "*" not in dist.package_data or "frontend/**/*" not in dist.package_data.get("*", [])
        finally:
            os.chdir(original_cwd)


def test_nodejs_extensions():
    """Test nodejs_extensions function."""
    # Create a distribution
    dist = Distribution()
    
    # Create some NodeJSExtension instances
    extensions = [
        NodeJSExtension("app1", "frontend1", "dist1"),
        NodeJSExtension("app2", "frontend2", "dist2")
    ]
    
    # Manually set nodejs_extensions on distribution
    # (nodejs_extensions function doesn't set this, it's set by pyprojecttoml_config)
    dist.nodejs_extensions = extensions  # type: ignore[attr-defined]
    
    # Call nodejs_extensions
    nodejs_extensions(dist, "nodejs_extensions", extensions)
    
    # Verify distribution still has extensions
    assert hasattr(dist, 'nodejs_extensions')
    assert dist.nodejs_extensions == extensions
    
    # Verify has_ext_modules was monkey-patched
    # has_ext_modules should return True when there are extensions
    assert dist.has_ext_modules() is True


def test_nodejs_extensions_empty():
    """Test nodejs_extensions function with empty list."""
    # Create a distribution
    dist = Distribution()
    
    # Store original has_ext_modules
    original_has_ext_modules = dist.has_ext_modules
    
    # Call nodejs_extensions with empty list
    nodejs_extensions(dist, "nodejs_extensions", [])
    
    # Verify distribution has extensions (empty list)
    assert hasattr(dist, 'nodejs_extensions')
    assert dist.nodejs_extensions == []
    
    # has_ext_modules should still work (call original)
    # Note: The monkey patch adds "or has_nodejs_extensions" which is False for empty list
    # So it should behave like original
    # We need to call the original function to compare
    # Note: original_has_ext_modules is a method, we need to call it
    # But the monkey patch replaces it, so we can't call it directly
    # Instead, we verify that has_ext_modules returns False (no extensions)
    assert dist.has_ext_modules() is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
