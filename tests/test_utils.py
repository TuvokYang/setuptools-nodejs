"""
Tests for _utils.py module.
Functional tests based on the documented behavior of utility functions.
"""

import subprocess
from unittest import mock

import pytest
from setuptools_nodejs._utils import (
    Env,
    run_subprocess,
    check_subprocess_output,
    format_called_process_error,
    _quote_whitespace,
)


# ============================================================================
# Env class tests
# ============================================================================

def test_env_class_hash_with_env():
    """Test Env hash calculation with environment variables."""
    env_dict = {"PATH": "/usr/bin", "HOME": "/home/user"}
    env1 = Env(env_dict)
    env2 = Env(env_dict.copy())
    
    # Same dictionary should produce same hash
    assert hash(env1) == hash(env2)
    assert env1 == env2


def test_env_class_hash_without_env():
    """Test Env hash calculation without environment variables."""
    env1 = Env(None)
    env2 = Env(None)
    
    assert hash(env1) == hash(env2)
    assert env1 == env2


def test_env_class_hash_different_envs():
    """Test Env hash calculation with different environment variables."""
    env1 = Env({"PATH": "/usr/bin"})
    env2 = Env({"HOME": "/home/user"})
    
    # Different dictionaries should produce different hashes
    assert hash(env1) != hash(env2)
    assert env1 != env2


def test_env_class_equality_with_other_types():
    """Test Env equality comparison with non-Env objects."""
    env = Env({"PATH": "/usr/bin"})
    
    # Should not be equal to other types
    assert env != {"PATH": "/usr/bin"}
    assert env != "string"
    assert env != None


# ============================================================================
# run_subprocess function tests
# ============================================================================

def test_run_subprocess_success():
    """Test run_subprocess with successful command execution."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['echo', 'test'],
            returncode=0,
            stdout='test output',
            stderr=''
        )
        
        result = run_subprocess(['echo', 'test'], env=None)
        
        mock_run.assert_called_once()
        assert result.returncode == 0
        assert result.stdout == 'test output'


def test_run_subprocess_with_env_dict():
    """Test run_subprocess with environment dictionary."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['echo', 'test'],
            returncode=0
        )
        
        env_dict = {"CUSTOM_VAR": "value"}
        run_subprocess(['echo', 'test'], env=env_dict)
        
        # Check that env was passed correctly
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['env'] == env_dict


