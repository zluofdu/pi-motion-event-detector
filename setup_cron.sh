#!/bin/bash
# Bathroom Health Monitor - Setup Cron Jobs
# This script sets up the automated scheduling for bathroom health monitoring

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_PATH="$(which python3)"

echo "🚽 Setting up Bathroom Health Monitor Cron Jobs"
echo "Script directory: $SCRIPT_DIR"
echo "Python path: $PYTHON_PATH"

# Create the cron job entries
CRON_JOBS="
# Bathroom Health Monitor - Job 1: Motion Detection (12:30 AM - 8:00 AM PST)
30 0 * * * cd $SCRIPT_DIR && $PYTHON_PATH bathroom_scheduler.py 1 >> /tmp/bathroom_motion.log 2>&1

# Bathroom Health Monitor - Job 2: Report Generation (9:00 AM PST)
0 9 * * * cd $SCRIPT_DIR && $PYTHON_PATH bathroom_scheduler.py 2 >> /tmp/bathroom_report.log 2>&1
"

# Check if cron jobs already exist
if crontab -l 2>/dev/null | grep -q "Bathroom Health Monitor"; then
    echo "⚠️  Cron jobs already exist. Updating..."
    # Remove existing bathroom monitor jobs
    crontab -l 2>/dev/null | grep -v "Bathroom Health Monitor" | grep -v "bathroom_scheduler.py" > /tmp/new_crontab
    echo "$CRON_JOBS" >> /tmp/new_crontab
    crontab /tmp/new_crontab
    rm /tmp/new_crontab
else
    echo "📅 Adding new cron jobs..."
    # Add to existing crontab
    (crontab -l 2>/dev/null; echo "$CRON_JOBS") | crontab -
fi

echo "✅ Cron jobs installed successfully!"
echo ""
echo "📋 Scheduled Jobs:"
echo "  Job 1: Motion Detection - Daily at 12:30 AM (runs until 8:00 AM)"
echo "  Job 2: Report Generation - Daily at 9:00 AM"
echo ""
echo "📄 Log files:"
echo "  Motion detection: /tmp/bathroom_motion.log"
echo "  Report generation: /tmp/bathroom_report.log"
echo ""
echo "🔧 Configuration:"
echo "  1. Edit src/config.py to set your email settings"
echo "  2. Install dependencies: pip install -r requirements.txt"
echo "  3. Test manually: python bathroom_scheduler.py 2"
echo ""
echo "📋 To view current cron jobs: crontab -l"
echo "🗑️  To remove cron jobs: ./remove_cron.sh"
