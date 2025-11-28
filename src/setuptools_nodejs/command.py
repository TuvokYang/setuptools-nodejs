from abc import ABC, abstractmethod
import logging
from setuptools import Command, Distribution
from typing import List, Optional

from .extension import NodeJSExtension

logger = logging.getLogger(__name__)


class NodeJSCommand(Command, ABC):
    """Abstract base class for commands which interact with Node.js Extensions."""

    # Types for distutils variables which exist on all commands but seem to be
    # missing from https://github.com/python/typeshed/blob/master/stdlib/distutils/cmd.pyi
    distribution: Distribution
    verbose: int

    def initialize_options(self) -> None:
        self.extensions: List[NodeJSExtension] = []

    def finalize_options(self) -> None:
        extensions: Optional[List[NodeJSExtension]] = getattr(
            self.distribution, "nodejs_extensions", None
        )
        if extensions is None:
            # extensions is None if the setup.py file did not contain
            # nodejs_extensions keyword; just no-op if this is the case.
            return

        if not isinstance(extensions, list):
            ty = type(extensions)
            raise ValueError(
                "expected list of NodeJSExtension objects for nodejs_extensions "
                f"argument to setup(), got `{ty}`"
            )
        for i, extension in enumerate(extensions):
            if not isinstance(extension, NodeJSExtension):
                ty = type(extension)
                raise ValueError(
                    "expected NodeJSExtension object for nodejs_extensions "
                    f"argument to setup(), got `{ty}` at position {i}"
                )
        # Extensions have been verified to be at the correct type
        self.extensions = extensions

    def run(self) -> None:
        if not self.extensions:
            logger.info("%s: no nodejs_extensions defined", self.get_command_name())
            return

        all_optional = all(ext.optional for ext in self.extensions)
        # Use the environment of the first non-optional extension, or the first optional
        # extension if there is no non-optional extension.
        env = None
        for ext in self.extensions:
            if ext.env:
                env = ext.env
                if not ext.optional:
                    break

        for ext in self.extensions:
            try:
                self.run_for_extension(ext)
            except Exception as e:
                if not ext.optional:
                    raise
                else:
                    command_name = self.get_command_name()
                    logger.warning(f"{command_name}: optional Node.js extension {ext.name} failed")
                    logger.warning(str(e))

    @abstractmethod
    def run_for_extension(self, extension: NodeJSExtension) -> None: ...
