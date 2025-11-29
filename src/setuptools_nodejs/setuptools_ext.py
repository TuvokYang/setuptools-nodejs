import os
from pathlib import Path
import sys
import logging

from typing import List, Literal, Optional, Set, Tuple, Type, TypeVar, cast
from functools import partial

from setuptools.command.build_ext import build_ext

from setuptools.command.install import install
from setuptools.command.install_lib import install_lib
from setuptools.command.sdist import sdist
from setuptools.dist import Distribution

from ._utils import Env
from .extension import NodeJSExtension

try:
    from setuptools.command.bdist_wheel import bdist_wheel
except ImportError:
    try:  # old version of setuptools
        from wheel.bdist_wheel import bdist_wheel  # type: ignore[no-redef]
    except ImportError:
        bdist_wheel = None  # type: ignore[assignment,misc]

if sys.version_info[:2] >= (3, 11):
    from tomllib import load as toml_load
else:
    try:
        from tomli import load as toml_load
    except ImportError:
        from setuptools.extern.tomli import load as toml_load


logger = logging.getLogger(__name__)

T = TypeVar("T", bound=NodeJSExtension)

def add_nodejs_extension(dist: Distribution) -> None:
    # Store the original sdist class
    sdist_base_class = cast(Type[sdist], dist.cmdclass.get("sdist", sdist))
    
    # Create a wrapper that intelligently handles Node.js extensions
    class sdist_nodejs_extension(sdist_base_class):  # type: ignore[misc,valid-type]
        def add_defaults(self) -> None:
            # First call the parent method to get default files
            super().add_defaults()
            # Then add Node.js source directories, excluding specified directories
            if hasattr(self.distribution, 'nodejs_extensions') and self.distribution.nodejs_extensions:
                logger.debug("sdist_nodejs_extension.add_defaults() called")
                
                # Get the first extension to get configuration
                extension = self.distribution.nodejs_extensions[0]
                source_dir = extension.source_dir
                exclude_dirs = extension.exclude_dirs
                
                logger.debug(f"source_dir: {source_dir}")
                logger.debug(f"exclude_dirs: {exclude_dirs}")
                
                # Convert source_dir to Path object for normalization
                source_dir_path = Path(source_dir)
                
                # Check if source_dir exists
                if not source_dir_path.exists():
                    logger.warning(f"source_dir {source_dir} does not exist, skipping")
                    return
                
                logger.debug(f"source_dir_path exists: {source_dir_path.exists()}")
                logger.debug(f"source_dir_path: {source_dir_path}")
                
                # Add all files from source_dir, excluding exclude_dirs
                file_count = 0
                for file_path in source_dir_path.rglob('*'):
                    # Skip directories
                    if file_path.is_dir():
                        continue
                    
                    # Check if this file should be excluded
                    should_exclude = False
                    
                    # Always exclude node_modules
                    if "node_modules" in file_path.parts:
                        should_exclude = True
                        logger.debug(f"Excluding {file_path} (node_modules)")
                    
                    # Check exclude_dirs
                    if not should_exclude:
                        rel_path = file_path.relative_to(source_dir_path)
                        for exclude_dir in exclude_dirs:
                            exclude_path = source_dir_path / exclude_dir
                            try:
                                file_path.relative_to(exclude_path)
                                should_exclude = True
                                logger.debug(f"Excluding {file_path} (exclude_dir: {exclude_dir})")
                                break
                            except ValueError:
                                # File is not under exclude_dir
                                pass
                    
                    if should_exclude:
                        continue
                    
                    # Add the file to the distribution
                    file_str = str(file_path)
                    if file_str not in self.filelist.files:
                        logger.debug(f"Adding {file_str} to sdist")
                        self.filelist.append(file_str)
                        file_count += 1
                
                logger.debug(f"Added {file_count} files from {source_dir} to sdist")
                logger.debug(f"Total files in sdist: {len(self.filelist.files)}")

    dist.cmdclass["sdist"] = sdist_nodejs_extension

    build_ext_base_class = cast(
        Type[build_ext], dist.cmdclass.get("build_ext", build_ext)
    )
    build_ext_options = build_ext_base_class.user_options.copy()

    class build_ext_nodejs_extension(build_ext_base_class):  # type: ignore[misc,valid-type]
        user_options = build_ext_options

        def run(self) -> None:
            super().run()
            logger.debug("build_ext_nodejs_extension.run() called")
            logger.debug(f"has nodejs_extensions: {hasattr(self.distribution, 'nodejs_extensions')}")
            if hasattr(self.distribution, 'nodejs_extensions'):
                logger.debug(f"nodejs_extensions: {self.distribution.nodejs_extensions}")
            if hasattr(self.distribution, 'nodejs_extensions') and self.distribution.nodejs_extensions:
                logger.info("running build_nodejs")
                build_nodejs = self.get_finalized_command("build_nodejs")
                build_nodejs.inplace = self.inplace
                build_nodejs.verbose = self.verbose
                build_nodejs.plat_name = self._get_wheel_plat_name() or self.plat_name
                build_nodejs.run()

        def _get_wheel_plat_name(self) -> Optional[str]:
            cmd = _get_bdist_wheel_cmd(self.distribution)
            return cast(Optional[str], getattr(cmd, "plat_name", None))

    dist.cmdclass["build_ext"] = build_ext_nodejs_extension

    clean_base_class = dist.cmdclass.get("clean")

    if clean_base_class is not None:

        class clean_nodejs_extension(clean_base_class):  # type: ignore[misc,valid-type]
            def run(self) -> None:
                super().run()
                if not self.dry_run:
                    self.run_command("clean_nodejs")

        dist.cmdclass["clean"] = clean_nodejs_extension

    install_base_class = cast(Type[install], dist.cmdclass.get("install", install))

    class install_nodejs_extension(install_base_class):  # type: ignore[misc,valid-type]
        def run(self) -> None:
            super().run()
            # For Node.js extensions, we don't need special install handling
            # since artifacts are included via package-data

    dist.cmdclass["install"] = install_nodejs_extension

    install_lib_base_class = cast(
        Type[install_lib], dist.cmdclass.get("install_lib", install_lib)
    )

    class install_lib_nodejs_extension(install_lib_base_class):  # type: ignore[misc,valid-type]
        def get_exclusions(self) -> Set[str]:
            exclusions: Set[str] = super().get_exclusions()
            # No special exclusions needed for Node.js extensions
            return exclusions

    dist.cmdclass["install_lib"] = install_lib_nodejs_extension

    if bdist_wheel is not None:
        bdist_wheel_base_class = cast(
            Type[bdist_wheel], dist.cmdclass.get("bdist_wheel", bdist_wheel)
        )
        bdist_wheel_options = bdist_wheel_base_class.user_options.copy()

        class bdist_wheel_nodejs_extension(bdist_wheel_base_class):  # type: ignore[misc,valid-type]
            user_options = bdist_wheel_options

            def initialize_options(self) -> None:
                super().initialize_options()

            def get_tag(self) -> Tuple[str, str, str]:
                # python, abi, plat = super().get_tag()
                # No special platform handling needed for Node.js extensions
                return 'py3', 'none', 'any'

        dist.cmdclass["bdist_wheel"] = bdist_wheel_nodejs_extension


