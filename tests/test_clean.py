"""
Tests for clean.py module.
Tests the clean_nodejs command functionality.
"""

import os
import json
import tempfile
from pathlib import Path
from unittest import mock

import pytest
from setuptools.dist import Distribution
from setuptools_nodejs.clean import clean_nodejs
from setuptools_nodejs.extension import NodeJSExtension


class MockDistribution(Distribution):
    """Mock distribution for testing."""
    
    def __init__(self, extensions=None):
        super().__init__()
        self.nodejs_extensions = extensions or []
        self.verbose = False
        self.dry_run = False
        
    def get_command_obj(self, command, create=True):
        """Mock implementation to avoid command lookup errors."""
        return None


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_extension(temp_dir):
    """Create a mock NodeJSExtension with temp directory."""
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    return NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )


@pytest.fixture
def clean_command():
    """Create a clean_nodejs command instance."""
    cmd = clean_nodejs(MockDistribution())
    cmd.initialize_options()
    return cmd


def test_clean_nodejs_initialization(clean_command):
    """Test clean_nodejs command initialization."""
    assert clean_command.description == "clean Node.js extensions (remove node_modules and build artifacts)"
    assert hasattr(clean_command, 'inplace')
    assert clean_command.inplace is False


def test_clean_nodejs_with_npm_clean_script(temp_dir, clean_command):
    """Test clean_nodejs when package.json has clean script."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create package.json with clean script
    package_json = source_dir / "package.json"
    package_json.write_text(json.dumps({
        "name": "test-project",
        "scripts": {
            "clean": "echo 'Cleaning...' && rm -rf node_modules dist"
        }
    }))
    
    # Create mock extension
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )
    
    # Mock check_subprocess_output to simulate successful npm clean
    with mock.patch('setuptools_nodejs.clean.check_subprocess_output') as mock_check:
        clean_command.run_for_extension(extension)
        
        # Verify npm run clean was called
        mock_check.assert_called_once()
        args = mock_check.call_args[0][0]
        assert args[0] == "npm"
        assert args[1] == "run"
        assert args[2] == "clean"


def test_clean_nodejs_without_npm_clean_script(temp_dir, clean_command):
    """Test clean_nodejs when package.json doesn't have clean script."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create package.json without clean script
    package_json = source_dir / "package.json"
    package_json.write_text(json.dumps({
        "name": "test-project",
        "scripts": {
            "build": "echo 'Building...'"
        }
    }))
    
    # Create directories to be cleaned
    node_modules = source_dir / "node_modules"
    node_modules.mkdir()
    (node_modules / "some-package").mkdir()
    
    artifacts_dir = source_dir / "dist"
    artifacts_dir.mkdir()
    (artifacts_dir / "bundle.js").write_text("test content")
    
    # Create mock extension
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )
    
    # Mock logger to capture output
    with mock.patch('setuptools_nodejs.clean.logger') as mock_logger:
        clean_command.run_for_extension(extension)
        
        # Verify directories were removed
        assert not node_modules.exists()
        assert not artifacts_dir.exists()
        
        # Verify logging was called
        mock_logger.info.assert_called()


def test_clean_nodejs_no_package_json(temp_dir, clean_command):
    """Test clean_nodejs when package.json doesn't exist."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create directories to be cleaned
    node_modules = source_dir / "node_modules"
    node_modules.mkdir()
    
    artifacts_dir = source_dir / "dist"
    artifacts_dir.mkdir()
    
    # Create mock extension
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )
    
    clean_command.run_for_extension(extension)
    
    # Verify directories were removed
    assert not node_modules.exists()
    assert not artifacts_dir.exists()


def test_clean_nodejs_npm_clean_fails(temp_dir, clean_command):
    """Test clean_nodejs when npm run clean fails."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create package.json with clean script
    package_json = source_dir / "package.json"
    package_json.write_text(json.dumps({
        "name": "test-project",
        "scripts": {
            "clean": "echo 'Cleaning...'"
        }
    }))
    
    # Create directories to be cleaned
    node_modules = source_dir / "node_modules"
    node_modules.mkdir()
    
    artifacts_dir = source_dir / "dist"
    artifacts_dir.mkdir()
    
    # Create mock extension
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )
    
    # Mock check_subprocess_output to raise exception
    with mock.patch('setuptools_nodejs.clean.check_subprocess_output', 
                   side_effect=Exception("npm failed")):
        clean_command.run_for_extension(extension)
    
    # Verify directories were still removed (fallback to manual cleanup)
    assert not node_modules.exists()
    assert not artifacts_dir.exists()


