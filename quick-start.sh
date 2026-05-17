#!/bin/bash
# ============================================
# OpenGov AI Assistant - Quick Start Script
# Automated deployment for tharshan.lk
# ============================================

echo "🚀 OpenGov AI Assistant - Quick Start"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker and Docker Compose are installed${NC}"

# Check if .env file exists
if [ ! -f "backend/.env" ]; then
    echo -e "${YELLOW}⚠️  Creating .env file from template...${NC}"
    cp backend/.env.example backend/.env
    echo -e "${YELLOW}⚠️  Please edit backend/.env and set your GEMINI_API_KEY and ADMIN_TOKEN${NC}"
    echo ""
    read -p "Press Enter after you've updated the .env file..."
fi

# Check if SSL certificates exist
if [ ! -f "ssl/certificate.crt" ] || [ ! -f "ssl/private.key" ]; then
    echo -e "${YELLOW}⚠️  Generating SSL certificates...${NC}"
    chmod +x ssl/generate-ssl.sh
    ./ssl/generate-ssl.sh
fi

echo ""
echo -e "${GREEN}✅ All prerequisites are ready${NC}"
echo ""

# Ask user for deployment type
echo "Select deployment type:"
echo "1) Development (without SSL, port 8000)"
echo "2) Production (with SSL, ports 80/443)"
read -p "Enter choice [1-2]: " deployment_type

if [ "$deployment_type" = "1" ]; then
    echo ""
    echo -e "${YELLOW}🔧 Starting development environment...${NC}"
    docker-compose up -d
    
    echo ""
    echo -e "${GREEN}✅ Development server started!${NC}"
    echo ""
    echo "📱 Access the application:"
    echo "   http://localhost:8000"
    echo ""
    echo "🔍 Check health:"
    echo "   curl http://localhost:8000/health"
    echo ""
elif [ "$deployment_type" = "2" ]; then
    echo ""
    echo -e "${YELLOW}🔧 Starting production environment...${NC}"
    docker-compose --profile production up -d
    
    echo ""
    echo -e "${GREEN}✅ Production server started!${NC}"
    echo ""
    echo "📱 Access the application:"
    echo "   https://tharshan.lk"
    echo "   http://tharshan.lk (redirects to HTTPS)"
    echo ""
    echo "🔍 Check health:"
    echo "   curl https://tharshan.lk/health -k"
    echo ""
else
    echo -e "${RED}❌ Invalid choice. Please run the script again.${NC}"
    exit 1
fi

echo "📊 View logs:"
echo "   docker-compose logs -f"
echo ""
echo "⏹️  Stop services:"
echo "   docker-compose down"
echo ""
echo -e "${GREEN}🎉 Deployment complete!${NC}"