def nodejs_extensions(
    dist: Distribution, attr: Literal["nodejs_extensions"], value: List[NodeJSExtension]
) -> None:
    assert attr == "nodejs_extensions"
    has_nodejs_extensions = len(value) > 0

    # Monkey patch has_ext_modules to include Node.js extensions.
    orig_has_ext_modules = dist.has_ext_modules
    dist.has_ext_modules = lambda: (orig_has_ext_modules() or has_nodejs_extensions)  # type: ignore[method-assign]

    if has_nodejs_extensions:
        add_nodejs_extension(dist)


def pyprojecttoml_config(dist: Distribution) -> None:
    logger.debug("setuptools_nodejs pyprojecttoml_config called")
    
    # Get Node.js extensions from configuration
    extensions = get_nodejs_extensions_from_config()
    
    # Always set nodejs_extensions attribute, even if empty
    dist.nodejs_extensions = extensions  # type: ignore[attr-defined]
    
    if extensions:
        logger.debug(f"created nodejs_extensions: {dist.nodejs_extensions}")
        nodejs_extensions(dist, "nodejs_extensions", dist.nodejs_extensions)  # type: ignore[attr-defined]
        
        # Automatically add package-data for package_artifacts_dir
        if not hasattr(dist, 'package_data') or dist.package_data is None:
            dist.package_data = {}
        
        # Add package_artifacts_dir/**/* to package_data for all packages
        # Use the first extension's package_artifacts_dir, or default to "frontend"
        package_artifacts_dir = "frontend"
        if dist.nodejs_extensions and hasattr(dist.nodejs_extensions[0], 'package_artifacts_dir'):
            package_artifacts_dir = dist.nodejs_extensions[0].package_artifacts_dir
        
        dist.package_data["*"] = [f"{package_artifacts_dir}/**/*"]
        logger.debug(f"automatically added package_data: {dist.package_data}")
        
        logger.debug(f"final package_data: {dist.package_data}")
        
        # Register find_nodejs_source_files as a file finder for sdist
        # This ensures Node.js source files are included in sdist but not in wheel
        # if not hasattr(dist, 'find_files'):
        #     dist.find_files = {}
        # dist.find_files['nodejs'] = find_nodejs_source_files
        # logger.debug("Registered find_nodejs_source_files as file finder")
        
    else:
        logger.debug("no setuptools-nodejs config found or no extensions created")


