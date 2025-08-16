#!/bin/bash
# Bathroom Health Monitor - Status Check
# This script shows the current status of the bathroom health monitoring system

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
WHITE='\033[1;37m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Fun animated header
echo -e "${CYAN}${BOLD}"
echo "╔═══════════════════════════════════════════════════════╗"
echo "║  🚽 💧 BATHROOM HEALTH MONITOR - STATUS CHECK 💧 🚽  ║"
echo "╚═══════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo -e "${PURPLE}🔍 Checking system health...${NC}"
echo ""

# Check if cron jobs exist
echo -e "${BLUE}${BOLD}📅 CRON JOBS:${NC}"
if crontab -l 2>/dev/null | grep -q "Bathroom Health Monitor"; then
    echo -e "${GREEN}✅ Bathroom Health Monitor cron jobs are ${BOLD}ACTIVE${NC}"
    echo ""
    echo -e "${YELLOW}📋 Current Jobs:${NC}"
    crontab -l 2>/dev/null | grep -A1 -B1 "Bathroom Health Monitor" | sed 's/^/   /'
    echo ""
else
    echo -e "${RED}❌ No Bathroom Health Monitor cron jobs found${NC}"
    echo -e "${YELLOW}   💡 Run ${BOLD}'./setup_cron.sh'${NC}${YELLOW} to install${NC}"
    echo ""
fi

# Check database
echo -e "${BLUE}${BOLD}🗄️  DATABASE:${NC}"
if [ -f "motion_events.db" ]; then
    echo -e "${GREEN}✅ Database file exists: ${BOLD}motion_events.db${NC}"
    echo -e "${CYAN}   👤 Owner: ${BOLD}$(ls -l motion_events.db | awk '{print $3":"$4}')${NC}"
    echo -e "${CYAN}   🔒 Permissions: ${BOLD}$(ls -l motion_events.db | awk '{print $1}')${NC}"
    echo -e "${CYAN}   📏 Size: ${BOLD}$(ls -lh motion_events.db | awk '{print $5}')${NC}"
else
    echo -e "${RED}❌ Database file not found${NC}"
fi
echo ""

# Check log files
echo -e "${BLUE}${BOLD}📄 LOG FILES:${NC}"
for log_file in "/tmp/bathroom_motion.log" "/tmp/bathroom_report.log"; do
    if [ -f "$log_file" ]; then
        # Choose emoji based on log type
        if [[ "$log_file" == *"motion"* ]]; then
            log_emoji="🌙"
        else
            log_emoji="📊"
        fi
        echo -e "${GREEN}✅ ${log_emoji} ${BOLD}$(basename $log_file)${NC}${GREEN} exists${NC}"
        if [ -s "$log_file" ]; then
            echo -e "${CYAN}   📝 Last activity: ${BOLD}$(tail -1 $log_file 2>/dev/null | head -c 50)...${NC}"
        else
            echo -e "${YELLOW}   📭 (empty file)${NC}"
        fi
    else
        if [[ "$log_file" == *"motion"* ]]; then
            log_emoji="🌙"
        else
            log_emoji="📊"
        fi
        echo -e "${RED}❌ ${log_emoji} ${BOLD}$(basename $log_file)${NC}${RED} not found${NC}"
    fi
done
echo ""

# Check configuration
echo -e "${BLUE}${BOLD}⚙️  CONFIGURATION:${NC}"
if [ -f "src/config.py" ]; then
    echo -e "${GREEN}✅ Configuration file exists${NC}"
    
    # Check key settings (safely)
    if grep -q "your_email@gmail.com" src/config.py; then
        echo -e "${YELLOW}⚠️  📧 Email settings need configuration (still using defaults)${NC}"
        echo -e "${CYAN}   💡 Edit: ${BOLD}nano src/config.py${NC}"
    else
        echo -e "${GREEN}✅ 📧 Email settings appear to be configured${NC}"
    fi
    
    if grep -q "recipient@gmail.com" src/config.py; then
        echo -e "${YELLOW}⚠️  📬 Report recipient needs configuration (still using defaults)${NC}"
        echo -e "${CYAN}   💡 Edit: ${BOLD}nano src/config.py${NC}"
    else
        echo -e "${GREEN}✅ 📬 Report recipient appears to be configured${NC}"
    fi
    
    if grep -q "your_app_password" src/config.py; then
        echo -e "${YELLOW}⚠️  🔑 Gmail App Password needs configuration${NC}"
        echo -e "${CYAN}   💡 Edit: ${BOLD}nano src/config.py${NC}"
    else
        echo -e "${GREEN}✅ 🔑 Gmail App Password appears to be configured${NC}"
    fi
