from logging_handler import create_logger, INFO, DEBUG
import os
from importlib import import_module
from .platforms._base import SbcPlatform_Base

PLATFORM_BASE_DIR = os.path.join(os.path.dirname(__file__), 'platforms')

def SBCPlatform(list_only=False, log_level=INFO):
    ''' Identify the platform and return the SbcPlatformClass that matches '''
    logger = create_logger(console_level=log_level, name=__name__)

    # Get a list of the platform files
    logger.debug(f"{__name__}: Listing platform files from: {PLATFORM_BASE_DIR}")
    platform_files = os.listdir(PLATFORM_BASE_DIR)
    supported_platforms = []
    matched_platform = None
    for platform_file in platform_files:
        if platform_file.endswith('.py') and not platform_file.startswith('_'):
            try:
                logger.debug(f"{__name__}: {platform_file}: Testing platform file...")
                module = import_module(f"sbc_gpio.platforms.{platform_file.split('.py')[0]}")
                supported_platforms += [platform.get('description', platform.get('model')) for platform in module.SUPPORTED_PLATFORMS]
                sbc_platform = module.SbcPlatformClass(log_level=log_level)
                if sbc_platform.platform_matched:
                    logger.info(f"{__name__}: {platform_file}: Matched platform: {sbc_platform.description}")
                    if not list_only:
                        return sbc_platform
                    matched_platform = sbc_platform
            except Exception as e:
                logger.warning(f'{__name__}: Unable to import {platform_file}. Error: {e}')

    if list_only:
        print(f'Supported platforms: {supported_platforms}')
        if matched_platform is not None:
            print(f'Matched platform: {matched_platform.description}')
        quit()

    # platform wasn't identified
    raise ImportError(f'Unable to identify platform.  Supported platforms: {supported_platforms}')