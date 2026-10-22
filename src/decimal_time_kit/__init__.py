# decimal_time_kit
#
# Public surface for the package.  We re-export the two conversion
# functions and the dataclass that carries a result so callers can do
# `from decimal_time_kit import to_decimal, to_standard, DecimalTime`
# without reaching into the `core` submodule.

from .core import (
    DecimalTime,
    to_decimal,
    to_standard,
)

__all__ = ["DecimalTime", "to_decimal", "to_standard"]
