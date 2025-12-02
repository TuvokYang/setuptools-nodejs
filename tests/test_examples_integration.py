"""
Integration tests for example projects.
Tests that example projects can be built with local setuptools-nodejs
and that tar.gz contains all source files.
"""

import os
import sys
import tempfile
import shutil
import subprocess
import tarfile
import zipfile
import fnmatch
import re
from pathlib import Path
from typing import List, Set
import pytest


# TOML loading setup (as provided by user)
if sys.version_info[:2] >= (3, 11):
    from tomllib import load as toml_load
else:
    try:
        from tomli import load as toml_load
    except ImportError:
        from setuptools.extern.tomli import load as toml_load

# For writing TOML
try:
    from tomli_w import dump as toml_dump
except ImportError:
    toml_dump = None


def get_local_package_path(package_name: str) -> str:
    """
    Get local package path using 'pip show'.
    
    Args:
        package_name: Name of the package
        
    Returns:
        Local path to the package
    """
    try:
        result = subprocess.run(
            ["pip", "show", package_name],
            capture_output=True,
            text=True,
            check=True
        )
        
        # Parse output to find Editable project location
        for line in result.stdout.splitlines():
            if line.startswith("Editable project location:"):
                path = line.split(":", 1)[1].strip()
                return path
        
        # If not editable, try to find Location (for regular installs)
        for line in result.stdout.splitlines():
            if line.startswith("Location:"):
                path = line.split(":", 1)[1].strip()
                return path
                
        # Fallback: use current directory if package is setuptools-nodejs
        if package_name == "setuptools-nodejs":
            # Try to find the package in the current project
            project_root = Path(__file__).parent.parent
            if (project_root / "src" / "setuptools_nodejs").exists():
                return str(project_root)
        
        raise RuntimeError(f"Could not find location for {package_name}")
    except subprocess.CalledProcessError as e:
        # Fallback for CI environment
        if package_name == "setuptools-nodejs":
            project_root = Path(__file__).parent.parent
            if (project_root / "src" / "setuptools_nodejs").exists():
                return str(project_root)
        raise RuntimeError(f"Failed to get package info for {package_name}: {e}")


def discover_example_projects() -> List[Path]:
    """
    Discover all example projects in examples/ directory.
    
    Returns:
        List of paths to example project directories
    """
    # Get the directory containing this test file
    test_dir = Path(__file__).parent
    # Go up to project root, then find examples directory
    project_root = test_dir.parent
    examples_dir = project_root / "examples"
    
    if not examples_dir.exists():
        return []
    
    projects = []
    for item in examples_dir.iterdir():
        if item.is_dir() and (item / "pyproject.toml").exists():
            projects.append(item)
    
    return projects


def get_source_files(project_dir: Path) -> List[Path]:
    """
    Get all source files in project directory.
    
    Args:
        project_dir: Path to project directory
        
    Returns:
        List of relative paths to source files
    """
    source_files = []
    exclude_patterns = [
        "node_modules",
        "dist",
        ".git",
        "__pycache__",
        "*.pyc",
        "*.egg-info",
        "build",
        ".pytest_cache",
        "*.whl",
        "*.tar.gz",
        "*.egg",
        ".DS_Store",
        "Thumbs.db"
    ]
    
    for root, dirs, files in os.walk(project_dir):
        # Exclude directories matching patterns
        dirs[:] = [d for d in dirs if not any(
            fnmatch.fnmatch(d, pat) for pat in exclude_patterns
        )]
        
        for file in files:
            filepath = Path(root) / file
            rel_path = filepath.relative_to(project_dir)
            
            # Check if file should be excluded
            exclude = False
            for pattern in exclude_patterns:
                if fnmatch.fnmatch(str(rel_path), pattern):
                    exclude = True
                    break
            
            if not exclude:
                source_files.append(rel_path)
    
    return source_files


