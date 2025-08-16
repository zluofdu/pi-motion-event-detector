import smtplib
import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from io import BytesIO
import base64
from collections import defaultdict
import statistics
from src.models.bathroom_visit import BathroomVisit
from src.timezone_utils import to_pst, format_pst, PST

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
    
    def create_charts(self, report_data: Dict[str, Any]) -> str:
        """Create beautiful charts and return as base64 encoded image."""
        if report_data['total_visits'] == 0:
            return ""
        
        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        fig.suptitle('Bathroom Visit Analysis Dashboard', fontsize=16, fontweight='bold')
        
        # 1. Hourly Distribution Bar Chart
        hours = list(range(24))
        counts = [report_data['hourly_distribution'].get(h, 0) for h in hours]
        
        bars = ax1.bar(hours, counts, color='skyblue', alpha=0.7, edgecolor='navy')
        ax1.set_title('Visits by Hour of Day', fontweight='bold')
        ax1.set_xlabel('Hour')
        ax1.set_ylabel('Number of Visits')
        ax1.set_xticks(range(0, 24, 2))
        ax1.grid(True, alpha=0.3)
        
        # Highlight peak hours
        if counts:
            max_count = max(counts)
            for i, bar in enumerate(bars):
                if counts[i] == max_count:
                    bar.set_color('orange')
        
        # 2. Visit Duration Timeline
        visits = report_data['visits']
        if visits:
            # Convert all times to PST for consistent display
            times = [to_pst(v.visit_start) for v in visits]
            durations = [v.duration_seconds / 60 for v in visits]  # Convert to minutes
            
            scatter = ax2.scatter(times, durations, c=durations, cmap='viridis', alpha=0.7, s=60)
            ax2.set_title('Visit Duration Timeline (PST)', fontweight='bold')
            ax2.set_xlabel('Time (PST)')
            ax2.set_ylabel('Duration (minutes)')
            
            # Format x-axis for PST times
            ax2.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M', tz=PST))
            ax2.xaxis.set_major_locator(mdates.HourLocator(interval=2))
            plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)
            
            # Add colorbar
            cbar = plt.colorbar(scatter, ax=ax2)
            cbar.set_label('Duration (minutes)')
            ax2.grid(True, alpha=0.3)
        
        # 3. Duration Distribution Histogram
        if visits:
            durations_min = [v.duration_seconds / 60 for v in visits]
            ax3.hist(durations_min, bins=10, color='lightgreen', alpha=0.7, edgecolor='darkgreen')
            ax3.set_title('Duration Distribution', fontweight='bold')
            ax3.set_xlabel('Duration (minutes)')
            ax3.set_ylabel('Frequency')
            ax3.axvline(report_data['avg_duration'] / 60, color='red', linestyle='--', 
                       label=f'Average: {report_data["avg_duration"]/60:.1f} min')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 4. Summary Statistics (Text)
        ax4.axis('off')
        stats_text = f"""
📊 SUMMARY STATISTICS
        
Total Visits: {report_data['total_visits']}
Average Duration: {report_data['avg_duration']/60:.1f} minutes
Total Time: {report_data['total_time']/60:.1f} minutes

🏆 RECORDS
Longest Visit: {report_data['longest_visit'].duration_seconds/60:.1f} min
  at {format_pst(report_data['longest_visit'].visit_start, '%H:%M %Z')}

Shortest Visit: {report_data['shortest_visit'].duration_seconds/60:.1f} min
  at {format_pst(report_data['shortest_visit'].visit_start, '%H:%M %Z')}

💡 INSIGHTS
Peak Hour: {max(report_data['hourly_distribution'], key=report_data['hourly_distribution'].get) if report_data['hourly_distribution'] else 'N/A'}:00 PST
Visit Frequency: {report_data['total_visits']/8:.1f} visits/hour avg
        """
        
        ax4.text(0.05, 0.95, stats_text, transform=ax4.transAxes, fontsize=12,
                verticalalignment='top', fontfamily='monospace',
                bbox=dict(boxstyle="round,pad=0.5", facecolor="lightblue", alpha=0.8))
        
        # Adjust layout
        plt.tight_layout()
        
        # Convert to base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', dpi=150, bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.getvalue()).decode()
        plt.close()
        
        return image_base64
    
    def create_html_email(self, report_data: Dict[str, Any], chart_image: str, report_date: datetime.date) -> str:
        """Create beautiful HTML email content."""
        
        # Color scheme
        primary_color = "#2E86AB"
        secondary_color = "#A23B72"
        accent_color = "#F18F01"
        background_color = "#F8F9FA"
        
        # Determine health status
        visit_count = report_data['total_visits']
        if visit_count >= 6:
            health_status = "🟢 Excellent"
            health_color = "#28a745"
        elif visit_count >= 4:
            health_status = "🟡 Good"
            health_color = "#ffc107"
        elif visit_count >= 2:
            health_status = "🟠 Fair"
            health_color = "#fd7e14"
        else:
            health_status = "🔴 Concerning"
            health_color = "#dc3545"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bathroom Visit Report - {report_date.strftime('%B %d, %Y')}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: {background_color};
            color: #333;
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
            background: linear-gradient(135deg, {primary_color}, {secondary_color});
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.2em;
            font-weight: 300;
        }}
        .header .date {{
            font-size: 1.1em;
            opacity: 0.9;
            margin-top: 10px;
        }}
        .health-status {{
            background: white;
            margin: 20px;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-left: 5px solid {health_color};
        }}
        .health-status h2 {{
            color: {health_color};
            margin: 0 0 10px 0;
            font-size: 1.5em;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 20px;
        }}
        .stat-card {{
            background: {background_color};
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border-top: 4px solid {accent_color};
        }}
        .stat-value {{
            font-size: 2em;
            font-weight: bold;
            color: {primary_color};
            margin: 0;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
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
        .chart-image {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .recommendations {{
            background: #e8f4f8;
            margin: 20px;
            padding: 20px;
            border-radius: 8px;
            border-left: 5px solid {primary_color};
        }}
        .recommendations h3 {{
            color: {primary_color};
            margin-top: 0;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .emoji {{
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span class="emoji">🚽</span> Bathroom Visit Report</h1>
            <div class="date">{report_date.strftime('%A, %B %d, %Y')}</div>
        </div>
        
        <div class="health-status">
            <h2>Health Status: {health_status}</h2>
            <p>Based on visit frequency and patterns</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{report_data['total_visits']}</div>
                <div class="stat-label">Total Visits</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report_data['avg_duration']/60:.1f}</div>
                <div class="stat-label">Avg Duration (min)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report_data['total_time']/60:.0f}</div>
                <div class="stat-label">Total Time (min)</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{report_data['total_visits']/8:.1f}</div>
                <div class="stat-label">Visits per Hour</div>
            </div>
        </div>
        """
        
        if chart_image:
            html_content += f"""
        <div class="chart-section">
            <h3><span class="emoji">📊</span> Visual Analysis Dashboard</h3>
            <img src="data:image/png;base64,{chart_image}" alt="Bathroom Visit Charts" class="chart-image">
        </div>
            """
        
        # Add recommendations based on data
        recommendations = self._generate_recommendations(report_data)
        if recommendations:
            html_content += f"""
        <div class="recommendations">
            <h3><span class="emoji">💡</span> Health Insights & Recommendations</h3>
            {recommendations}
        </div>
            """
        
        html_content += f"""
        <div class="footer">
            <p>Generated automatically by Bathroom Health Monitor</p>
            <p>Report covers sleep period: 12:30 AM - 8:00 AM PST</p>
            <p>All times displayed in Pacific Standard Time (PST/PDT)</p>
            <p><small>This report is for health monitoring purposes. Consult a healthcare professional for medical concerns.</small></p>
        </div>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def _generate_recommendations(self, report_data: Dict[str, Any]) -> str:
        """Generate health recommendations based on visit patterns."""
        recommendations = []
        visit_count = report_data['total_visits']
        avg_duration = report_data['avg_duration'] / 60  # Convert to minutes
        
        # Visit frequency recommendations
        if visit_count < 2:
            recommendations.append("🔴 <strong>Low visit frequency:</strong> Consider increasing fluid intake before bedtime and monitoring for potential constipation.")
        elif visit_count > 8:
            recommendations.append("🟡 <strong>High visit frequency:</strong> Frequent nighttime visits may indicate overhydration or potential health issues. Consider consulting a healthcare provider.")
        else:
            recommendations.append("✅ <strong>Normal visit frequency:</strong> Your nighttime bathroom visits are within a healthy range.")
        
        # Duration recommendations
        if avg_duration > 10:
            recommendations.append("⏱️ <strong>Extended visit duration:</strong> Longer visits may indicate digestive issues or other concerns worth monitoring.")
        elif avg_duration < 1:
            recommendations.append("⚡ <strong>Very brief visits:</strong> Quick visits suggest good efficiency and health.")
        
        # Pattern recommendations
        hourly_dist = report_data['hourly_distribution']
        if hourly_dist:
            peak_hour = max(hourly_dist, key=hourly_dist.get)
            if peak_hour <= 2:
                recommendations.append("🌙 <strong>Early night pattern:</strong> Most visits occur soon after bedtime, which is normal.")
            elif peak_hour >= 6:
                recommendations.append("🌅 <strong>Early morning pattern:</strong> Most visits near wake time, indicating good sleep quality.")
        
        return "<ul>" + "".join(f"<li>{rec}</li>" for rec in recommendations) + "</ul>" if recommendations else ""
    
    def send_report(self, to_email: str, report_data: Dict[str, Any], report_date: datetime.date) -> bool:
        """Send the bathroom visit report via email."""
        try:
            # Generate chart
            chart_image = self.create_charts(report_data)
            
            # Create email
            msg = MIMEMultipart('alternative')
            msg['Subject'] = f"🚽 Bathroom Health Report - {report_date.strftime('%m/%d/%Y')}"
            msg['From'] = self.email
            msg['To'] = to_email
            
            # Create HTML content
            html_content = self.create_html_email(report_data, chart_image, report_date)
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
