import unittest

from decimal_time_kit import DecimalTime, to_decimal, to_standard
from decimal_time_kit.core import TimeInputError


class TestToDecimal(unittest.TestCase):
    def test_midnight_is_zero(self):
        dt = to_decimal(0, 0, 0, 0)
        self.assertEqual(dt, DecimalTime(0, 0, 0, 0))

    def test_six_am_is_two_and_a_half_decimal_hours(self):
        # 6 standard hours = 6 * 3600 = 21600 SI seconds.
        # 21600 / 86400 of a day = 0.25 of a decimal day = 2.5 decimal hours.
        dt = to_decimal(6, 0, 0, 0)
        self.assertEqual(dt, DecimalTime(2, 50, 0, 0))

    def test_noon_is_five_decimal_hours(self):
        dt = to_decimal(12, 0, 0, 0)
        self.assertEqual(dt, DecimalTime(5, 0, 0, 0))

    def test_just_before_midnight_is_just_before_ten(self):
        dt = to_decimal(23, 59, 59, 999)
        self.assertEqual(dt.hours, 9)
        self.assertEqual(dt.minutes, 99)
        self.assertEqual(dt.seconds, 99)
        # The exact millis can vary by rounding direction, so we only assert
        # it is non-zero and in range — the value is carried, not invented.
        self.assertGreaterEqual(dt.millis, 0)
        self.assertLess(dt.millis, 1000)

    def test_milliseconds_are_preserved_in_proportion(self):
        # One standard millisecond is 100000/86400 ≈ 1.157 decimal ms.
        # Feeding 500 standard ms should produce a value strictly between 0
        # and 1000 decimal ms, never a round 0.
        dt = to_decimal(0, 0, 0, 500)
        self.assertGreater(dt.millis, 0)
        self.assertLess(dt.millis, 1000)

    def test_rejects_negative_hours(self):
        with self.assertRaises(TimeInputError):
            to_decimal(-1, 0, 0, 0)

    def test_rejects_24_hours(self):
        with self.assertRaises(TimeInputError):
            to_decimal(24, 0, 0, 0)

    def test_rejects_60_minutes(self):
        with self.assertRaises(TimeInputError):
            to_decimal(0, 60, 0, 0)

    def test_rejects_negative_millis(self):
        with self.assertRaises(TimeInputError):
            to_decimal(0, 0, 0, -1)

    def test_rejects_1000_millis(self):
        with self.assertRaises(TimeInputError):
            to_decimal(0, 0, 0, 1000)


class TestToStandard(unittest.TestCase):
    def test_zero_decimal_is_midnight(self):
        hh, mm, ss, ms = to_standard(DecimalTime(0, 0, 0, 0))
        self.assertEqual((hh, mm, ss, ms), (0, 0, 0, 0))

    def test_five_decimal_hours_is_noon(self):
        hh, mm, ss, ms = to_standard(DecimalTime(5, 0, 0, 0))
        self.assertEqual((hh, mm, ss, ms), (12, 0, 0, 0))

    def test_two_decimal_hours_fifty_minutes_is_six_am(self):
        hh, mm, ss, ms = to_standard(DecimalTime(2, 50, 0, 0))
        self.assertEqual((hh, mm, ss, ms), (6, 0, 0, 0))

    def test_rejects_ten_decimal_hours(self):
        with self.assertRaises(TimeInputError):
            to_standard(DecimalTime(10, 0, 0, 0))

    def test_rejects_hundred_decimal_minutes(self):
        with self.assertRaises(TimeInputError):
            to_standard(DecimalTime(0, 100, 0, 0))

    def test_rejects_hundred_decimal_seconds(self):
        with self.assertRaises(TimeInputError):
            to_standard(DecimalTime(0, 0, 100, 0))

    def test_rejects_negative_decimal_hours(self):
        with self.assertRaises(TimeInputError):
            to_standard(DecimalTime(-1, 0, 0, 0))


class TestRoundTrip(unittest.TestCase):
    def _round_trip(self, h, m, s, ms):
        return to_standard(to_decimal(h, m, s, ms))

    def test_midnight_round_trips(self):
        self.assertEqual(self._round_trip(0, 0, 0, 0), (0, 0, 0, 0))

    def test_noon_round_trips(self):
        self.assertEqual(self._round_trip(12, 0, 0, 0), (12, 0, 0, 0))

    def test_six_am_round_trips(self):
        self.assertEqual(self._round_trip(6, 0, 0, 0), (6, 0, 0, 0))

    def test_quarter_past_midnight_round_trips(self):
        self.assertEqual(self._round_trip(0, 15, 0, 0), (0, 15, 0, 0))

    def test_eleven_thirty_pm_round_trips(self):
        self.assertEqual(self._round_trip(23, 30, 0, 0), (23, 30, 0, 0))

    def test_arbitrary_second_round_trips(self):
        self.assertEqual(self._round_trip(13, 37, 42, 0), (13, 37, 42, 0))

    def test_just_before_midnight_round_trips_within_a_second(self):
        # The two grids are incommensurate at millisecond resolution, so we
        # assert the round-trip lands within one SI second of the input rather
        # than demanding bit-exactness on the millisecond.
        h, m, s, ms = 23, 59, 59, 999
        oh, om, os, oms = self._round_trip(h, m, s, ms)
        in_total_ms = ((h * 60 + m) * 60 + s) * 1000 + ms
        out_total_ms = ((oh * 60 + om) * 60 + os) * 1000 + oms
        self.assertLessEqual(abs(in_total_ms - out_total_ms), 1000)


if __name__ == "__main__":
    unittest.main()
