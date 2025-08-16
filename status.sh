#!/bin/bash
# Bathroom Health Monitor - Status Check
# This script shows the current status of the bathroom health monitoring system

echo "🚽 Bathroom Health Monitor - Status Check"
echo "========================================"
echo ""

# Check if cron jobs exist
echo "📅 CRON JOBS:"
if crontab -l 2>/dev/null | grep -q "Bathroom Health Monitor"; then
    echo "✅ Bathroom Health Monitor cron jobs are active:"
    echo ""
    crontab -l 2>/dev/null | grep -A1 -B1 "Bathroom Health Monitor"
    echo ""
else
    echo "❌ No Bathroom Health Monitor cron jobs found"
    echo "   Run './setup_cron.sh' to install"
    echo ""
fi

# Check database
echo "🗄️  DATABASE:"
if [ -f "motion_events.db" ]; then
    echo "✅ Database file exists: motion_events.db"
    echo "   Owner: $(ls -l motion_events.db | awk '{print $3":"$4}')"
    echo "   Permissions: $(ls -l motion_events.db | awk '{print $1}')"
    echo "   Size: $(ls -lh motion_events.db | awk '{print $5}')"
else
    echo "❌ Database file not found"
fi
echo ""

# Check log files
echo "📄 LOG FILES:"
for log_file in "/tmp/bathroom_motion.log" "/tmp/bathroom_report.log"; do
    if [ -f "$log_file" ]; then
        echo "✅ $(basename $log_file) exists"
        if [ -s "$log_file" ]; then
            echo "   Last activity: $(tail -1 $log_file 2>/dev/null | head -c 50)..."
        else
            echo "   (empty file)"
        fi
    else
        echo "❌ $(basename $log_file) not found"
    fi
done
echo ""

# Check configuration
echo "⚙️  CONFIGURATION:"
if [ -f "src/config.py" ]; then
    echo "✅ Configuration file exists"
    
    # Check key settings (safely)
    if grep -q "your_email@gmail.com" src/config.py; then
        echo "⚠️  Email settings need configuration (still using defaults)"
    else
        echo "✅ Email settings appear to be configured"
    fi
    
    if grep -q "recipient@gmail.com" src/config.py; then
        echo "⚠️  Report recipient needs configuration (still using defaults)"
    else
        echo "✅ Report recipient appears to be configured"
    fi
else
    echo "❌ Configuration file not found"
fi
echo ""

# Check Python dependencies
echo "🐍 DEPENDENCIES:"
if python3 -c "import pytz, sqlalchemy, matplotlib" 2>/dev/null; then
    echo "✅ Required Python packages are installed"
else
    echo "⚠️  Some Python packages may be missing"
    echo "   Run: pip install -r requirements.txt"
fi
echo ""

# Show next scheduled runs
echo "⏰ NEXT SCHEDULED RUNS:"
if crontab -l 2>/dev/null | grep -q "bathroom_scheduler.py"; then
    echo "🌙 Motion Detection: Tonight at 12:30 AM PST"
    echo "📊 Report Generation: Tomorrow at 9:00 AM PST"
else
    echo "❌ No jobs scheduled"
fi
echo ""

# Quick commands
echo "🔧 QUICK COMMANDS:"
echo "   View logs:        tail -f /tmp/bathroom_motion.log"
echo "   Test report:      python bathroom_scheduler.py 2"
echo "   Setup cron:       ./setup_cron.sh"
echo "   Remove cron:      ./remove_cron.sh"
echo "   Configure:        nano src/config.py"
echo ""
echo "✨ Status check complete!"
