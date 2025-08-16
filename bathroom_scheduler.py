#!/usr/bin/env python3
"""
Bathroom Health Monitor - Scheduled Jobs

Job 1: Motion Detection (12:30 AM - 8:00 AM PST)
Job 2: Daily Report Generation and Email (9:00 AM PST)
"""

import datetime
import time
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.main import MotionSystem
from src.bathroom_visit_detector import BathroomVisitDetector
from src.bathroom_reporter import BathroomReporter
from src.config import Config
from src.timezone_utils import now_pst, pst_datetime_today, PST

class BathroomHealthScheduler:
    def __init__(self):
        """Initialize the bathroom health monitoring scheduler."""
        self.config = Config()
        
        # Email configuration (you'll need to set these in config.py)
        self.reporter = BathroomReporter(
            smtp_server=getattr(self.config, 'SMTP_SERVER', 'smtp.gmail.com'),
            smtp_port=getattr(self.config, 'SMTP_PORT', 587),
            email=getattr(self.config, 'EMAIL_ADDRESS', ''),
            password=getattr(self.config, 'EMAIL_PASSWORD', '')
        )
        
        self.detector = BathroomVisitDetector()
        
        # Target email for reports
        self.target_email = getattr(self.config, 'REPORT_EMAIL', '')
    
    def job1_motion_detection(self):
        """
        Job 1: Run motion detection from 12:30 AM to 8:00 AM PST
        This should be scheduled to run daily at 12:30 AM
        """
        print("🌙 Starting nighttime motion detection (12:30 AM - 8:00 AM PST)")
        
        # Calculate duration until 8:00 AM PST
        now = now_pst()
        target_end = pst_datetime_today(8, 0, 0)  # 8:00 AM PST today
        
        # If it's already past 8 AM, target tomorrow's 8 AM
        if now.hour >= 8:
            target_end += datetime.timedelta(days=1)
        
        duration_seconds = (target_end - now).total_seconds()
        duration_hours = duration_seconds / 3600
        
        print(f"Motion detection will run for {duration_hours:.1f} hours until {target_end.strftime('%H:%M %Z')}")
        
        # Run motion detection with calculated duration
        motion_system = MotionSystem(duration=int(duration_seconds))
        try:
            motion_system.run()
        except KeyboardInterrupt:
            print("\n🛑 Motion detection stopped manually")
        
        print("✅ Nighttime motion detection completed")
    
    def job2_generate_report(self):
        """
        Job 2: Generate and send daily bathroom report at 9:00 AM PST
        This should be scheduled to run daily at 9:00 AM
        """
        print("📊 Starting daily report generation (9:00 AM PST)")
        
        # Get yesterday's date (the night we just monitored) in PST
        today_pst = now_pst().date()
        yesterday_pst = today_pst - datetime.timedelta(days=1)
        
        # Define the monitoring period (12:30 AM to 8:00 AM PST of "today")
        start_time = pst_datetime_today(0, 30, 0)  # 12:30 AM PST today
        end_time = pst_datetime_today(8, 0, 0)     # 8:00 AM PST today
        
        print(f"Analyzing bathroom visits from {start_time.strftime('%m/%d %H:%M %Z')} to {end_time.strftime('%m/%d %H:%M %Z')}")
        
        # Detect bathroom visits from motion events
        visits = self.detector.detect_visits_for_period(start_time, end_time)
        print(f"Found {len(visits)} bathroom visits")
        
        if visits:
            # Save visits to database
            self.detector.save_visits(visits)
            print(f"Saved {len(visits)} visits to database")
        
        # Generate report data
        report_data = self.reporter.generate_report(visits, today_pst)
        
        # Send email report
        if self.target_email:
            print(f"Sending report to {self.target_email}...")
            success = self.reporter.send_report(self.target_email, report_data, today_pst)
            if success:
                print("✅ Email report sent successfully")
            else:
                print("❌ Failed to send email report")
        else:
            print("⚠️  No target email configured - skipping email")
        
        # Print summary to console
        self._print_summary(report_data)
        
        print("✅ Daily report generation completed")
    
    def _print_summary(self, report_data):
        """Print a summary of the report to console."""
        print("\n" + "="*50)
        print("🚽 BATHROOM HEALTH SUMMARY")
        print("="*50)
        print(f"Total Visits: {report_data['total_visits']}")
        print(f"Average Duration: {report_data['avg_duration']/60:.1f} minutes")
        print(f"Total Time: {report_data['total_time']/60:.1f} minutes")
        
        if report_data['longest_visit']:
            print(f"Longest Visit: {report_data['longest_visit'].duration_seconds/60:.1f} min at {report_data['longest_visit'].visit_start.strftime('%H:%M')}")
        
        if report_data['hourly_distribution']:
            peak_hour = max(report_data['hourly_distribution'], key=report_data['hourly_distribution'].get)
            print(f"Peak Hour: {peak_hour}:00 ({report_data['hourly_distribution'][peak_hour]} visits)")
        
        print("="*50)
    
    def run_job(self, job_number: int):
        """Run a specific job by number."""
        if job_number == 1:
            self.job1_motion_detection()
        elif job_number == 2:
            self.job2_generate_report()
        else:
            print(f"❌ Invalid job number: {job_number}. Use 1 or 2.")
            sys.exit(1)

def main():
    """Main entry point for the scheduler."""
    if len(sys.argv) != 2:
        print("Usage: python bathroom_scheduler.py <job_number>")
        print("  job_number 1: Motion detection (12:30 AM - 8:00 AM)")
        print("  job_number 2: Report generation (9:00 AM)")
        sys.exit(1)
    
    try:
        job_number = int(sys.argv[1])
    except ValueError:
        print("❌ Job number must be 1 or 2")
        sys.exit(1)
    
    scheduler = BathroomHealthScheduler()
    scheduler.run_job(job_number)

if __name__ == "__main__":
    main()
