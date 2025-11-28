from .build import build_nodejs
from .clean import clean_nodejs
from .extension import NodeJSExtension
from .version import version as __version__  # noqa: F401

from .setuptools_ext import pyprojecttoml_config
from setuptools import Distribution

# PEP 517
_dist = Distribution()
pyprojecttoml_config(_dist)

__all__ = ("NodeJSExtension", "build_nodejs", "clean_nodejs")