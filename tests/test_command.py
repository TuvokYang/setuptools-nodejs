"""
Tests for command.py module.
Functional tests for NodeJSCommand abstract base class.
"""

import logging
from unittest import mock

import pytest
from setuptools.dist import Distribution
from setuptools_nodejs.command import NodeJSCommand
from setuptools_nodejs.extension import NodeJSExtension


# ============================================================================
# Mock classes for testing
# ============================================================================

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


class ConcreteNodeJSCommand(NodeJSCommand):
    """Concrete implementation for testing abstract methods."""
    
    def run_for_extension(self, extension):
        """Simple implementation that tracks calls."""
        if hasattr(self, 'call_log'):
            self.call_log.append(extension.name)
        else:
            self.call_log = [extension.name]


# ============================================================================
# Command initialization tests
# ============================================================================

def test_nodejs_command_initialization():
    """Test basic command initialization."""
    dist = MockDistribution()
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    
    assert cmd.extensions == []
    assert hasattr(cmd, 'shell_enable')
    # shell_enable should be True on Windows, False otherwise
    import os
    expected_shell = os.name == "nt"
    assert cmd.shell_enable == expected_shell


def test_nodejs_command_get_command_name():
    """Test get_command_name method."""
    dist = MockDistribution()
    cmd = ConcreteNodeJSCommand(dist)
    
    # The command name should be derived from the class name
    name = cmd.get_command_name()
    assert "concretenodejscommand" in name.lower()


# ============================================================================
# finalize_options tests
# ============================================================================

def test_finalize_options_with_valid_extensions():
    """Test finalize_options with valid NodeJSExtension list."""
    extensions = [
        NodeJSExtension(target="frontend", source_dir="frontend"),
        NodeJSExtension(target="backend", source_dir="backend"),
    ]
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    assert cmd.extensions == extensions
    assert len(cmd.extensions) == 2


def test_finalize_options_with_no_extensions():
    """Test finalize_options when distribution has no extensions."""
    dist = MockDistribution()  # nodejs_extensions is empty list by default
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    assert cmd.extensions == []


def test_finalize_options_with_none_extensions():
    """Test finalize_options when distribution has None for extensions."""
    dist = MockDistribution()
    dist.nodejs_extensions = None  # Simulate setup.py without nodejs_extensions
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    # Should handle None gracefully
    assert cmd.extensions == []


def test_finalize_options_with_invalid_type():
    """Test finalize_options with non-list extensions."""
    dist = MockDistribution()
    dist.nodejs_extensions = "not a list"  # Wrong type
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    
    with pytest.raises(ValueError) as exc_info:
        cmd.finalize_options()
    
    assert "expected list of NodeJSExtension objects" in str(exc_info.value)


def test_finalize_options_with_invalid_extension_object():
    """Test finalize_options with list containing non-NodeJSExtension objects."""
    dist = MockDistribution()
    dist.nodejs_extensions = ["string", 123, NodeJSExtension(target="valid")]
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    
    with pytest.raises(ValueError) as exc_info:
        cmd.finalize_options()
    
    assert "expected NodeJSExtension object" in str(exc_info.value)
    assert "position 0" in str(exc_info.value)  # Should indicate position


# ============================================================================
# run method tests
# ============================================================================

def test_run_with_no_extensions():
    """Test run method when no extensions are defined."""
    dist = MockDistribution([])
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    # Mock the module logger instead of instance logger
    with mock.patch('setuptools_nodejs.command.logger') as mock_logger:
        cmd.run()
        
        # Should log that no extensions are defined
        mock_logger.info.assert_called()
        call_args = mock_logger.info.call_args[0][0]
        assert "no nodejs_extensions defined" in call_args


def test_run_with_extensions_all_success():
    """Test run method with all extensions succeeding."""
    extensions = [
        NodeJSExtension(target="ext1", source_dir="dir1"),
        NodeJSExtension(target="ext2", source_dir="dir2"),
    ]
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    cmd.run()
    
    # Both extensions should have been processed
    assert hasattr(cmd, 'call_log')
    assert cmd.call_log == ["ext1", "ext2"]


def test_run_with_optional_extension_failure():
    """Test run method with optional extension failing."""
    extensions = [
        NodeJSExtension(target="ext1", source_dir="dir1", optional=True),
    ]
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    # Make run_for_extension raise an exception
    def failing_run(extension):
        raise RuntimeError("Extension failed")
    
    cmd.run_for_extension = failing_run
    
    # Mock the module logger instead of instance logger
    with mock.patch('setuptools_nodejs.command.logger') as mock_logger:
        cmd.run()
        
        # Should log warning but not raise exception
        mock_logger.warning.assert_called()
        warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
        assert any("optional Node.js extension" in str(call) for call in warning_calls)


def test_run_with_non_optional_extension_failure():
    """Test run method with non-optional extension failing."""
    extensions = [
        NodeJSExtension(target="ext1", source_dir="dir1", optional=False),
    ]
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    # Make run_for_extension raise an exception
    def failing_run(extension):
        raise RuntimeError("Extension failed")
    
    cmd.run_for_extension = failing_run
    
    # Non-optional extension failure should raise exception
    with pytest.raises(RuntimeError, match="Extension failed"):
        cmd.run()


