#!/bin/bash

# VitaNips Notification System - Service Startup Script
# This script helps you start all required services for the notification system

echo "🚀 VitaNips Notification System - Service Startup"
echo "=================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "env" ]; then
    echo -e "${RED}❌ Virtual environment not found!${NC}"
    echo "Run: python -m venv env"
    exit 1
fi

# Activate virtual environment
echo -e "${YELLOW}📦 Activating virtual environment...${NC}"
source env/bin/activate

# Check if Redis is running
echo -e "${YELLOW}🔍 Checking Redis...${NC}"
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${RED}❌ Redis is not running!${NC}"
    echo "Start Redis with: brew services start redis"
    echo "Or: redis-server"
    exit 1
else
    echo -e "${GREEN}✅ Redis is running${NC}"
fi

echo ""
echo -e "${GREEN}✅ Prerequisites checked${NC}"
echo ""
echo "To start the notification system, open 3 separate terminals and run:"
echo ""
echo -e "${YELLOW}Terminal 1 - Celery Worker:${NC}"
echo "  cd VitaNips-Backend-Dev"
echo "  source env/bin/activate"
echo "  celery -A vitanips worker --loglevel=info"
echo ""
echo -e "${YELLOW}Terminal 2 - Celery Beat:${NC}"
echo "  cd VitaNips-Backend-Dev"
echo "  source env/bin/activate"
echo "  celery -A vitanips beat --loglevel=info"
echo ""
echo -e "${YELLOW}Terminal 3 - Django Server:${NC}"
echo "  cd VitaNips-Backend-Dev"
echo "  source env/bin/activate"
echo "  python manage.py runserver"
echo ""
echo -e "${GREEN}📝 Note:${NC} You can also use tmux or screen to run these in the background"
echo ""

# Ask if user wants to start services now
read -p "Do you want to start the Celery worker now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}🚀 Starting Celery worker...${NC}"
    celery -A vitanips worker --loglevel=info
fi
