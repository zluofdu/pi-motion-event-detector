import pytest
import datetime
import pytz
from unittest.mock import patch
from src.timezone_utils import (
    now_pst, to_pst, pst_from_naive, pst_time, 
    pst_datetime_today, format_pst, PST
)

class TestTimezoneUtils:
    """Test suite for PST timezone utility functions."""

    def test_pst_timezone_constant(self):
        """Test that PST constant is correctly configured."""
        assert PST.zone == 'US/Pacific'
        assert isinstance(PST, pytz.tzinfo.DstTzInfo)

    def test_now_pst(self):
        """Test getting current time in PST."""
        pst_now = now_pst()
        
        assert pst_now.tzinfo is not None
        assert pst_now.tzinfo.zone == 'US/Pacific'
        assert isinstance(pst_now, datetime.datetime)
        
        # Should be within a few seconds of actual time
        utc_now = datetime.datetime.now(pytz.UTC)
        pst_utc = pst_now.astimezone(pytz.UTC)
        time_diff = abs((utc_now - pst_utc).total_seconds())
        assert time_diff < 5  # Within 5 seconds

    def test_to_pst_with_naive_datetime(self):
        """Test converting naive datetime to PST."""
        naive_dt = datetime.datetime(2025, 8, 14, 12, 30, 0)
        pst_dt = to_pst(naive_dt)
        
        assert pst_dt.tzinfo is not None
        # Naive datetime is treated as UTC, so 12:30 UTC becomes 5:30 PDT in August
        assert pst_dt.hour == 5  # 12 UTC - 7 hours PDT offset = 5 PDT
        assert pst_dt.minute == 30
        assert pst_dt.second == 0

    def test_to_pst_with_aware_datetime(self):
        """Test converting timezone-aware datetime to PST."""
        # Create UTC datetime
        utc_dt = pytz.UTC.localize(datetime.datetime(2025, 8, 14, 19, 30, 0))
        pst_dt = to_pst(utc_dt)
        
        assert pst_dt.tzinfo.zone == 'US/Pacific'
        # UTC 19:30 should be PST 12:30 (PDT is UTC-7)
        assert pst_dt.hour == 12
        assert pst_dt.minute == 30

    def test_pst_from_naive(self):
        """Test converting naive datetime assuming it's already PST."""
        naive_dt = datetime.datetime(2025, 8, 14, 15, 45, 30)
        pst_dt = pst_from_naive(naive_dt)
        
        assert pst_dt.tzinfo.zone == 'US/Pacific'
        assert pst_dt.hour == 15
        assert pst_dt.minute == 45
        assert pst_dt.second == 30

    def test_pst_time(self):
        """Test creating PST time object."""
        pst_time_obj = pst_time(14, 30, 45)
        
        assert pst_time_obj.hour == 14
        assert pst_time_obj.minute == 30
        assert pst_time_obj.second == 45
        assert pst_time_obj.tzinfo.zone == 'US/Pacific'

    def test_pst_time_defaults(self):
        """Test PST time with default values."""
        pst_time_obj = pst_time(9)
        
        assert pst_time_obj.hour == 9
        assert pst_time_obj.minute == 0
        assert pst_time_obj.second == 0

    def test_pst_datetime_today(self):
        """Test creating PST datetime for today."""
        result = pst_datetime_today(15, 30, 45)
        
        # Should create PST datetime with specified time
        assert result.hour == 15
        assert result.minute == 30
        assert result.second == 45
        assert result.tzinfo.zone == 'US/Pacific'
        
        # Should be today's date
        pst_now = now_pst()
        assert result.date() == pst_now.date()

    def test_format_pst_with_naive(self):
        """Test formatting naive datetime as PST."""
        naive_dt = datetime.datetime(2025, 8, 14, 10, 30, 45)
        formatted = format_pst(naive_dt)
        
        assert '2025-08-14' in formatted
        assert '10:30:45' in formatted
        assert 'PDT' in formatted or 'PST' in formatted

    def test_format_pst_with_aware(self):
        """Test formatting timezone-aware datetime as PST."""
        utc_dt = pytz.UTC.localize(datetime.datetime(2025, 8, 14, 17, 30, 45))
        formatted = format_pst(utc_dt)
        
        assert '2025-08-14' in formatted
        assert 'PDT' in formatted or 'PST' in formatted

    def test_format_pst_custom_format(self):
        """Test formatting with custom format string."""
        naive_dt = datetime.datetime(2025, 8, 14, 10, 30, 45)
        formatted = format_pst(naive_dt, '%H:%M %Z')
        
        assert '10:30' in formatted
        assert 'PDT' in formatted or 'PST' in formatted
        assert '2025' not in formatted  # Year shouldn't be included

    def test_pst_handles_dst_transition(self):
        """Test that PST properly handles daylight saving time."""
        # Create specific dates for testing DST vs standard time
        # August is PDT (UTC-7), January is PST (UTC-8)
        
        # Test summer time (PDT) - August 14, 2025 at noon
        summer_pst_dt = PST.localize(datetime.datetime(2025, 8, 14, 12, 0, 0))
        
        # Test winter time (PST) - January 14, 2025 at noon
        winter_pst_dt = PST.localize(datetime.datetime(2025, 1, 14, 12, 0, 0))
        
        # Both should have US/Pacific timezone
        assert summer_pst_dt.tzinfo.zone == 'US/Pacific'
        assert winter_pst_dt.tzinfo.zone == 'US/Pacific'
        
        # Convert to UTC to check offset
        summer_utc = summer_pst_dt.astimezone(pytz.UTC)
        winter_utc = winter_pst_dt.astimezone(pytz.UTC)
        
        # In August (PDT), 12:00 PST should be 19:00 UTC (12 + 7 = 19)
        # In January (PST), 12:00 PST should be 20:00 UTC (12 + 8 = 20)
        assert summer_utc.hour == 19  # PDT is UTC-7
        assert winter_utc.hour == 20  # PST is UTC-8