def modify_pyproject_with_local_path(pyproject_path: Path, local_package_path: str) -> None:
    """
    Modify pyproject.toml to use local setuptools-nodejs package.
    
    Args:
        pyproject_path: Path to pyproject.toml file
        local_package_path: Local path to setuptools-nodejs package
    """
    # Read the entire file content
    with open(pyproject_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Convert Windows path to file:// URL format
    local_path = local_package_path.replace('\\', '/')
    new_req = f'setuptools-nodejs @ file://{local_path}'
    
    # Replace setuptools-nodejs with local path
    # Handle both "setuptools-nodejs" and "setuptools-nodejs" with quotes
    import re
    
    # Pattern to match setuptools-nodejs in requires list
    # Matches: "setuptools-nodejs" or 'setuptools-nodejs'
    pattern = r'("setuptools-nodejs"|\'setuptools-nodejs\')'
    
    # Replace with new requirement
    new_content = re.sub(pattern, f'"{new_req}"', content)
    
    # Write back to file
    with open(pyproject_path, 'w', encoding='utf-8') as f:
        f.write(new_content)


def verify_tar_gz_contains_files(tar_gz_path: Path, expected_files: List[Path]) -> List[Path]:
    """
    Verify that tar.gz contains all expected files.
    
    Args:
        tar_gz_path: Path to tar.gz file
        expected_files: List of expected relative file paths
        
    Returns:
        List of missing files
    """
    missing_files = []
    
    with tarfile.open(tar_gz_path, "r:gz") as tar:
        # Get all files in tar archive
        tar_files = {Path(name) for name in tar.getnames()}
        
        # Check each expected file
        for expected_file in expected_files:
            # Convert expected file to string for comparison
            expected_str = str(expected_file).replace('\\', '/')
            
            # Check if file exists in tar (with any prefix)
            found = False
            for tar_file in tar_files:
                tar_str = str(tar_file).replace('\\', '/')
                # Check if tar file ends with expected file path
                if tar_str.endswith(expected_str):
                    found = True
                    break
            
            if not found:
                missing_files.append(expected_file)
    
    return missing_files


def verify_whl_contents(whl_path: Path, project_dir: Path) -> None:
    """
    Verify that whl file contains artifacts and Python source code.
    
    Args:
        whl_path: Path to whl file
        project_dir: Path to project directory
    """
    with zipfile.ZipFile(whl_path, 'r') as whl:
        # Get all files in whl
        whl_files = set(whl.namelist())
        
        # Check for Python source files
        python_files = [f for f in whl_files if f.endswith('.py')]
        assert len(python_files) > 0, "No Python files found in whl"
        
        # Check for package directory - look for any directory containing .py files
        package_dirs = set()
        for file in whl_files:
            if file.endswith('.py'):
                # Extract directory name
                dir_part = file.split('/')[0] if '/' in file else ''
                if dir_part and dir_part not in package_dirs:
                    package_dirs.add(dir_part)
        
        assert len(package_dirs) > 0, f"No package directory found in whl. Files: {list(whl_files)[:10]}"
        
        # Check for artifacts if defined in pyproject.toml
        pyproject_path = project_dir / "pyproject.toml"
        if pyproject_path.exists():
            with open(pyproject_path, 'rb') as f:
                data = toml_load(f)
            
            # Check for setuptools-nodejs configuration
            if 'tool' in data and 'setuptools-nodejs' in data['tool']:
                config = data['tool']['setuptools-nodejs']
                if 'frontend-projects' in config:
                    for project in config['frontend-projects']:
                        if 'artifacts_dir' in project:
                            artifacts_dir = project['artifacts_dir']
                            # Look for artifacts in whl - check for frontend directory
                            artifact_files = [f for f in whl_files if 'frontend' in f]
                            assert len(artifact_files) > 0, f"No frontend artifacts found in whl"


@pytest.mark.parametrize("project_dir", discover_example_projects(), ids=lambda p: p.name)
def test_example_project_build(project_dir: Path):
    """
    Test that example project builds successfully with local package
    and that tar.gz contains all source files.
    """
    # Skip if no example projects found
    if not discover_example_projects():
        pytest.skip("No example projects found")
    
    # Get local package path
    local_path = get_local_package_path("setuptools-nodejs")
    
    # Create temporary directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        
        # Copy project to temporary directory
        tmp_project = tmpdir_path / project_dir.name
        shutil.copytree(project_dir, tmp_project)
        
        # Modify pyproject.toml to use local package
        pyproject_file = tmp_project / "pyproject.toml"
        modify_pyproject_with_local_path(pyproject_file, local_path)
        
        # Run build command with npm cache directory to avoid permission issues
        try:
            # Create npm cache directory in temp dir
            npm_cache_dir = tmpdir_path / '.npm_cache'
            npm_cache_dir.mkdir(exist_ok=True)
            
            # Set environment variables for npm
            env = os.environ.copy()
            env['npm_config_cache'] = str(npm_cache_dir)
            # Use npm registry mirror for faster downloads in CI
            env['npm_config_registry'] = 'https://registry.npmjs.org/'
            
            # Check if npm is available
            # On Windows, npm might be npm.cmd
            npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
            npm_available = shutil.which(npm_cmd) is not None
            
            if not npm_available:
                # Try the other variant
                npm_cmd = "npm" if os.name == "nt" else "npm.cmd"
                npm_available = shutil.which(npm_cmd) is not None
            
            if not npm_available:
                pytest.skip("npm not available, skipping test")
            
            # First, try to run npm install directly to see detailed errors
            browser_dir = tmp_project / "browser"
            if browser_dir.exists():
                # Run npm install with detailed output
                npm_result = subprocess.run(
                    [npm_cmd, "install"],
                    cwd=browser_dir,
                    capture_output=True,
                    text=True,
                    env=env
                )
                if npm_result.returncode != 0:
                    pytest.fail(
                        f"npm install failed for {project_dir.name}:\n"
                        f"npm STDOUT:\n{npm_result.stdout}\n"
                        f"npm STDERR:\n{npm_result.stderr}\n"
                        f"npm return code: {npm_result.returncode}"
                    )
            
            # Then run the build
            result = subprocess.run(
                ["python", "-m", "build", "--no-isolation"],
                cwd=tmp_project,
                capture_output=True,
                text=True,
                env=env
            )
            
            if result.returncode != 0:
                # Provide detailed error information
                error_msg = (
                    f"Build failed for {project_dir.name} (return code: {result.returncode}):\n"
                    f"STDOUT:\n{result.stdout}\n"
                    f"STDERR:\n{result.stderr}\n"
                    f"Environment: npm_cache={npm_cache_dir}, registry={env['npm_config_registry']}\n"
                )
                pytest.fail(error_msg)
                
        except subprocess.CalledProcessError as e:
            # Fallback for check=True case
            pytest.fail(
                f"Build failed for {project_dir.name}:\n"
                f"STDOUT:\n{e.stdout}\n"
                f"STDERR:\n{e.stderr}\n"
                f"Return code: {e.returncode}"
            )
        
        # Check dist directory exists
        dist_dir = tmp_project / "dist"
        assert dist_dir.exists() and dist_dir.is_dir(), f"dist directory not created for {project_dir.name}"
        
        # Get tar.gz and whl files
        tar_gz_files = list(dist_dir.glob("*.tar.gz"))
        whl_files = list(dist_dir.glob("*.whl"))
        
        assert len(tar_gz_files) > 0, f"No .tar.gz file created for {project_dir.name}"
        assert len(whl_files) > 0, f"No .whl file created for {project_dir.name}"
        
        # Get source files from project
        source_files = get_source_files(tmp_project)
        assert len(source_files) > 0, f"No source files found in {project_dir.name}"
        
        # Verify tar.gz contains all source files
        tar_gz_path = tar_gz_files[0]
        missing_files = verify_tar_gz_contains_files(tar_gz_path, source_files)
        
        assert len(missing_files) == 0, (
            f"Missing files in {tar_gz_path.name} for {project_dir.name}:\n"
            f"{chr(10).join(str(f) for f in missing_files)}"
        )
        
        # Verify whl contents
        whl_path = whl_files[0]
        verify_whl_contents(whl_path, tmp_project)


if __name__ == "__main__":
    # For manual testing
    projects = discover_example_projects()
    print(f"Found {len(projects)} example projects:")
    for project in projects:
        print(f"  - {project.name}")