def test_run_subprocess_with_env_object():
    """Test run_subprocess with Env object."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['echo', 'test'],
            returncode=0
        )
        
        env_obj = Env({"CUSTOM_VAR": "value"})
        run_subprocess(['echo', 'test'], env=env_obj)
        
        # Check that env was extracted from Env object
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['env'] == {"CUSTOM_VAR": "value"}


def test_run_subprocess_with_additional_kwargs():
    """Test run_subprocess with additional subprocess.run kwargs."""
    with mock.patch('subprocess.run') as mock_run:
        mock_run.return_value = subprocess.CompletedProcess(
            args=['echo', 'test'],
            returncode=0
        )
        
        run_subprocess(['echo', 'test'], env=None, cwd='/tmp', timeout=30)
        
        call_kwargs = mock_run.call_args[1]
        assert call_kwargs['cwd'] == '/tmp'
        assert call_kwargs['timeout'] == 30


# ============================================================================
# check_subprocess_output function tests
# ============================================================================

def test_check_subprocess_output_success():
    """Test check_subprocess_output with successful command."""
    with mock.patch('subprocess.check_output') as mock_check_output:
        mock_check_output.return_value = b'test output'
        
        result = check_subprocess_output(['echo', 'test'], env=None)
        
        mock_check_output.assert_called_once()
        # check_subprocess_output returns bytes (cast to str is just type hint)
        assert result == b'test output'


def test_check_subprocess_output_failure():
    """Test check_subprocess_output with failing command."""
    with mock.patch('subprocess.check_output') as mock_check_output:
        mock_check_output.side_effect = subprocess.CalledProcessError(
            returncode=1,
            cmd=['echo', 'test'],
            output=b'error output'
        )
        
        with pytest.raises(subprocess.CalledProcessError) as exc_info:
            check_subprocess_output(['echo', 'test'], env=None)
        
        assert exc_info.value.returncode == 1
        assert exc_info.value.output == b'error output'


def test_check_subprocess_output_with_env_conversion():
    """Test check_subprocess_output converts Env object to dict."""
    with mock.patch('subprocess.check_output') as mock_check_output:
        mock_check_output.return_value = b'output'
        
        env_obj = Env({"VAR": "value"})
        check_subprocess_output(['echo', 'test'], env=env_obj)
        
        call_kwargs = mock_check_output.call_args[1]
        assert call_kwargs['env'] == {"VAR": "value"}


# ============================================================================
# format_called_process_error function tests
# ============================================================================

def test_format_called_process_error_basic():
    """Test basic error formatting without stdout/stderr."""
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=['ls', '-la'],
        output=None,
        stderr=None
    )
    
    result = format_called_process_error(error)
    assert "`ls -la` failed with code 1" in result
    assert "stdout" not in result
    assert "stderr" not in result


def test_format_called_process_error_with_stdout():
    """Test error formatting with stdout."""
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=['npm', 'run', 'build'],
        output='Build failed: missing dependency',
        stderr=None
    )
    
    result = format_called_process_error(error)
    # Note: _quote_whitespace only adds quotes for strings with spaces
    # 'run' doesn't have spaces, so no quotes
    assert "`npm run build` failed with code 1" in result
    assert "Output captured from stdout" in result
    assert "Build failed: missing dependency" in result


def test_format_called_process_error_with_stderr():
    """Test error formatting with stderr."""
    error = subprocess.CalledProcessError(
        returncode=-1,
        cmd=['npm'],
        output=None,
        stderr='Permission denied'
    )
    
    result = format_called_process_error(error)
    assert "`npm` failed with code -1" in result
    assert "Output captured from stderr" in result
    assert "Permission denied" in result


def test_format_called_process_error_with_both_outputs():
    """Test error formatting with both stdout and stderr."""
    error = subprocess.CalledProcessError(
        returncode=2,
        cmd=['python', 'script.py'],
        output='Script started',
        stderr='RuntimeError: Something went wrong'
    )
    
    result = format_called_process_error(error)
    assert "`python script.py` failed with code 2" in result
    assert "Output captured from stdout" in result
    assert "Script started" in result
    assert "Output captured from stderr" in result
    assert "RuntimeError: Something went wrong" in result


def test_format_called_process_error_exclude_stdout():
    """Test error formatting excluding stdout."""
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=['npm', 'run', 'build'],
        output='Build output',
        stderr=None
    )
    
    result = format_called_process_error(error, include_stdout=False)
    assert "`npm run build` failed with code 1" in result
    assert "Output captured from stdout" not in result
    assert "Build output" not in result


def test_format_called_process_error_exclude_stderr():
    """Test error formatting excluding stderr."""
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=['npm', 'run', 'build'],
        output=None,
        stderr='Error details'
    )
    
    result = format_called_process_error(error, include_stderr=False)
    assert "`npm run build` failed with code 1" in result
    assert "Output captured from stderr" not in result
    assert "Error details" not in result


def test_format_called_process_error_empty_strings():
    """Test error formatting with empty stdout/stderr strings."""
    error = subprocess.CalledProcessError(
        returncode=1,
        cmd=['echo', 'test'],
        output='',
        stderr=''
    )
    
    result = format_called_process_error(error)
    assert "`echo test` failed with code 1" in result
    # Empty strings should still be included
    assert "Output captured from stdout" in result
    assert "Output captured from stderr" in result


# ============================================================================
# _quote_whitespace function tests
# ============================================================================

def test_quote_whitespace_with_spaces():
    """Test _quote_whitespace with string containing spaces."""
    result = _quote_whitespace("hello world")
    assert result == "'hello world'"


def test_quote_whitespace_without_spaces():
    """Test _quote_whitespace with string without spaces."""
    result = _quote_whitespace("hello")
    assert result == "hello"


def test_quote_whitespace_empty_string():
    """Test _quote_whitespace with empty string."""
    result = _quote_whitespace("")
    assert result == ""


def test_quote_whitespace_multiple_spaces():
    """Test _quote_whitespace with multiple consecutive spaces."""
    result = _quote_whitespace("hello  world")
    assert result == "'hello  world'"


def test_quote_whitespace_tab_character():
    """Test _quote_whitespace with tab character (not a space)."""
    result = _quote_whitespace("hello\tworld")
    assert result == "hello\tworld"  # Tab is not a space, so no quotes


def test_quote_whitespace_newline_character():
    """Test _quote_whitespace with newline character (not a space)."""
    result = _quote_whitespace("hello\nworld")
    assert result == "hello\nworld"  # Newline is not a space, so no quotes


# ============================================================================
# Integration tests
# ============================================================================

def test_env_with_lru_cache():
    """Test Env class compatibility with functools.lru_cache."""
    from functools import lru_cache
    
    @lru_cache(maxsize=2)
    def cached_function(env: Env) -> str:
        return "processed"
    
    env1 = Env({"VAR1": "value1"})
    env2 = Env({"VAR1": "value1"})  # Same content, different object
    env3 = Env({"VAR2": "value2"})  # Different content
    
    # First call should compute
    result1 = cached_function(env1)
    assert result1 == "processed"
    
    # Second call with same content should use cache
    result2 = cached_function(env2)
    assert result2 == "processed"
    
    # Different content should be new computation
    result3 = cached_function(env3)
    assert result3 == "processed"
    
    # Check cache info
    cache_info = cached_function.cache_info()
    assert cache_info.hits >= 1  # env2 should have been a hit
    assert cache_info.misses == 2  # env1 and env3 were misses


def test_real_subprocess_integration():
    """Test actual subprocess execution (simple command)."""
    # Skip on Windows if needed, or use cross-platform command
    import sys
    if sys.platform == "win32":
        command = ["cmd", "/c", "echo", "test"]
    else:
        command = ["echo", "test"]
    
    # This test actually runs a subprocess
    result = run_subprocess(command, env=None, capture_output=True, text=True)
    
    assert result.returncode == 0
    assert "test" in result.stdout or "test" in result.stderr


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
