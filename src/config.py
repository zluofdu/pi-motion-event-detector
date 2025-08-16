# filepath: /home/luozhe/Workspace/motion-event/motion-event/src/config.py

class Config:
    # Database settings
    DATABASE_PATH = 'motion_events.db'
    
    # Timezone settings
    TIMEZONE = 'US/Pacific'  # PST/PDT timezone
    
    # Email settings for bathroom health reports
    SMTP_SERVER = 'smtp.gmail.com'  # Change to your SMTP server
    SMTP_PORT = 587
    EMAIL_ADDRESS = 'your_email@gmail.com'  # Your sender email
    EMAIL_PASSWORD = 'your_app_password'    # Your email app password
    REPORT_EMAIL = 'recipient@gmail.com'    # Where to send reports
    
    # Monitoring schedule settings (all times in PST)
    MOTION_START_TIME = '00:30'  # 12:30 AM PST - start motion detection
    MOTION_END_TIME = '08:00'    # 8:00 AM PST - end motion detection
    REPORT_TIME = '09:00'        # 9:00 AM PST - generate and send report
    
    # Visit detection settings
    CLUSTER_WINDOW_MINUTES = 5   # Group motion events within 5 minutes into one visit
    MOTION_EVENT_THRESHOLD = 300 # Minimum seconds between motion events to be considered separate events