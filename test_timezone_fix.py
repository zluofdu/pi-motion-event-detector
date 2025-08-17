#!/usr/bin/env python3
"""
Test timezone conversion to verify the fix
"""

import sys
import datetime
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.timezone_utils import now_pst, to_pst, format_pst

def test_timezone_conversion():
    """Test the timezone conversion fix"""
    print("🕐 Testing Timezone Conversion Fix")
    print("=" * 40)
    
    # Get current PST time
    current_pst = now_pst()
    print(f"Current PST time: {format_pst(current_pst)}")
    
    # Simulate a naive datetime (what would come from database)
    naive_dt = current_pst.replace(tzinfo=None)
    print(f"Naive datetime: {naive_dt}")
    
    # Convert back to PST using our fixed function
    converted_pst = to_pst(naive_dt)
    print(f"Converted to PST: {format_pst(converted_pst)}")
    
    # Check if they match
    time_diff = abs((current_pst - converted_pst).total_seconds())
    print(f"Time difference: {time_diff} seconds")
    
    if time_diff < 1:
        print("✅ Timezone conversion is working correctly!")
        
        # Test specific time that was problematic
        test_time = datetime.datetime(2025, 8, 17, 0, 30, 0)  # 12:30 AM
        converted_test = to_pst(test_time)
        print(f"\nTest case - 12:30 AM naive -> {format_pst(converted_test, '%H:%M %Z')}")
        
        if converted_test.hour == 0 and converted_test.minute == 30:
            print("✅ 12:30 AM conversion correct!")
            return True
        else:
            print(f"❌ Expected 00:30, got {converted_test.hour:02d}:{converted_test.minute:02d}")
            return False
    else:
        print("❌ Timezone conversion has issues")
        return False

if __name__ == "__main__":
    success = test_timezone_conversion()
    sys.exit(0 if success else 1)
