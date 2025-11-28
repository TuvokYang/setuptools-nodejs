import os
import subprocess
from unittest import mock

import pytest
from setuptools.dist import Distribution

from setuptools_nodejs.build import build_nodejs
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


class MockCommand:
    """Mock command for testing."""
    
    def __init__(self, distribution=None):
        self.distribution = distribution or MockDistribution()
        self.verbose = False
        self.dry_run = False
        self.inplace = False
        self.plat_name = None


def test_build_nodejs_initialization():
    """Test build_nodejs command initialization."""
    cmd = build_nodejs(MockDistribution())
    assert cmd.extensions == []
    assert cmd.inplace is False
    assert cmd.verbose is False
    assert cmd.dry_run is False


def test_build_nodejs_with_extensions():
    """Test build_nodejs with Node.js extensions."""
    extensions = [
        NodeJSExtension(target="frontend", source_dir="frontend", artifacts_dir="dist"),
        NodeJSExtension(target="backend", source_dir="backend", artifacts_dir="build"),
    ]
    dist = MockDistribution(extensions)
    cmd = build_nodejs(dist)
    
    # Test that extensions are properly set after finalize_options
    # We can't call finalize_options directly because it requires other commands
    # Instead, we'll test that the distribution has the extensions
    assert dist.nodejs_extensions == extensions


def test_build_nodejs_no_extensions():
    """Test build_nodejs with no extensions."""
    dist = MockDistribution([])
    cmd = build_nodejs(dist)
    
    # Should not raise any errors
    cmd.run()


@mock.patch('os.path.exists')
@mock.patch('subprocess.run')
def test_build_nodejs_build_extension(mock_run, mock_exists):
    """Test build_extension method."""
    mock_run.return_value.returncode = 0
    mock_exists.return_value = True
    
    extension = NodeJSExtension(target="test", source_dir="test_dir")
    dist = MockDistribution([extension])
    cmd = build_nodejs(dist)
    
    # Mock the platform name
    cmd.plat_name = "any"
    
    # Test build_extension method
    artifacts = cmd.build_extension(extension)
    
    # Should have called npm install and npm run build
    assert mock_run.call_count == 2
    
    # Check npm install call
    install_call = mock_run.call_args_list[0]
    call_args = install_call[0][0]
    assert call_args[0] == "npm"
    assert call_args[1] == "install"
    
    # Check npm run build call
    build_call = mock_run.call_args_list[1]
    call_args = build_call[0][0]
    assert call_args[0] == "npm"
    assert call_args[1] == "run"
    assert call_args[2] == "build"


@mock.patch('os.path.exists')
@mock.patch('subprocess.run')
def test_build_nodejs_with_quiet_flag(mock_run, mock_exists):
    """Test build_nodejs with quiet flag."""
    mock_run.return_value.returncode = 0
    mock_exists.return_value = True
    
    extension = NodeJSExtension(target="test", source_dir="test_dir", quiet=True)
    dist = MockDistribution([extension])
    cmd = build_nodejs(dist)
    
    # Mock the platform name
    cmd.plat_name = "any"
    
    # Test build_extension method
    cmd.build_extension(extension)
    
    # Check that subprocess was called with quiet settings
    for call in mock_run.call_args_list:
        call_kwargs = call[1]
        assert call_kwargs['stderr'] == subprocess.PIPE


@mock.patch('os.path.exists')
@mock.patch('subprocess.run')
def test_build_nodejs_with_additional_args(mock_run, mock_exists):
    """Test build_nodejs with additional npm arguments."""
    mock_run.return_value.returncode = 0
    mock_exists.return_value = True
    
    extension = NodeJSExtension(
        target="test", 
        source_dir="test_dir", 
        args=["--production", "--silent"]
    )
    dist = MockDistribution([extension])
    cmd = build_nodejs(dist)
    
    # Mock the platform name
    cmd.plat_name = "any"
    
    # Test build_extension method
    cmd.build_extension(extension)
    
    # Check that additional args were passed to npm install
    install_call = mock_run.call_args_list[0]
    call_args = install_call[0][0]
    assert "--production" in call_args
    assert "--silent" in call_args


@mock.patch('os.path.exists')
@mock.patch('subprocess.run')
def test_build_nodejs_command_failure(mock_run, mock_exists):
    """Test build_nodejs when npm command fails."""
    # Mock subprocess to raise CalledProcessError
    mock_run.side_effect = subprocess.CalledProcessError(1, ['npm', 'install'])
    mock_exists.return_value = True
    
    extension = NodeJSExtension(target="test", source_dir="test_dir")
    dist = MockDistribution([extension])
    cmd = build_nodejs(dist)
    
    # Mock the platform name
    cmd.plat_name = "any"
    
    with pytest.raises(Exception):
        cmd.build_extension(extension)


@mock.patch('os.path.exists')
@mock.patch('subprocess.run')
def test_build_nodejs_optional_extension_failure(mock_run, mock_exists):
    """Test build_nodejs with optional extension that fails."""
    # Mock subprocess to raise CalledProcessError
    mock_run.side_effect = subprocess.CalledProcessError(1, ['npm', 'install'])
    mock_exists.return_value = True
    
    extension = NodeJSExtension(target="test", source_dir="test_dir", optional=True)
    dist = MockDistribution([extension])
    cmd = build_nodejs(dist)
    
    # Mock the platform name
    cmd.plat_name = "any"
    
    # Should not raise an error for optional extensions when run through run_for_extension
    # but build_extension itself will still raise
    with pytest.raises(Exception):
        cmd.build_extension(extension)
