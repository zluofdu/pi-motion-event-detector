import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from collections import defaultdict
import statistics
from src.models.bathroom_visit import BathroomVisit
from src.timezone_utils import to_pst, format_pst, PST
from src.config import Config

class BathroomReporter:
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        """
        Initialize the bathroom reporter.
        
        Args:
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            email: Sender email address
            password: Email password or app password
        """
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
    
    def _format_time_display(self, time_str: str) -> str:
        """Format time string (HH:MM) for display with AM/PM."""
        hour, minute = map(int, time_str.split(':'))
        if hour == 0:
            return f"12:{minute:02d} AM"
        elif hour < 12:
            return f"{hour}:{minute:02d} AM"
        elif hour == 12:
            return f"12:{minute:02d} PM"
        else:
            return f"{hour - 12}:{minute:02d} PM"
    
    def generate_report(self, visits: List[BathroomVisit], report_date: datetime.date) -> Dict[str, Any]:
        """Generate comprehensive report data from bathroom visits."""
        if not visits:
            return {
                'total_visits': 0,
                'avg_duration': 0,
                'total_time': 0,
                'hourly_distribution': {},
                'trends': [],
                'longest_visit': None,
                'shortest_visit': None
            }
        
        # Basic statistics
        total_visits = len(visits)
        durations = [v.duration_seconds for v in visits]
        avg_duration = statistics.mean(durations)
        total_time = sum(durations)
        
        # Hourly distribution
        hourly_counts = defaultdict(int)
        for visit in visits:
            # Ensure timezone conversion to PST for consistent hourly grouping
            visit_time_pst = to_pst(visit.visit_start)
            hour = visit_time_pst.hour
            hourly_counts[hour] += 1
        
        # Find extremes
        longest_visit = max(visits, key=lambda v: v.duration_seconds)
        shortest_visit = min(visits, key=lambda v: v.duration_seconds)
        
        return {
            'total_visits': total_visits,
            'avg_duration': avg_duration,
            'total_time': total_time,
            'hourly_distribution': dict(hourly_counts),
            'longest_visit': longest_visit,
            'shortest_visit': shortest_visit,
            'visits': visits
        }
    
    def create_html_email(self, report_data: Dict[str, Any], report_date: datetime.date) -> str:
        """Create simple HTML email content focused on visits timeline."""
        
        # Color scheme
        primary_color = "#2E86AB"
        background_color = "#F8F9FA"
        
        visits = report_data['visits']
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bathroom Visits - {report_date.strftime('%B %d, %Y')}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', sans-serif;
            font-size: 16px;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: {background_color};
            color: #333;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: {primary_color};
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2rem;
            font-weight: 600;
            letter-spacing: -0.02em;
        }}
        .header .date {{
            font-size: 1rem;
            font-weight: 400;
            opacity: 0.9;
            margin-top: 8px;
        }}
        .summary {{
            padding: 24px;
            text-align: center;
            background: {background_color};
            margin: 20px;
            border-radius: 8px;
        }}
        .summary h2 {{
            color: {primary_color};
            margin: 0 0 8px 0;
            font-size: 1.5rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}
        .summary p {{
            margin: 0;
            font-size: 0.9rem;
            color: #666;
            font-weight: 400;
        }}
        .chart-section {{
            padding: 20px;
            text-align: center;
        }}
        .chart-section h3 {{
            color: {primary_color};
            margin-bottom: 20px;
            font-size: 1.3em;
        }}
        .visits-section {{
            padding: 24px;
            margin: 20px;
        }}
        .visits-header {{
            text-align: center;
            margin-bottom: 32px;
            padding-bottom: 16px;
            border-bottom: 2px solid {primary_color};
        }}
        .visits-header h3 {{
            color: {primary_color};
            margin: 0 0 8px 0;
            font-size: 1.4rem;
            font-weight: 600;
            letter-spacing: -0.01em;
        }}
        .visits-header p {{
            color: #666;
            margin: 0;
            font-size: 0.9rem;
            font-weight: 400;
        }}
        .visits-grid {{
            display: grid;
            gap: 20px;
            margin-top: 20px;
        }}
        .visit-card {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border-left: 4px solid {primary_color};
            transition: all 0.2s ease;
        }}
        .visit-card:hover {{
            transform: translateY(-1px);
            box-shadow: 0 4px 16px rgba(0,0,0,0.12);
        }}
        .visit-card-header {{
            display: flex;
            justify-content: flex-start;
            align-items: center;
            margin-bottom: 16px;
        }}
        .visit-number {{
            background: {primary_color};
            color: white;
            padding: 8px 14px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9rem;
            letter-spacing: 0.02em;
        }}
        .visit-time-display {{
            margin-bottom: 16px;
        }}
        .time-range {{
            font-size: 1.1rem;
            font-weight: 600;
            color: {primary_color};
            margin-bottom: 4px;
            letter-spacing: -0.01em;
        }}
        .visit-date {{
            color: #666;
            font-size: 0.85rem;
            font-weight: 400;
        }}
        .visit-stats {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 16px;
            margin: 16px 0;
        }}
        .stat-label {{
            font-weight: 500;
            color: #495057;
            font-size: 0.95rem;
        }}
        .stat-value {{
            font-weight: 600;
            color: #212529;
            font-size: 1rem;
        }}
        @media only screen and (max-width: 600px) {{
            body {{
                font-size: 15px;
                padding: 10px;
            }}
            .container {{
                margin: 5px;
                border-radius: 8px;
            }}
            .header {{
                padding: 20px;
            }}
            .header h1 {{
                font-size: 1.6rem;
            }}
            .header .date {{
                font-size: 0.9rem;
            }}
            .summary {{
                margin: 10px;
                padding: 16px;
            }}
            .summary h2 {{
                font-size: 1.3rem;
            }}
            .summary p {{
                font-size: 0.85rem;
            }}
            .chart-section {{
                padding: 15px;
            }}
            .visits-section {{
                margin: 10px;
                padding: 16px;
            }}
            .visits-header h3 {{
                font-size: 1.2rem;
            }}
            .visits-header p {{
                font-size: 0.85rem;
            }}
            .visit-card {{
                padding: 16px;
            }}
            .visit-card-header {{
                flex-direction: row;
                align-items: center;
                gap: 0px;
                margin-bottom: 12px;
            }}
            .visit-number {{
                padding: 6px 10px;
                font-size: 0.85rem;
            }}
            .time-range {{
                font-size: 1rem;
            }}
            .visit-date {{
                font-size: 0.8rem;
            }}
            .visit-stats {{
                gap: 12px;
            }}
            .stat-item {{
                padding: 10px;
            }}
            .stat-label {{
                font-size: 0.7rem;
            }}
            .stat-value {{
                font-size: 0.9rem;
            }}
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.85rem;
            font-weight: 400;
            line-height: 1.5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚽 Bathroom Visits</h1>
            <div class="date">{report_date.strftime('%A, %B %d, %Y')}</div>
        </div>
        
        <div class="summary">
            <h2>Total Visits: {report_data['total_visits']}</h2>
            <p>Monitoring period: {self._format_time_display(Config.MOTION_START_TIME)} - {self._format_time_display(Config.MOTION_END_TIME)} PST</p>
        </div>
        """
        
        # Skip timeline - go directly to visit details which are more useful
        
        # Add enhanced visit details section
        if visits:
            html_content += f"""
        <div class="visits-section">
            <div class="visits-header">
                <h3>📋 Bathroom Visits Details</h3>
                <p>All visits during monitoring period</p>
            </div>
            <div class="visits-grid">
            """
            
            for i, visit in enumerate(sorted(visits, key=lambda v: v.visit_start), 1):
                visit_start_pst = to_pst(visit.visit_start)
                visit_end_pst = to_pst(visit.visit_end)
                duration_min = visit.duration_seconds / 60
                
                html_content += f"""
                <div class="visit-card">
                    <div class="visit-card-header">
                        <span class="visit-number">#{i}</span>
                    </div>
                    <div class="visit-time-display">
                        <div class="time-range">
                            <strong>{format_pst(visit_start_pst, '%H:%M')} - {format_pst(visit_end_pst, '%H:%M')} PST</strong>
                        </div>
                        <div class="visit-date">
                            {format_pst(visit_start_pst, '%A, %B %d')}
                        </div>
                    </div>
                    <div class="visit-stats">
                        <table style="width: 100%; border-collapse: collapse;">
                            <tr>
                                <td style="padding: 12px 0; border-bottom: 1px solid #eee;">
                                    <span class="stat-label">Duration</span>
                                </td>
                                <td style="padding: 12px 0; border-bottom: 1px solid #eee; text-align: right;">
                                    <span class="stat-value">{duration_min:.1f} min</span>
                                </td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0;">
                                    <span class="stat-label">Motion Events</span>
                                </td>
                                <td style="padding: 12px 0; text-align: right;">
                                    <span class="stat-value">{visit.event_count}</span>
                                </td>
                            </tr>
                        </table>
                    </div>
                </div>
                """
            
            html_content += "</div></div>"
        
        html_content += f"""
        <div class="footer">
            <p>Generated automatically by Bathroom Health Monitor</p>
            <p>All times displayed in Pacific Standard Time (PST/PDT)</p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def send_report(self, to_email: str, report_data: Dict[str, Any], report_date: datetime.date) -> bool:
        """Send the bathroom visit report via email."""
        try:
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚽 Bathroom Health Report - {report_date.strftime('%m/%d/%Y')}"
            msg['From'] = self.email
            msg['To'] = to_email
            
            # Create HTML content
            html_content = self.create_html_email(report_data, report_date)
            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            return True
            
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
