#!/bin/bash

# HMO Analyser API Startup Script
# This script validates configuration and starts the API with proper error handling

set -e  # Exit on any error

echo "🚀 HMO Analyser API Startup Script"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if Python is installed
echo "🔍 Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    print_error "Python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_status "Python $PYTHON_VERSION found"

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    print_error "pip3 is not installed. Please install pip."
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_warning "Virtual environment not found. Creating one..."
    python3 -m venv venv
    print_status "Virtual environment created"
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate
print_status "Virtual environment activated"

# Upgrade pip
echo "📦 Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install requirements
echo "📦 Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt > /dev/null 2>&1
    print_status "Dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi

# Validate configuration
echo "🔍 Validating configuration..."
python3 -c "
import sys
sys.path.append('.')

try:
    from config_validator import validate_and_setup_config
    if not validate_and_setup_config():
        sys.exit(1)
except ImportError:
    # Fallback validation
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    if not os.getenv('DATABASE_URL'):
        print('❌ DATABASE_URL not found in environment')
        print('💡 Create a .env file with your database URL')
        print('Example: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname')
        sys.exit(1)
    else:
        print('✅ Configuration looks good')
"

if [ $? -ne 0 ]; then
    print_error "Configuration validation failed"
    exit 1
fi

# Check database connectivity
echo "🔍 Testing database connection..."
python3 -c "
from database import test_connection
if not test_connection():
    print('❌ Database connection failed')
    exit(1)
else:
    print('✅ Database connection successful')
"

if [ $? -ne 0 ]; then
    print_error "Database connection test failed"
    exit 1
fi

# Create exports directory
echo "📁 Setting up exports directory..."
mkdir -p exports
print_status "Exports directory ready"

# Check for required directories
if [ ! -d "modules" ]; then
    print_error "modules directory not found"
    exit 1
fi

# Start the API
echo ""
echo "🚀 Starting HMO Analyser API..."
echo "=================================="
echo ""
print_status "API will be available at: http://localhost:8000"
print_status "API documentation: http://localhost:8000/docs"
print_status "Health check: http://localhost:8000/api/health"
echo ""
print_warning "Press Ctrl+C to stop the server"
echo ""

# Start with proper error handling
exec python3 main.py