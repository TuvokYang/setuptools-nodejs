from __future__ import annotations

import os
import json
from pathlib import Path
from setuptools.errors import SetupError
from setuptools.extension import Extension
from typing import (
    Dict,
    List,
    Optional,
    Sequence,
    TYPE_CHECKING,
    Union,
)

if TYPE_CHECKING:
    from semantic_version import SimpleSpec

from ._utils import Env


class NodeJSExtension(Extension):
    """Used to define a Node.js extension and its build configuration.

    Args:
        target: The name of the extension.
        source_dir: Path to the frontend source directory containing package.json.
        artifacts_dir: Directory where build artifacts are output (relative to source_dir).
        output_dir: Directory where artifacts will be copied in the Python package (relative to project root).
        exclude_dirs: List of directories to exclude from source_dir in sdist packages.
            Defaults to ["node_modules"].
        args: A list of extra arguments to be passed to npm. For example,
            ``args=["--production"]`` will install only production dependencies.
        node_version: Minimum Node.js version required for this extension.
        npm_version: Minimum npm version required for this extension.
        quiet: Suppress npm's output.
        optional: If it is true, a build failure in the extension will not
            abort the build process, and instead simply not install the failing
            extension.
        env: Environment variables to use when calling npm or node (``env=``
            in ``subprocess.Popen``). setuptools-nodejs may add additional
            variables or modify ``PATH``.
    """

    def __init__(
        self,
        target: Union[str, Dict[str, str]],
        source_dir: str = ".",
        artifacts_dir: Optional[str] = None,
        output_dir: Optional[str] = None,
        exclude_dirs: Optional[List[str]] = None,
        args: Optional[Sequence[str]] = (),
        node_version: Optional[str] = None,
        npm_version: Optional[str] = None,
        quiet: bool = False,
        optional: bool = False,
        env: Optional[Dict[str, str]] = None,
    ):
        if isinstance(target, dict):
            name = "; ".join("%s=%s" % (key, val) for key, val in target.items())
        else:
            name = target
            target = {"": target}

        # Call parent Extension constructor with dummy sources
        super().__init__(name=name, sources=[])
        
        self.name = name
        self.target = target
        self.source_dir = source_dir  # keep as provided, will be resolved at build time
        self.artifacts_dir = artifacts_dir or self._detect_artifacts_dir()
        self.package_artifacts_dir = output_dir or "frontend"  # use output_dir if provided, otherwise default to "frontend"
        
        # Initialize exclude_dirs with defaults and add artifacts_dir and package_artifacts_dir
        self.exclude_dirs = exclude_dirs or ["node_modules"]  # default to exclude node_modules
        
        # Add artifacts_dir to exclude_dirs if not already present
        if self.artifacts_dir and self.artifacts_dir not in self.exclude_dirs:
            self.exclude_dirs.append(self.artifacts_dir)
        
        # Add package_artifacts_dir to exclude_dirs if not already present
        if self.package_artifacts_dir and self.package_artifacts_dir not in self.exclude_dirs:
            self.exclude_dirs.append(self.package_artifacts_dir)
        
        self.args = tuple(args or ())
        self.node_version = node_version
        self.npm_version = npm_version
        self.quiet = quiet
        self.optional = optional
        self.env = Env(env)

    def get_node_version(self) -> Optional[SimpleSpec]:  # type: ignore[no-any-unimported]
        if self.node_version is None:
            return None
        try:
            from semantic_version import SimpleSpec

            return SimpleSpec(self.node_version)
        except ValueError:
            raise SetupError(
                "Can not parse Node.js version: %s", self.node_version
            )

    def should_exclude_file(self, file_path: Path) -> bool:
        """
        Check if a file should be excluded from source files.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if the file should be excluded, False otherwise
        """
        # Always exclude node_modules
        if "node_modules" in file_path.parts:
            return True
        
        # Check exclude_dirs
        source_path = Path(self.source_dir)
        for exclude_dir in self.exclude_dirs:
            exclude_path = source_path / exclude_dir
            try:
                file_path.relative_to(exclude_path)
                return True  # File is under exclude_dir
            except ValueError:
                # File is not under exclude_dir
                continue
        
        return False

    def get_source_files(self) -> List[str]:
        """
        Get all source files from the source directory, excluding specified directories.
        
        Returns:
            List of file paths relative to project root
        """
        source_path = Path(self.source_dir)
        files = []
        
        if source_path.exists():
            for file_path in source_path.rglob('*'):
                if file_path.is_file() and not self.should_exclude_file(file_path):
                    files.append(str(file_path))
        
        return files

    def get_npm_version(self) -> Optional[SimpleSpec]:  # type: ignore[no-any-unimported]
        if self.npm_version is None:
            return None
        try:
            from semantic_version import SimpleSpec

            return SimpleSpec(self.npm_version)
        except ValueError:
            raise SetupError(
                "Can not parse npm version: %s", self.npm_version
            )

    def get_artifact_path(self) -> str:
        """Get the full path to the artifacts directory."""
        if os.path.isabs(self.artifacts_dir):
            return self.artifacts_dir
        else:
            return os.path.join(self.source_dir, self.artifacts_dir)

    def _detect_artifacts_dir(self) -> str:
        """Automatically detect the artifacts directory from project configuration."""
        source_path = self.source_dir
        
        # Check Vue.js configuration
        vue_config = self._detect_vue_config(source_path)
        if vue_config:
            return vue_config
        
        # Check Angular configuration
        angular_config = self._detect_angular_config(source_path)
        if angular_config:
            return angular_config
        
        # Check React configuration
        react_config = self._detect_react_config(source_path)
        if react_config:
            return react_config
        
        # Default to "dist"
        return "dist"

    def _detect_vue_config(self, source_path: str) -> Optional[str]:
        """Detect Vue.js build output directory."""
        # Check vite.config.*
        for ext in ['.ts', '.js']:
            vite_config_path = os.path.join(source_path, f'vite.config{ext}')
            if os.path.exists(vite_config_path):
                # For simplicity, assume default Vite output directory
                return "dist"
        
        # Check vue.config.js
        vue_config_path = os.path.join(source_path, 'vue.config.js')
        if os.path.exists(vue_config_path):
            # For simplicity, assume default Vue CLI output directory
            return "dist"
        
        return None

    def _detect_angular_config(self, source_path: str) -> Optional[str]:
        """Detect Angular build output directory."""
        angular_json_path = os.path.join(source_path, 'angular.json')
        if os.path.exists(angular_json_path):
            try:
                with open(angular_json_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Extract output path from angular.json
                projects = config.get('projects', {})
                for project_name, project_config in projects.items():
                    build_config = project_config.get('architect', {}).get('build', {})
                    options = build_config.get('options', {})
                    output_path = options.get('outputPath')
                    if output_path:
                        return output_path
            except (json.JSONDecodeError, KeyError, IOError):
                pass
        
        return None

    def _detect_react_config(self, source_path: str) -> Optional[str]:
        """Detect React build output directory."""
        package_json_path = os.path.join(source_path, 'package.json')
        if os.path.exists(package_json_path):
            try:
                with open(package_json_path, 'r', encoding='utf-8') as f:
                    package_config = json.load(f)
                
                # Check build script for output directory hints
                scripts = package_config.get('scripts', {})
                build_script = scripts.get('build', '')
                if 'build' in build_script:
                    # For simplicity, assume default Create React App output directory
                    return "build"
            except (json.JSONDecodeError, KeyError, IOError):
                pass
        
        return None
