#!/bin/bash
# ============================================
# OpenGov AI Assistant - Setup Script
# Automated installation and configuration
# ============================================

set -e

echo "============================================"
echo "  OpenGov AI Assistant - Setup Script"
echo "============================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Python is installed
echo -e "${BLUE}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.11 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo -e "${GREEN}✓ Python $PYTHON_VERSION found${NC}"

# Check if pip is installed
echo -e "${BLUE}Checking pip installation...${NC}"
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip is not installed. Please install pip.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pip found${NC}"

# Create virtual environment
echo -e "${BLUE}Creating virtual environment...${NC}"
python3 -m venv venv
echo -e "${GREEN}✓ Virtual environment created${NC}"

# Activate virtual environment
echo -e "${BLUE}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Install dependencies
echo -e "${BLUE}Installing Python dependencies...${NC}"
cd backend
pip install -r requirements.txt
echo -e "${GREEN}✓ Dependencies installed${NC}"

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file from template...${NC}"
    cp .env.example .env
    echo -e "${GREEN}✓ .env file created${NC}"
    echo -e "${YELLOW}⚠ Please edit backend/.env and set your GEMINI_API_KEY${NC}"
fi

# Create necessary directories
echo -e "${BLUE}Creating directory structure...${NC}"
mkdir -p data/FR data/Procurement data/ECode vector_db
echo -e "${GREEN}✓ Directories created${NC}"

# Deactivate virtual environment
deactivate

echo ""
echo "============================================"
echo "  Setup Complete!"
echo "============================================"
echo ""
echo -e "${GREEN}Next Steps:${NC}"
echo ""
echo "1. Configure your environment:"
echo -e "   ${YELLOW}nano backend/.env${NC}"
echo "   - Set GEMINI_API_KEY (required)"
echo "   - Change ADMIN_TOKEN (recommended)"
echo ""
echo "2. Add PDF documents:"
echo -e "   Place your PDF files in:"
echo -e "   - ${BLUE}backend/data/FR/${NC} for Financial Regulations"
echo -e "   - ${BLUE}backend/data/Procurement/${NC} for Procurement Guidelines"
echo -e "   - ${BLUE}backend/data/ECode/${NC} for Expenditure Codes"
echo ""
echo "3. Ingest documents:"
echo -e "   ${YELLOW}cd backend && source ../venv/bin/activate && python ingest.py${NC}"
echo ""
echo "4. Start the application:"
echo -e "   ${YELLOW}cd backend && uvicorn main:app --reload --host 0.0.0.0 --port 8000${NC}"
echo ""
echo "5. Access the application:"
echo -e "   ${BLUE}http://localhost:8000${NC}"
echo ""
echo -e "${GREEN}============================================${NC}"
echo ""