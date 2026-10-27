# decimal_time_kit

Converts between standard 24-hour time and French decimal time. Decimal time divides the day into 10 hours of 100 minutes of 100 seconds, so one decimal second is 0.864 SI seconds.

```python
from decimal_time_kit import to_decimal, to_standard, DecimalTime

# Midnight to decimal
assert to_decimal(0, 0, 0, 0) == DecimalTime(0, 0, 0, 0)

# Noon maps to 5 decimal hours exactly
assert to_decimal(12, 0, 0, 0) == DecimalTime(5, 0, 0, 0)

# And back
assert to_standard(DecimalTime(5, 0, 0, 0)) == (12, 0, 0, 0)
```

## Why this exists

The library exists to do one conversion with no surprises and no dependencies. The entire calculation is carried out in integer arithmetic (millidecimal-seconds internally) so results are deterministic across machines and Python versions; floating point never touches the comparison path.

## The edge you will hit

The standard and decimal grids are incommensurate at millisecond resolution: 86 400 does not divide 100 000. Whole-second inputs round-trip exactly, but a millisecond-precision input may drift by up to one SI second when converted to decimal and back. `DecimalTime.millis` carries the sub-second remainder forward so the value you put in is never silently truncated, only quantised by the grid ratio when you convert back.

## Design notes

The window stores values eagerly rather than keeping running aggregates. Running
sums drift with floating point over long streams, and recomputing from a small
buffer is cheap enough that the drift is not worth the speed.

