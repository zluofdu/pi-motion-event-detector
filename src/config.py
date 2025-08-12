# filepath: /home/luozhe/Workspace/motion-event/motion-event/src/config.py

DATABASE_PATH = 'motion_events.db'
EMAIL_SERVER = 'smtp.example.com'
EMAIL_PORT = 587
EMAIL_USERNAME = 'your_email@example.com'
EMAIL_PASSWORD = 'your_password'
RECIPIENT_EMAIL = 'recipient@example.com'
SUMMARY_EMAIL_TIME = '10:00'  # Time to send the summary email every day
NIGHT_START = '24:00'  # Start of night time
NIGHT_END = '06:00'    # End of night time
MOTION_EVENT_THRESHOLD = 300  # Minimum seconds between motion events to be considered separate events