else
    echo -e "${RED}❌ Configuration file not found${NC}"
fi
echo ""

# Check Python dependencies
echo -e "${BLUE}${BOLD}🐍 DEPENDENCIES:${NC}"
if python3 -c "import pytz, sqlalchemy, dotenv" 2>/dev/null; then
    echo -e "${GREEN}✅ 📦 Required Python packages are ${BOLD}INSTALLED${NC}"
else
    echo -e "${YELLOW}⚠️  📦 Some Python packages may be missing${NC}"
    echo -e "${CYAN}   💡 Run: ${BOLD}pip install -r requirements.txt${NC}"
fi
echo ""

# Show next scheduled runs
echo -e "${BLUE}${BOLD}⏰ NEXT SCHEDULED RUNS:${NC}"
if crontab -l 2>/dev/null | grep -q "bathroom_scheduler.py"; then
    echo -e "${GREEN}🌙 Motion Detection: ${BOLD}Tonight at 12:30 AM PST${NC}"
    echo -e "${GREEN}📊 Report Generation: ${BOLD}Tomorrow at 9:00 AM PST${NC}"
else
    echo -e "${RED}❌ No jobs scheduled${NC}"
fi
echo ""

# Quick commands
echo -e "${PURPLE}${BOLD}🔧 QUICK COMMANDS:${NC}"
echo -e "${WHITE}   📄 View logs:        ${BOLD}tail -f /tmp/bathroom_motion.log${NC}"
echo -e "${WHITE}   🧪 Test report:      ${BOLD}python bathroom_scheduler.py 2${NC}"
echo -e "${WHITE}   📧 Test email:       ${BOLD}python test_email.py${NC}"
echo -e "${WHITE}   ⚙️  Setup cron:       ${BOLD}./setup_cron.sh${NC}"
echo -e "${WHITE}   🗑️  Remove cron:      ${BOLD}./remove_cron.sh${NC}"
echo -e "${WHITE}   📝 Configure:        ${BOLD}nano src/config.py${NC}"
echo ""

# Overall system health summary
echo -e "${CYAN}${BOLD}╔═══════════════════════════════════════════════════════╗${NC}"
if crontab -l 2>/dev/null | grep -q "bathroom_scheduler.py" && [ -f "motion_events.db" ] && python3 -c "import pytz, sqlalchemy, dotenv" 2>/dev/null; then
    echo -e "${CYAN}${BOLD}║${NC} ${GREEN}${BOLD}🎉 SYSTEM STATUS: HEALTHY & READY FOR MONITORING! 🎉${NC} ${CYAN}${BOLD}║${NC}"
elif [ -f "motion_events.db" ] && python3 -c "import pytz, sqlalchemy, dotenv" 2>/dev/null; then
    echo -e "${CYAN}${BOLD}║${NC} ${YELLOW}${BOLD}⚠️  SYSTEM STATUS: READY - SETUP AUTOMATION! ⚠️${NC}     ${CYAN}${BOLD}║${NC}"
else
    echo -e "${CYAN}${BOLD}║${NC} ${RED}${BOLD}🔧 SYSTEM STATUS: NEEDS CONFIGURATION 🔧${NC}           ${CYAN}${BOLD}║${NC}"
fi
echo -e "${CYAN}${BOLD}╚═══════════════════════════════════════════════════════╝${NC}"