def test_run_environment_selection():
    """Test environment variable selection logic."""
    # Create extensions with different environment configurations
    extensions = [
        NodeJSExtension(
            target="optional_with_env",
            source_dir="dir1",
            optional=True,
            env={"VAR1": "value1"}
        ),
        NodeJSExtension(
            target="non_optional_with_env",
            source_dir="dir2",
            optional=False,
            env={"VAR2": "value2"}
        ),
        NodeJSExtension(
            target="optional_no_env",
            source_dir="dir3",
            optional=True,
            env=None
        ),
    ]
    
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    # Track which extensions were called and with what environment
    call_records = []
    
    def tracking_run(extension):
        call_records.append({
            'name': extension.name,
            'env': extension.env
        })
    
    cmd.run_for_extension = tracking_run
    cmd.run()
    
    # All extensions should have been called
    assert len(call_records) == 3
    
    # The run method doesn't modify env, just selects one for the command
    # The actual env selection happens in the run method but isn't passed to run_for_extension
    # This test verifies the extensions are processed in order


def test_run_mixed_optional_extensions():
    """Test run method with mix of optional and non-optional extensions."""
    extensions = [
        NodeJSExtension(target="opt1", source_dir="dir1", optional=True),
        NodeJSExtension(target="nonopt1", source_dir="dir2", optional=False),
        NodeJSExtension(target="opt2", source_dir="dir3", optional=True),
    ]
    
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    call_log = []
    
    def tracking_run(extension):
        call_log.append(extension.name)
        if extension.name == "nonopt1":
            raise RuntimeError("Non-optional failed")
    
    cmd.run_for_extension = tracking_run
    
    # Non-optional extension failure should stop execution
    with pytest.raises(RuntimeError, match="Non-optional failed"):
        cmd.run()
    
    # Only the first optional and the non-optional should have been called
    assert call_log == ["opt1", "nonopt1"]


# ============================================================================
# Platform-specific tests
# ============================================================================

def test_shell_enable_windows():
    """Test shell_enable on Windows platform."""
    with mock.patch('os.name', 'nt'):  # Windows
        dist = MockDistribution()
        cmd = ConcreteNodeJSCommand(dist)
        cmd.initialize_options()
        
        assert cmd.shell_enable is True


def test_shell_enable_unix():
    """Test shell_enable on Unix-like platforms."""
    with mock.patch('os.name', 'posix'):  # Unix-like
        dist = MockDistribution()
        cmd = ConcreteNodeJSCommand(dist)
        cmd.initialize_options()
        
        assert cmd.shell_enable is False


# ============================================================================
# Error handling and edge cases
# ============================================================================

def test_command_with_missing_distribution_attribute():
    """Test command when distribution is missing expected attributes."""
    # Create a minimal distribution that inherits from Distribution
    class MinimalDistribution(Distribution):
        pass
    
    dist = MinimalDistribution()
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    
    # Should handle missing attribute gracefully
    cmd.finalize_options()
    assert cmd.extensions == []


def test_run_for_extension_abstract_method():
    """Test that NodeJSCommand cannot be instantiated directly."""
    dist = MockDistribution()
    
    # Can't instantiate abstract class
    with pytest.raises(TypeError):
        NodeJSCommand(dist)


def test_logger_initialization():
    """Test that logger is properly initialized."""
    dist = MockDistribution()
    cmd = ConcreteNodeJSCommand(dist)
    
    # The command doesn't have its own logger attribute
    # It uses the module-level logger
    # Check that the module logger exists and has correct name
    import setuptools_nodejs.command
    assert hasattr(setuptools_nodejs.command, 'logger')
    assert isinstance(setuptools_nodejs.command.logger, logging.Logger)
    assert setuptools_nodejs.command.logger.name == 'setuptools_nodejs.command'


# ============================================================================
# Integration tests with real extensions
# ============================================================================

def test_integration_with_real_extension_objects():
    """Test command with real NodeJSExtension objects."""
    extensions = [
        NodeJSExtension(
            target="frontend",
            source_dir="frontend",
            artifacts_dir="dist",
            args=["--production"],
            quiet=True,
            optional=False
        ),
        NodeJSExtension(
            target={"api": "myapp.api", "ui": "myapp.ui"},
            source_dir=".",
            artifacts_dir="build",
            node_version=">=18.0.0",
            npm_version=">=9.0.0",
            optional=True
        ),
    ]
    
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    cmd.initialize_options()
    cmd.finalize_options()
    
    assert len(cmd.extensions) == 2
    assert cmd.extensions[0].name == "frontend"
    assert cmd.extensions[1].name == "api=myapp.api; ui=myapp.ui"
    
    # Verify extensions have correct properties
    assert cmd.extensions[0].quiet is True
    assert cmd.extensions[0].optional is False
    assert cmd.extensions[1].optional is True


def test_command_lifecycle_integration():
    """Test complete command lifecycle."""
    extensions = [
        NodeJSExtension(target="test1", source_dir="dir1"),
        NodeJSExtension(target="test2", source_dir="dir2", optional=True),
    ]
    
    dist = MockDistribution(extensions)
    cmd = ConcreteNodeJSCommand(dist)
    
    # Step 1: initialize_options
    cmd.initialize_options()
    assert cmd.extensions == []
    
    # Step 2: finalize_options
    cmd.finalize_options()
    assert cmd.extensions == extensions
    
    # Step 3: run
    processed = []
    
    def track_run(ext):
        processed.append(ext.name)
    
    cmd.run_for_extension = track_run
    cmd.run()
    
    assert processed == ["test1", "test2"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
