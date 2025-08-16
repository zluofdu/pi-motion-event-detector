# 🚽 Motion Event Detector - Bathroom Health Monitor

A comprehensive health monitoring system that detects nighttime bathroom visits using PIR motion sensors and provides beautiful daily health reports with insights and visualizations.

## 🎯 Overview

This intelligent bathroom health monitoring system:
- **Monitors motion** from 12:30 AM to 8:00 AM PST using PIR sensors
- **Detects bathroom visits** through smart event clustering algorithms
- **Generates beautiful reports** with 4 comprehensive charts and health insights
- **Sends daily emails** with professional HTML reports at 9:00 AM PST
- **Saves all timestamps in PST** for consistent Pacific timezone tracking
- **Provides health recommendations** based on visit patterns and frequency

## 🏗️ System Architecture

### Automated Scheduling (2 Jobs)
- **Job 1**: Motion Detection (12:30 AM - 8:00 AM PST) - Nighttime monitoring
- **Job 2**: Report Generation (9:00 AM PST) - Daily analysis and email

### Core Components
- **Motion Detection**: Intelligent PIR sensor monitoring with stabilization
- **Visit Detection**: Smart clustering of motion events into bathroom visits
- **Health Analysis**: Pattern recognition and personalized recommendations
- **Email Reporting**: Beautiful HTML reports with embedded charts
- **Database Storage**: SQLAlchemy models with timezone-aware timestamps

## 📊 Features

### 🔍 **Smart Motion Detection**
- GPIO pin 4 PIR sensor integration
- Sensor stabilization to prevent false triggers
- Threading-based duration control
- PST timestamp recording
- Device ID tracking based on GPIO configuration

### 🧠 **Intelligent Visit Detection**
- Clusters motion events within configurable time windows (default: 5 minutes)
- Requires minimum 2 events to identify a bathroom visit
- Accurate timing tracking (start/end times, duration)
- Timezone-aware processing with PST timestamps

### 📈 **Beautiful Visualization & Reports**
- **4 Comprehensive Charts**:
  - 📊 Hourly visit distribution (PST hours)
  - ⏱️ Duration timeline with color-coded scatter plot
  - 📊 Duration histogram with statistics
  - 📋 Summary statistics panel with records
- **Health Status Indicators**: 🟢 Excellent / 🟡 Good / 🟠 Fair / 🔴 Concerning
- **Personalized Recommendations**: Based on visit frequency and patterns
- **Professional HTML Emails**: Responsive design with embedded charts
- **PST Timezone Display**: All times clearly labeled with Pacific timezone

### ⏰ **Automated Scheduling**
- **Cron Integration**: Easy one-command setup with `./setup_cron.sh`
- **Comprehensive Logging**: System monitoring via log files
- **Error Handling**: Robust error recovery and notification
- **Manual Testing**: Individual job execution for debugging

## 🚀 Quick Start

### 1. Hardware Setup
Connect a PIR motion sensor to your Raspberry Pi:
```
PIR Sensor → Raspberry Pi
VCC        → 5V (Pin 2)
GND        → Ground (Pin 6)  
OUT        → GPIO 4 (Pin 7)
```

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/zluofdu/pi-motion-event-detector.git
cd motion-event

# Install system dependencies
sudo apt update && sudo apt install -y python3-matplotlib python3-pip

# Install Python dependencies
pip install pytz

# Install the package
pip install -e .
```

### 3. Configuration
Edit `src/config.py` with your settings:
```python
class Config:
    # Email settings
    SMTP_SERVER = 'smtp.gmail.com'
    EMAIL_ADDRESS = 'your_email@gmail.com'
    EMAIL_PASSWORD = 'your_app_password'  # Use app-specific password
    REPORT_EMAIL = 'recipient@gmail.com'
    
    # Timezone (PST/PDT)
    TIMEZONE = 'US/Pacific'
    
    # Optional: Adjust timing and clustering
    CLUSTER_WINDOW_MINUTES = 5  # Group events within 5 minutes
```

### 4. Setup Automation
```bash
# Make setup script executable and run
chmod +x setup_cron.sh
./setup_cron.sh
```

### 5. Test the System
```bash
# Test motion detection (10 seconds)
python src/main.py --duration 10

# Test report generation
python bathroom_scheduler.py 2

