#!/usr/bin/env python3
"""
Email Test Script for Bathroom Health Monitor
Tests Gmail configuration and email sending functionality
"""

import sys
import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from src.config import Config
    from src.bathroom_reporter import BathroomReporter
    from src.models.bathroom_visit import BathroomVisit
    from src.timezone_utils import pst_from_naive
    print("✅ All modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure all dependencies are installed: pip install -r requirements.txt")
    sys.exit(1)

def test_email_configuration():
    """Test email configuration and send a test email."""
    print("📧 Testing Gmail Configuration")
    print("=" * 40)
    
    # Validate email configuration
    try:
        Config.validate_email_config()
        print("✅ Email configuration validated")
    except ValueError as e:
        print(f"❌ Configuration Error:")
        print(f"{e}")
        return False
    
    # Load configuration
    config = Config()
    
    # REPORT_EMAIL is always expected to be a list
    recipient_emails = getattr(config, 'REPORT_EMAIL', [])
    
    # Check configuration
    print("📋 Current Email Settings:")
    print(f"   SMTP Server: {config.SMTP_SERVER}")
    print(f"   SMTP Port: {config.SMTP_PORT}")
    print(f"   Sender Email: {config.EMAIL_ADDRESS}")
    print(f"   Recipient Emails: {recipient_emails}")
    print(f"   Password: {'*' * len(config.EMAIL_PASSWORD) if config.EMAIL_PASSWORD != 'your_app_password' else 'NOT CONFIGURED'}")
    print()
    
    # Validate configuration
    if config.EMAIL_ADDRESS == 'your_email@gmail.com':
        print("❌ Email address not configured. Update src/config.py")
        return False
    
    if config.EMAIL_PASSWORD == 'your_app_password':
        print("❌ Email password not configured. Update src/config.py")
        return False
    
    if not recipient_emails:
        print("❌ No recipient emails configured. Update REPORT_EMAIL in src/config.py")
        return False
    
    if not config.EMAIL_ADDRESS.endswith('@gmail.com'):
        print("⚠️  Warning: Email address doesn't appear to be Gmail")
    
    # Create reporter
    try:
        reporter = BathroomReporter(
            smtp_server=config.SMTP_SERVER,
            smtp_port=config.SMTP_PORT,
            email=config.EMAIL_ADDRESS,
            password=config.EMAIL_PASSWORD
        )
        print("✅ Reporter created successfully")
    except Exception as e:
        print(f"❌ Failed to create reporter: {e}")
        return False
    
    # Create test data
    print("📊 Creating test report data...")
    
    # Generate sample bathroom visits for testing
    sample_visits = []
    base_time = datetime.datetime(2025, 8, 16, 2, 0, 0)
    
    for i in range(3):
        start_time = pst_from_naive(base_time + datetime.timedelta(hours=i*2))
        end_time = start_time + datetime.timedelta(minutes=5 + i)
        
        visit = BathroomVisit(
            device_id='pir_sensor_4',
            visit_start=start_time,
            visit_end=end_time,
            event_count=2 + i,
            duration_seconds=300 + i*60
        )
        sample_visits.append(visit)
    
    # Generate report
    try:
        report_date = datetime.date.today()
        report_data = reporter.generate_report(sample_visits, report_date)
        print("✅ Test report data generated")
        print(f"   Total visits: {report_data['total_visits']}")
        print(f"   Average duration: {report_data['avg_duration']/60:.1f} minutes")
    except Exception as e:
        print(f"❌ Failed to generate report: {e}")
        return False
    
    # Send test emails to all recipients
    print(f"📤 Sending test emails to {len(recipient_emails)} recipient(s)...")
    try:
        successful_sends = 0
        failed_sends = 0
        
        for email in recipient_emails:
            print(f"📧 Sending to {email}...")
            success = reporter.send_report(email, report_data, report_date)
            
            if success:
                print(f"✅ Successfully sent to {email}")
                successful_sends += 1
            else:
                print(f"❌ Failed to send to {email}")
                failed_sends += 1
        
        print(f"📊 Summary: {successful_sends} successful, {failed_sends} failed")
        
        if successful_sends > 0:
            print("✅ Test email(s) sent successfully!")
            print(f"   Check inbox(es): {', '.join(recipient_emails)}")
            print("   Subject: 🚽 Bathroom Health Report - [today's date]")
            return successful_sends == len(recipient_emails)  # All must succeed
        else:
            print("❌ Failed to send test emails")
            print("   Common issues:")
            print("   - Check your app password (should be 16 characters)")
            print("   - Ensure 2-Factor Authentication is enabled")
            print("   - Verify sender email address")
            return False
            
    except Exception as e:
        print(f"❌ Email sending error: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Verify Gmail App Password is correct")
        print("   2. Check internet connection")
        print("   3. Ensure Gmail allows 'Less secure app access' or use App Password")
        print("   4. Try regenerating Gmail App Password")
        return False

def main():
    """Main test function."""
    print("🚽 Bathroom Health Monitor - Email Test")
    print("======================================")
    print()
    
    success = test_email_configuration()
    
    print()
    if success:
        print("🎉 Email configuration test completed successfully!")
        print()
        print("📋 Next Steps:")
        print("   1. Set up automated scheduling: ./setup_cron.sh")
        print("   2. Check system status: ./status.sh")
        print("   3. View logs: tail -f /tmp/bathroom_report.log")
    else:
        print("❌ Email configuration test failed")
        print()
        print("🔧 To fix:")
        print("   1. Run email setup: ./configure_email.sh")
        print("   2. Verify Gmail App Password setup")
        print("   3. Re-run this test: python test_email.py")
    
    print()

if __name__ == "__main__":
    main()