def test_clean_nodejs_with_quiet_flag(temp_dir, clean_command):
    """Test clean_nodejs with quiet flag."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create directories to be cleaned
    node_modules = source_dir / "node_modules"
    node_modules.mkdir()
    
    artifacts_dir = source_dir / "dist"
    artifacts_dir.mkdir()
    
    # Create mock extension with quiet flag
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
        quiet=True,
    )
    
    # Mock logger to capture output
    with mock.patch('setuptools_nodejs.clean.logger') as mock_logger:
        clean_command.run_for_extension(extension)
        
        # Verify directories were removed
        assert not node_modules.exists()
        assert not artifacts_dir.exists()
        
        # Verify no logging calls for quiet mode
        # (logger.info should not be called for quiet mode)
        # We'll check that info wasn't called with the specific message
        info_calls = [call for call in mock_logger.info.call_args_list 
                     if call and call[0] and "Removing" in str(call[0])]
        assert len(info_calls) == 0


def test_clean_nodejs_with_additional_args(temp_dir, clean_command):
    """Test clean_nodejs with additional npm arguments."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create package.json with clean script
    package_json = source_dir / "package.json"
    package_json.write_text(json.dumps({
        "name": "test-project",
        "scripts": {
            "clean": "echo 'Cleaning...'"
        }
    }))
    
    # Create mock extension with additional args
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
        args=["--silent", "--production"],
    )
    
    # Mock check_subprocess_output
    with mock.patch('setuptools_nodejs.clean.check_subprocess_output') as mock_check:
        clean_command.run_for_extension(extension)
        
        # Verify npm run clean was called with additional args
        mock_check.assert_called_once()
        args = mock_check.call_args[0][0]
        assert args[0] == "npm"
        assert args[1] == "run"
        assert args[2] == "clean"
        assert "--silent" in args
        assert "--production" in args


def test_clean_nodejs_nonexistent_directories(temp_dir, clean_command):
    """Test clean_nodejs when directories don't exist."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Don't create node_modules or dist directories
    
    # Create mock extension
    extension = NodeJSExtension(
        target="test",
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )
    
    # This should not raise any exceptions
    clean_command.run_for_extension(extension)
    
    # Verify source directory still exists
    assert source_dir.exists()


def test_clean_nodejs_with_dict_target(temp_dir, clean_command):
    """Test clean_nodejs with dictionary target."""
    # Create test directory structure
    source_dir = temp_dir / "test_project"
    source_dir.mkdir()
    
    # Create directories to be cleaned
    node_modules = source_dir / "node_modules"
    node_modules.mkdir()
    
    artifacts_dir = source_dir / "dist"
    artifacts_dir.mkdir()
    
    # Create mock extension with dict target
    extension = NodeJSExtension(
        target={"frontend": "myapp.frontend", "backend": "myapp.backend"},
        source_dir=str(source_dir),
        artifacts_dir="dist",
    )
    
    clean_command.run_for_extension(extension)
    
    # Verify directories were removed
    assert not node_modules.exists()
    assert not artifacts_dir.exists()


def test_clean_nodejs_inplace_option():
    """Test clean_nodejs inplace option."""
    cmd = clean_nodejs(MockDistribution())
    cmd.initialize_options()
    
    # Set inplace to True
    cmd.inplace = True
    
    # Create a mock extension
    mock_extension = mock.MagicMock(spec=NodeJSExtension)
    mock_extension.source_dir = "/test/path"
    mock_extension.artifacts_dir = "dist"
    mock_extension.args = ()
    mock_extension.quiet = False
    mock_extension.optional = False
    mock_extension.get_artifact_path.return_value = "/test/path/dist"
    
    # Mock os.path.exists to return False for package.json, True for directories
    def exists_side_effect(path):
        if "package.json" in path:
            return False
        # Return True for node_modules and artifacts directory
        return "node_modules" in path or "dist" in path
    
    # Mock os.path.join to return correct paths
    with mock.patch('os.path.join') as mock_join:
        mock_join.side_effect = lambda *args: "/".join(args)
        
        # Mock os.path.exists with side effect
        with mock.patch('os.path.exists', side_effect=exists_side_effect):
            # Mock shutil.rmtree to track calls
            with mock.patch('shutil.rmtree') as mock_rmtree:
                cmd.run_for_extension(mock_extension)
                
                # Verify rmtree was called with correct paths
                assert mock_rmtree.call_count == 2
                
                # First call should be for node_modules
                first_call_path = mock_rmtree.call_args_list[0][0][0]
                assert "node_modules" in first_call_path
                
                # Second call should be for artifacts directory
                second_call_path = mock_rmtree.call_args_list[1][0][0]
                assert second_call_path == "/test/path/dist"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
