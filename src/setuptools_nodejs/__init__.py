import logging
import os
from .build import build_nodejs
from .clean import clean_nodejs
from .extension import NodeJSExtension
from .version import version as __version__  # noqa: F401

logger = logging.getLogger(__name__)
if os.environ.get("SETUPTOOLS_NODEJS_DEBUG")==1:
    logging.basicConfig(level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
__all__ = ("NodeJSExtension", "build_nodejs", "clean_nodejs")