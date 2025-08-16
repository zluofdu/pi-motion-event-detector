#!/bin/bash
# Bathroom Health Monitor - Remove Cron Jobs
# This script removes the automated scheduling for bathroom health monitoring

echo "🗑️  Removing Bathroom Health Monitor Cron Jobs"

# Check if cron jobs exist
if crontab -l 2>/dev/null | grep -q "Bathroom Health Monitor"; then
    echo "📋 Found existing cron jobs:"
    echo ""
    crontab -l 2>/dev/null | grep -A1 -B1 "Bathroom Health Monitor"
    echo ""
    
    # Ask for confirmation
    read -p "Are you sure you want to remove these cron jobs? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🚮 Removing bathroom health monitor cron jobs..."
        
        # Remove bathroom monitor jobs while preserving other cron jobs
        crontab -l 2>/dev/null | grep -v "Bathroom Health Monitor" | grep -v "bathroom_scheduler.py" > /tmp/cleaned_crontab
        
        # Install the cleaned crontab
        crontab /tmp/cleaned_crontab
        rm /tmp/cleaned_crontab
        
        echo "✅ Cron jobs removed successfully!"
        echo ""
        
        # Show remaining cron jobs (if any)
        if crontab -l 2>/dev/null | grep -q "."; then
            echo "📋 Remaining cron jobs:"
            crontab -l
        else
            echo "📋 No cron jobs remaining"
        fi
        
        echo ""
        echo "🧹 Cleanup options:"
        echo "  - Log files are still available at:"
        echo "    /tmp/bathroom_motion.log"
        echo "    /tmp/bathroom_report.log"
        echo ""
        read -p "Do you want to remove log files too? (y/N): " -n 1 -r
        echo
        
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            rm -f /tmp/bathroom_motion.log /tmp/bathroom_report.log
            echo "🗑️  Log files removed"
        else
            echo "📄 Log files preserved"
        fi
        
    else
        echo "❌ Operation cancelled"
        exit 0
    fi
else
    echo "ℹ️  No Bathroom Health Monitor cron jobs found"
    echo ""
    echo "📋 Current cron jobs:"
    if crontab -l 2>/dev/null | grep -q "."; then
        crontab -l
    else
        echo "  (none)"
    fi
fi

echo ""
echo "✨ Done!"
