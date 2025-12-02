import os
import shutil
import sys
import logging

from ._utils import check_subprocess_output

from .command import NodeJSCommand
from .extension import NodeJSExtension

logger = logging.getLogger(__name__)


class clean_nodejs(NodeJSCommand):
    """Clean Node.js extensions."""

    description = "clean Node.js extensions (remove node_modules and build artifacts)"

    def initialize_options(self) -> None:
        super().initialize_options()
        self.inplace = False

    def run_for_extension(self, ext: NodeJSExtension) -> None:
        # Try npm run clean first if it exists
        package_json_path = os.path.join(ext.source_dir, "package.json")
        if os.path.exists(package_json_path):
            try:
                # Check if package.json has a "clean" script
                import json
                with open(package_json_path, 'r') as f:
                    package_json = json.load(f)
                
                if "scripts" in package_json and "clean" in package_json["scripts"]:
                    # Use npm run clean
                    args = ["npm", "run", "clean"]
                    if ext.args:
                        args.extend(ext.args)

                    if not ext.quiet:
                        logger.info(" ".join(args))

                    # Execute npm clean command
                    try:
                        check_subprocess_output(
                            args, 
                            env=ext.env, 
                            text=True, 
                            encoding='utf-8', 
                            shell=self.shell_enable,
                            cwd=ext.source_dir
                        )
                        return  # Successfully cleaned with npm
                    except Exception:
                        # If npm clean fails, fall back to manual cleanup
                        pass
            except Exception:
                # If we can't read package.json, fall back to manual cleanup
                pass

        # Manual cleanup: remove node_modules and artifacts directory
        node_modules_path = os.path.join(ext.source_dir, "node_modules")
        artifacts_path = ext.get_artifact_path()

        if not ext.quiet:
            logger.info(f"Removing {node_modules_path} and {artifacts_path}")

        # Remove node_modules
        if os.path.exists(node_modules_path):
            shutil.rmtree(node_modules_path, ignore_errors=True)

        # Remove artifacts directory
        if os.path.exists(artifacts_path):
            shutil.rmtree(artifacts_path, ignore_errors=True)