def _create(constructor: Type[T], config: dict) -> T:
    kwargs = {
        # PEP 517/621 convention: pyproject.toml uses dashes
        k.replace("-", "_"): v
        for k, v in config.items()
    }
    # Set target from source_dir if not provided
    if "target" not in kwargs:
        kwargs["target"] = kwargs.get("source_dir", "nodejs")
    return constructor(**kwargs)

def get_nodejs_extensions_from_config() -> List[NodeJSExtension]:
    """
    Read configuration from pyproject.toml and create NodeJSExtension instances.
    
    Returns:
        List of NodeJSExtension instances, empty list if no configuration found
    """
    try:
        with open("pyproject.toml", "rb") as f:
            cfg = toml_load(f).get("tool", {}).get("setuptools-nodejs")
        logger.debug(f"pyproject.toml config: {cfg}")
    except FileNotFoundError:
        logger.debug("pyproject.toml not found")
        return []
    except Exception as e:
        logger.debug(f"Error reading pyproject.toml: {e}")
        return []

    if cfg:
        # Handle frontend-projects array format
        frontend_projects = cfg.get("frontend-projects", [])
        logger.debug(f"frontend_projects: {frontend_projects}")
        extensions = map(partial(_create, NodeJSExtension), frontend_projects)
        return [*extensions]
    else:
        logger.debug("no setuptools-nodejs config found")
        return []


def _get_bdist_wheel_cmd(
    dist: Distribution, create: Literal[True, False] = True
) -> Optional[bdist_wheel]:
    try:
        cmd_obj = dist.get_command_obj("bdist_wheel", create=create)
        cmd_obj.ensure_finalized()  # type: ignore[union-attr]
        return cast(bdist_wheel, cmd_obj)
    except Exception:
        return None


def find_nodejs_source_files(dirname: str) -> list[str]:
    """
    File finder for Node.js source files in sdist only.
    This adds Node.js source directories to sdist but not to wheel.
    
    Args:
        dirname: The directory to search (ignored, we search based on config)
        
    Returns:
        List of file paths relative to project root
    """
    # Get Node.js extensions from configuration
    extensions = get_nodejs_extensions_from_config()
    files = []
    
    for extension in extensions:
        logger.debug(f"Processing extension: {extension.name}")
        logger.debug(f"source_dir: {extension.source_dir}")
        logger.debug(f"exclude_dirs: {extension.exclude_dirs}")
        
        # Use the extension's get_source_files method
        extension_files = extension.get_source_files()
        files.extend(extension_files)
        
        logger.debug(f"Added {len(extension_files)} files from {extension.source_dir}")
    
    logger.debug(f"find_nodejs_source_files found {len(files)} files total")
    logger.debug(f"Files found: {files[:10]}")  # Show first 10 files for debugging
    return files
