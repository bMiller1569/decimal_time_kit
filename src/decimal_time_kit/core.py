# decimal_time_kit
#
# Core conversion logic between standard 24-hour time and French decimal time.
#
# French decimal time was introduced during the French Revolution.  The day is
# split into 10 decimal hours, each of 100 decimal minutes, each of 100 decimal
# seconds.  So one decimal day is 100 000 decimal seconds.
#
# A standard day has 86 400 SI seconds.  The conversion factor is therefore
# 86 400 / 100 000 = 0.864.  We carry the calculation out in integral
# millidecimal-seconds (one-thousandth of a decimal second) so that rounding is
# explicit and deterministic; floating point never touches the comparison path.

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

# Whole SI seconds in one standard day.
_STANDARD_DAY_SECONDS: int = 86_400

# Whole decimal seconds in one decimal day.
_DECIMAL_DAY_SECONDS: int = 100_000

# A decimal second expressed in milliseconds gives us headroom for rounding
# without ever hitting float arithmetic.  One decimal day is 100 000 decimal
# seconds = 100 000 000 decimal milliseconds.
_DECIMAL_DAY_MILLIS: int = 100_000_000


class TimeInputError(ValueError):
    """Raised when caller-supplied time components are out of range."""


@dataclass(frozen=True)
class DecimalTime:
    """A moment expressed in French decimal time.

    Attributes:
        hours: Decimal hour, 0-9.
        minutes: Decimal minute, 0-99.
        seconds: Decimal second, 0-99.  The ``millis`` field carries any
            sub-second remainder so the trio (hours, minutes, seconds) always
            represents a value rounded down to the nearest whole decimal
            second.
        millis: Decimal milliseconds, 0-999.  Lets callers recover the exact
            input when round-tripping through :func:`to_standard`.
    """

    hours: int
    minutes: int
    seconds: int
    millis: int

    def to_decimal_seconds(self) -> float:
        """Return the value as a total count of decimal seconds.

        Useful for sorting or arithmetic; kept as a float purely for
        ergonomics, never used internally for equality.
        """
        return (
            self.hours * 10_000
            + self.minutes * 100
            + self.seconds
            + self.millis / 1_000
        )


def _validate_standard(h: int, m: int, s: int, ms: int) -> None:
    if not 0 <= h <= 23:
        raise TimeInputError(f"hours must be 0-23, got {h}")
    if not 0 <= m <= 59:
        raise TimeInputError(f"minutes must be 0-59, got {m}")
    if not 0 <= s <= 59:
        raise TimeInputError(f"seconds must be 0-59, got {s}")
    if not 0 <= ms < 1_000:
        raise TimeInputError(f"millis must be 0-999, got {ms}")


def to_decimal(hours: int, minutes: int, seconds: int, millis: int = 0) -> DecimalTime:
    """Convert a standard 24-hour time-of-day to French decimal time.

    The inputs describe a moment within a single day; date and timezone are
    intentionally out of scope.  ``millis`` is accepted so that a
    millisecond-precision source can be round-tripped losslessly.

    Args:
        hours: 0-23.
        minutes: 0-59.
        seconds: 0-59.
        millis: 0-999.  Defaults to 0 for callers working at whole-second
            resolution.

    Returns:
        A :class:`DecimalTime` whose sub-second part lives in ``millis``.

    Raises:
        TimeInputError: If any component is outside its valid range.
    """
    _validate_standard(hours, minutes, seconds, millis)

    # Total SI milliseconds elapsed since local midnight.
    total_si_ms: int = (
        ((hours * 60 + minutes) * 60 + seconds) * 1_000 + millis
    )

    # Map the SI-millisecond day [0, 86_400_000) onto the decimal-millisecond
    # day [0, 100_000_000).  Multiplying first keeps the ratio exact in integer
    # arithmetic; the denominator is 86_400_000.  We add half the denominator
    # before floor division so that the result is the nearest decimal
    # millisecond, not the truncated one — this makes whole-second inputs
    # round-trip exactly.
    total_dec_ms: int = (total_si_ms * _DECIMAL_DAY_MILLIS + (_STANDARD_DAY_SECONDS * 500)) // (_STANDARD_DAY_SECONDS * 1_000)

    # Split into hours / minutes / seconds / millis.  The modulo chain is
    # written so each field's range matches its conceptual maximum.
    dh: int = total_dec_ms // 10_000_000
    rem: int = total_dec_ms % 10_000_000
    dm: int = rem // 100_000
    rem %= 100_000
    ds: int = rem // 1_000
    dms: int = rem % 1_000

    return DecimalTime(hours=dh, minutes=dm, seconds=ds, millis=dms)


def _validate_decimal(h: int, m: int, s: int, ms: int) -> None:
    if not 0 <= h <= 9:
        raise TimeInputError(f"decimal hours must be 0-9, got {h}")
    if not 0 <= m <= 99:
        raise TimeInputError(f"decimal minutes must be 0-99, got {m}")
    if not 0 <= s <= 99:
        raise TimeInputError(f"decimal seconds must be 0-99, got {s}")
    if not 0 <= ms < 1_000:
        raise TimeInputError(f"decimal millis must be 0-999, got {ms}")


def to_standard(dt: DecimalTime) -> Tuple[int, int, int, int]:
    """Convert a :class:`DecimalTime` back to standard 24-hour time.

    Args:
        dt: A populated :class:`DecimalTime`.

    Returns:
        A 4-tuple ``(hours, minutes, seconds, millis)`` where ``hours`` is
        0-23, ``minutes`` and ``seconds`` are 0-59, and ``millis`` is 0-999.

    Raises:
        TimeInputError: If any field of ``dt`` is outside its valid range.
    """
    _validate_decimal(dt.hours, dt.minutes, dt.seconds, dt.millis)

    total_dec_ms: int = (
        ((dt.hours * 100 + dt.minutes) * 100 + dt.seconds) * 1_000 + dt.millis
    )

    total_si_ms: int = (total_dec_ms * (_STANDARD_DAY_SECONDS * 1_000) + (_DECIMAL_DAY_MILLIS // 2)) // _DECIMAL_DAY_MILLIS

    hh: int = total_si_ms // 3_600_000
    rem: int = total_si_ms % 3_600_000
    mm: int = rem // 60_000
    rem %= 60_000
    ss: int = rem // 1_000
    ms_out: int = rem % 1_000

    return hh, mm, ss, ms_out
