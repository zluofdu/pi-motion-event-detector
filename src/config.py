# filepath: /home/luozhe/Workspace/motion-event/motion-event/src/config.py

import os
from typing import List
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Database settings
    DATABASE_PATH = 'motion_events.db'
    
    # Timezone settings
    TIMEZONE = 'US/Pacific'  # PST/PDT timezone
    
    # Email settings for bathroom health reports
    # Gmail Configuration:
    # 1. Enable 2-Factor Authentication in your Google Account
    # 2. Generate App Password: https://myaccount.google.com/apppasswords
    # 3. Use the 16-character App Password (not your regular password)
    # 4. Set environment variables (see .env.example for details)
    SMTP_SERVER = 'smtp.gmail.com'         # Gmail SMTP server
    SMTP_PORT = 587                        # Gmail SMTP port (TLS)
    EMAIL_ADDRESS = os.getenv('EMAIL_ADDRESS')
    EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')  # Gmail App Password from environment
    
    # Parse recipient emails from environment variable (comma-separated)
    _report_emails_str = os.getenv('REPORT_EMAILS', '')
    REPORT_EMAIL: List[str] = [email.strip() for email in _report_emails_str.split(',') if email.strip()]
    
    # Monitoring schedule settings (all times in PST)
    MOTION_START_TIME = '00:30'  # 12:30 AM PST - start motion detection
    MOTION_END_TIME = '08:00'    # 8:00 AM PST - end motion detection
    REPORT_TIME = '09:00'        # 9:00 AM PST - generate and send report
    
    # Visit detection settings
    CLUSTER_WINDOW_MINUTES = 5   # Group motion events within 5 minutes into one visit
    MOTION_EVENT_THRESHOLD = 300 # Minimum seconds between motion events to be considered separate events
    
    @classmethod
    def validate_email_config(cls):
        """Validate that required email configuration is set."""
        errors = []
        
        if not cls.EMAIL_ADDRESS:
            errors.append("EMAIL_ADDRESS environment variable is required")
        
        if not cls.EMAIL_PASSWORD:
            errors.append("EMAIL_PASSWORD environment variable is required")
        
        if not cls.REPORT_EMAIL:
            errors.append("REPORT_EMAILS environment variable is required")
        
        if errors:
            error_msg = "Missing required email configuration:\n" + "\n".join(f"  - {error}" for error in errors)
            error_msg += "\n\nPlease set these in your .env file. See .env.example for reference."
            raise ValueError(error_msg)
        
        return True