# View logs
tail -f /tmp/bathroom_motion.log
tail -f /tmp/bathroom_report.log
```

## 📁 Project Structure

```
motion-event/
├── src/
│   ├── main.py                    # Motion system orchestration
│   ├── motion_detector.py         # PIR sensor handling with PST timestamps
│   ├── motion_event_dao.py        # Database operations
│   ├── bathroom_visit_detector.py # Smart visit clustering algorithm
│   ├── bathroom_reporter.py       # Beautiful email reports with charts
│   ├── timezone_utils.py          # PST timezone utilities
│   ├── config.py                  # Configuration settings
│   └── models/
│       ├── motion_event.py        # Motion event data model
│       └── bathroom_visit.py      # Bathroom visit data model
├── tests/                         # Comprehensive test suite (16 tests, 90% coverage)
├── bathroom_scheduler.py          # Main scheduler for automated jobs
├── setup_cron.sh                 # Automated cron job setup
├── requirements.txt              # Python dependencies
├── BATHROOM_README.md            # Detailed documentation
└── README.md                     # This file
```

## 🏥 Health Insights

The system provides intelligent health analysis:

### Health Status Indicators
- **🟢 Excellent**: 6+ visits (optimal hydration)
- **🟡 Good**: 4-5 visits (normal range)  
- **🟠 Fair**: 2-3 visits (monitor hydration)
- **🔴 Concerning**: <2 visits (may need attention)

### Smart Recommendations
- Visit frequency analysis
- Duration pattern insights
- Peak time identification
- Hydration suggestions
- Health trend monitoring

## ⚙️ Usage

### Manual Commands
```bash
# Start motion detection with duration
python src/main.py --duration 300  # 5 minutes

# Generate daily report
python bathroom_scheduler.py 2

# Run nighttime monitoring (until 8 AM PST)
python bathroom_scheduler.py 1
```

### Automated Operation
The system runs automatically via cron:
- **12:30 AM PST**: Start motion detection
- **8:00 AM PST**: Stop motion detection  
- **9:00 AM PST**: Generate and email daily report

### System Management
```bash
# Check system status
./status.sh

# Setup automation (one-time)
./setup_cron.sh

# Remove automation
./remove_cron.sh

# View scheduled jobs
crontab -l

# Monitor logs in real-time
tail -f /tmp/bathroom_motion.log
tail -f /tmp/bathroom_report.log
```

### Email Reports
Reports include:
- 📊 **4 Visual Charts**: Hourly distribution, duration timeline, statistics
- 🏥 **Health Status**: Color-coded health indicators
- 💡 **Smart Insights**: Personalized recommendations
- 📈 **Trend Analysis**: Patterns and statistics
- 🕐 **PST Timestamps**: All times in Pacific timezone

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific tests
pytest tests/test_motion_detector.py -v
```

**Current Status**: 16 tests, 90% coverage ✅

## 🔧 Configuration Options

### Email Settings
```python
SMTP_SERVER = 'smtp.gmail.com'     # Your SMTP server
SMTP_PORT = 587                    # SMTP port (587 for TLS)
EMAIL_ADDRESS = 'sender@gmail.com' # Sender email
EMAIL_PASSWORD = 'app_password'    # App-specific password
REPORT_EMAIL = 'recipient@gmail.com' # Report recipient
```

### Timezone & Timing
```python
TIMEZONE = 'US/Pacific'            # PST/PDT timezone
MOTION_START_TIME = '00:30'        # 12:30 AM PST
MOTION_END_TIME = '08:00'          # 8:00 AM PST
REPORT_TIME = '09:00'              # 9:00 AM PST
CLUSTER_WINDOW_MINUTES = 5         # Visit clustering window
```

## 🔧 Troubleshooting

### Common Issues

**Motion sensor not working:**
```bash
# Check GPIO permissions
sudo usermod -a -G gpio $USER
# Test sensor
python -c "from gpiozero import MotionSensor; m=MotionSensor(4); print('Sensor working!')"
```

**Email not sending:**
- Use app-specific passwords for Gmail
- Check SMTP settings for your email provider
- Verify firewall allows SMTP connections

**Cron jobs not running:**
```bash
# Check cron service
sudo systemctl status cron
# View logs
sudo tail -f /var/log/syslog | grep CRON
```

### Log Files
- Motion detection: `/tmp/bathroom_motion.log`
- Report generation: `/tmp/bathroom_report.log`
- System logs: `/var/log/syslog`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Add tests for new functionality
4. Ensure all tests pass (`pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Submit a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues or questions:
1. Check the [troubleshooting section](#-troubleshooting)
2. Review log files for error details
3. Create an issue with logs and configuration details

## 🔗 Additional Documentation

- **[BATHROOM_README.md](BATHROOM_README.md)**: Comprehensive bathroom health monitoring guide
- **[Architecture Details](docs/)**: Technical implementation details
- **[API Documentation](docs/api.md)**: Code reference and examples

---

**🚽 Stay healthy with intelligent bathroom monitoring! 🏥📊**

*Built with ❤️ for Raspberry Pi health monitoring*