from sbc_gpio import SBCPlatform
from sbc_gpio.platforms._base import SbcPlatform_Base

platform = SBCPlatform(log_level='DEBUG', list_only=True)

if isinstance(platform, SbcPlatform_Base):
    print(platform)
    platform.gpio_valid_values
    print(f"4B3: {platform.gpio_convert('4B3')}: {platform.gpio_tuple('4B3')}")
    print(f"4C4: {platform.gpio_convert('4C4')}: {platform.gpio_tuple('4C4')}")

