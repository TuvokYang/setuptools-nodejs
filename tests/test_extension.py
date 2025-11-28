import os
from pathlib import Path

import pytest
from pytest import CaptureFixture, MonkeyPatch

from setuptools_nodejs.extension import NodeJSExtension

SETUPTOOLS_NODEJS_DIR = Path(__file__).parent.parent


@pytest.fixture()
def browser_extension() -> NodeJSExtension:
    return NodeJSExtension(
        target="browser",
        source_dir="browser",
        artifacts_dir="dist",
    )


@pytest.fixture()
def simple_extension() -> NodeJSExtension:
    return NodeJSExtension(
        target="simple",
        source_dir=".",
        artifacts_dir="build",
    )


def test_nodejs_extension_creation(browser_extension: NodeJSExtension) -> None:
    """Test basic NodeJSExtension creation and properties."""
    assert browser_extension.name == "browser"
    assert browser_extension.target == {"": "browser"}
    assert browser_extension.source_dir == "browser"
    assert browser_extension.artifacts_dir == "dist"
    assert browser_extension.args == ()
    assert browser_extension.quiet is False
    assert browser_extension.optional is False


def test_nodejs_extension_with_args() -> None:
    """Test NodeJSExtension with additional arguments."""
    extension = NodeJSExtension(
        target="test",
        source_dir="frontend",
        artifacts_dir="output",
        args=["--production", "--silent"],
        quiet=True,
        optional=True,
    )
    
    assert extension.name == "test"
    assert extension.source_dir == "frontend"
    assert extension.artifacts_dir == "output"
    assert extension.args == ("--production", "--silent")
    assert extension.quiet is True
    assert extension.optional is True


def test_nodejs_extension_artifact_path(browser_extension: NodeJSExtension) -> None:
    """Test artifact path generation."""
    # Use os.path.join to handle platform-specific path separators
    expected_path = os.path.join("browser", "dist")
    assert browser_extension.get_artifact_path() == expected_path


def test_nodejs_extension_dict_target() -> None:
    """Test NodeJSExtension with dictionary target."""
    extension = NodeJSExtension(
        target={"frontend": "myapp.frontend", "backend": "myapp.backend"},
        source_dir="src",
        artifacts_dir="dist",
    )
    
    assert extension.name == "frontend=myapp.frontend; backend=myapp.backend"
    assert extension.target == {"frontend": "myapp.frontend", "backend": "myapp.backend"}
    assert extension.source_dir == "src"
    assert extension.artifacts_dir == "dist"


def test_nodejs_extension_node_version() -> None:
    """Test Node.js version parsing."""
    extension = NodeJSExtension(
        target="test",
        node_version=">=18.0.0",
    )
    
    spec = extension.get_node_version()
    assert spec is not None
    assert str(spec) == ">=18.0.0"


def test_nodejs_extension_npm_version() -> None:
    """Test npm version parsing."""
    extension = NodeJSExtension(
        target="test",
        npm_version=">=9.0.0",
    )
    
    spec = extension.get_npm_version()
    assert spec is not None
    assert str(spec) == ">=9.0.0"


def test_nodejs_extension_no_versions() -> None:
    """Test NodeJSExtension without version constraints."""
    extension = NodeJSExtension(target="test")
    
    assert extension.get_node_version() is None
    assert extension.get_npm_version() is None
