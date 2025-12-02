from __future__ import annotations

import os
import shutil
import subprocess
import sys
import logging
import warnings
from setuptools.errors import (
    CompileError,
    ExecError,
    FileError,
)
from typing import Dict, List, NamedTuple, Optional, cast

from setuptools import Distribution
from setuptools.command.build_ext import build_ext as CommandBuildExt

from ._utils import check_subprocess_output, format_called_process_error, Env
from .command import NodeJSCommand
from .extension import NodeJSExtension

logger = logging.getLogger(__name__)


try:
    from setuptools.command.bdist_wheel import bdist_wheel as CommandBdistWheel
except ImportError:  # old version of setuptools
    try:
        from wheel.bdist_wheel import bdist_wheel as CommandBdistWheel  # type: ignore[no-redef]
    except ImportError:
        from setuptools import Command as CommandBdistWheel  # type: ignore[assignment]


class build_nodejs(NodeJSCommand):
    """Command for building Node.js extensions via npm."""

    description = "build Node.js extensions (npm install/build to build directory)"

    user_options = [
        (
            "inplace",
            "i",
            "ignore build-lib and put compiled extensions into the source "
            + "directory alongside your pure Python modules",
        ),
        ("debug", "d", "Force debug to true for all Node.js extensions "),
        ("release", "r", "Force debug to false for all Node.js extensions "),
        ("qbuild", None, "Force enable quiet option for all Node.js extensions "),
        (
            "build-temp",
            "t",
            "directory for temporary files (cargo 'target' directory) ",
        ),
    ]
    boolean_options = ["inplace", "debug", "release", "qbuild"]

    inplace: bool = False
    debug: bool = False
    release: bool = False
    qbuild: bool = False

    plat_name: Optional[str] = None
    build_temp: Optional[str] = None

    def initialize_options(self) -> None:
        super().initialize_options()
        self.npm = os.getenv("NPM", "npm")

    def finalize_options(self) -> None:
        super().finalize_options()

        # Inherit settings from the `build` and `build_ext` commands
        self.set_undefined_options(
            "build",
            ("plat_name", "plat_name"),
        )

        # Inherit settings from the `build_ext` command
        self.set_undefined_options(
            "build_ext",
            ("build_temp", "build_temp"),
            ("debug", "debug"),
            ("inplace", "inplace"),
        )

        if self.build_temp is not None:
            warnings.warn(
                "`--build-temp` argument does nothing for Node.js extensions.",
                DeprecationWarning,
            )

    def run_for_extension(self, ext: NodeJSExtension) -> None:
        assert self.plat_name is not None

        artifacts = self.build_extension(ext)
        self.install_extension(ext, artifacts)

    def build_extension(
        self, ext: NodeJSExtension
    ) -> List["_BuiltArtifact"]:
        env = _prepare_build_environment(ext.env, ext)

        # Resolve source_dir relative to project root
        # In PEP 517 builds, the current working directory is the project root
        source_dir = os.path.abspath(ext.source_dir)
        
        if not os.path.exists(source_dir):
            raise FileError(
                f"can't find source directory for Node.js extension `{ext.name}` at path `{source_dir}` (resolved from `{ext.source_dir}`)"
            )

        package_json_path = os.path.join(source_dir, "package.json")
        if not os.path.exists(package_json_path):
            raise FileError(
                f"can't find package.json for Node.js extension `{ext.name}` at path `{package_json_path}`"
            )

        quiet = self.qbuild or ext.quiet

        # Step 1: npm install
        install_command = [
            self.npm,
            "install",
        ]
        if ext.args:
            install_command.extend(ext.args)

        if not quiet:
            logger.info(" ".join(install_command))
        # Execute npm install
        try:
            stderr = subprocess.PIPE if quiet else None
            # Use self.shell_enable from NodeJSCommand base class
            # shell=True is needed on Windows for npm (.cmd files)
            # shell=False on Unix-like systems to avoid argument parsing issues
            check_subprocess_output(
                install_command,
                env=env,
                stderr=stderr,
                text=True,
                encoding='utf-8',
                shell=self.shell_enable,
                cwd=source_dir,
            )
        except subprocess.CalledProcessError as e:
            # Don't include stdout in the formatted error as it is a huge dump
            # of npm output which aren't helpful for the end user.
            raise CompileError(format_called_process_error(e, include_stdout=False))

        except OSError:
            raise ExecError(
                "Unable to execute 'npm' - this package "
                "requires Node.js to be installed and npm to be on the PATH"
            )

        # Step 2: npm run build
        build_command = [
            self.npm,
            "run",
            "build",
        ]

        if not quiet:
            logger.info(" ".join(build_command))

        # Execute npm run build
        try:
            stderr = subprocess.PIPE if quiet else None
            # Use self.shell_enable from NodeJSCommand base class
            # shell=True is needed on Windows for npm (.cmd files)
            # shell=False on Unix-like systems to avoid argument parsing issues
            check_subprocess_output(
                build_command,
                env=env,
                stderr=stderr,
                text=True,
                encoding='utf-8',
                shell=self.shell_enable,
                cwd=source_dir,
            )
        except subprocess.CalledProcessError as e:
            # Don't include stdout in the formatted error as it is a huge dump
            # of npm output which aren't helpful for the end user.
            raise CompileError(format_called_process_error(e, include_stdout=False))

        except OSError:
            raise ExecError(
                "Unable to execute 'npm' - this package "
                "requires Node.js to be installed and npm to be on the PATH"
            )

        # Check if artifacts directory exists
        artifact_path = ext.get_artifact_path()
        if not os.path.exists(artifact_path):
            raise ExecError(
                f"Node.js build failed; unable to find build artifacts at `{artifact_path}`"
            )

        # Return the artifact path
        return [_BuiltArtifact(ext.name, artifact_path)]

    def install_extension(
        self, ext: NodeJSExtension, artifacts: List["_BuiltArtifact"]
    ) -> None:
        # Copy Node.js build artifacts to the package directory
        # This ensures they are included in the wheel package
        for artifact_name, artifact_path in artifacts:
            logger.info("Node.js artifacts built at %s", artifact_path)

        # Copy artifacts to package_artifacts_dir in the package
        build_py = self.get_finalized_command("build_py")
        package_dir = build_py.build_lib
        
        # Create package_artifacts_dir in the package
        package_artifacts_dir = os.path.join(package_dir, ext.package_artifacts_dir)
        os.makedirs(package_artifacts_dir, exist_ok=True)
        
        # Copy all artifacts to package_artifacts_dir
        if os.path.isdir(artifact_path):
            for root, dirs, files in os.walk(artifact_path):
                for file in files:
                    src_path = os.path.join(root, file)
                    rel_path = os.path.relpath(src_path, artifact_path)
                    dest_path = os.path.join(package_artifacts_dir, rel_path)
                    
                    # Create destination directory if needed
                    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                    
                    # Copy file
                    shutil.copy2(src_path, dest_path)
                    
                    # Set executable permissions if needed
                    mode = os.stat(dest_path).st_mode
                    mode |= (mode & 0o444) >> 2  # copy R bits to X
                    os.chmod(dest_path, mode)
                    
                    logger.debug("Copied %s to %s", src_path, dest_path)
        
        # For sdist, we need to ensure the package_artifacts_dir exists in the source
        # so it gets included in the source distribution
        source_package_artifacts_dir = os.path.join(os.getcwd(), ext.package_artifacts_dir)
        if not os.path.exists(source_package_artifacts_dir):
            os.makedirs(source_package_artifacts_dir, exist_ok=True)
            # Copy artifacts to source package_artifacts_dir for sdist
            if os.path.isdir(artifact_path):
                for root, dirs, files in os.walk(artifact_path):
                    for file in files:
                        src_path = os.path.join(root, file)
                        rel_path = os.path.relpath(src_path, artifact_path)
                        dest_path = os.path.join(source_package_artifacts_dir, rel_path)
                        
                        # Create destination directory if needed
                        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
                        
                        # Copy file
                        shutil.copy2(src_path, dest_path)
                        
                        logger.debug("Copied %s to %s for sdist", src_path, dest_path)


class _BuiltArtifact(NamedTuple):
    """
    Attributes:
        - extension_name: name of the Node.js extension
        - path: the location the artifacts have been built at
    """

    extension_name: str
    path: str


def _prepare_build_environment(env: Env, ext: NodeJSExtension) -> Dict[str, str]:
    """Prepares environment variables to use when executing npm build."""

    env_vars = (env.env or os.environ).copy()

    return env_vars
