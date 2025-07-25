#!/bin/bash

# Apna Swasthya Saathi Backend Runner Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Python version
check_python() {
    if command_exists python3; then
        PYTHON_CMD="python3"
    elif command_exists python; then
        PYTHON_CMD="python"
    else
        print_error "Python is not installed"
        exit 1
    fi
    
    # Check Python version
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)
    
    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
        print_error "Python 3.8 or higher is required. Found: $PYTHON_VERSION"
        exit 1
    fi
    
    print_success "Python $PYTHON_VERSION detected"
}

# Function to setup virtual environment
setup_venv() {
    if [ ! -d "venv" ]; then
        print_status "Creating virtual environment..."
        $PYTHON_CMD -m venv venv
        print_success "Virtual environment created"
    else
        print_status "Virtual environment already exists"
    fi
}

# Function to activate virtual environment
activate_venv() {
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    elif [ -f "venv/Scripts/activate" ]; then
        source venv/Scripts/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment activation script not found"
        exit 1
    fi
}

# Function to install dependencies
install_deps() {
    if [ -f "requirements.txt" ]; then
        print_status "Installing dependencies..."
        pip install --upgrade pip
        pip install -r requirements.txt
        print_success "Dependencies installed"
    else
        print_error "requirements.txt not found"
        exit 1
    fi
}

# Function to setup environment file
setup_env() {
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success ".env file created from example"
            print_warning "Please update .env file with your configuration"
        else
            print_error ".env.example not found"
            exit 1
        fi
    else
        print_status ".env file already exists"
    fi
}

# Function to create directories
create_dirs() {
    mkdir -p uploads logs
    print_success "Required directories created"
}

# Function to run the application
run_app() {
    print_status "Starting Apna Swasthya Saathi Backend..."
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                 Apna Swasthya Saathi API                     ║"
    echo "║              AI-Powered Rural Healthcare                     ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    
    $PYTHON_CMD app.py
}

# Function to run tests
run_tests() {
    print_status "Running tests..."
    if [ -d "tests" ]; then
        $PYTHON_CMD -m pytest tests/ -v
    else
        print_warning "No tests directory found"
    fi
}

# Function to show help
show_help() {
    echo "Apna Swasthya Saathi Backend Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup     Setup the development environment"
    echo "  run       Run the application (default)"
    echo "  test      Run tests"
    echo "  clean     Clean up generated files"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup   # Setup environment and dependencies"
    echo "  $0 run     # Run the application"
    echo "  $0 test    # Run tests"
}

# Function to clean up
clean_up() {
    print_status "Cleaning up..."
    
    # Remove virtual environment
    if [ -d "venv" ]; then
        rm -rf venv
        print_success "Virtual environment removed"
    fi
    
    # Remove cache files
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    
    # Remove logs
    if [ -d "logs" ]; then
        rm -rf logs
        print_success "Logs directory removed"
    fi
    
    print_success "Cleanup completed"
}

# Function to setup everything
setup_all() {
    print_status "Setting up Apna Swasthya Saathi Backend..."
    
    check_python
    setup_venv
    activate_venv
    install_deps
    setup_env
    create_dirs
    
    print_success "Setup completed successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update .env file with your configuration"
    echo "2. Run: $0 run"
}

# Main script logic
case "${1:-run}" in
    "setup")
        setup_all
        ;;
    "run")
        check_python
        if [ ! -d "venv" ]; then
            print_warning "Virtual environment not found. Running setup first..."
            setup_all
        fi
        activate_venv
        run_app
        ;;
    "test")
        check_python
        activate_venv
        run_tests
        ;;
    "clean")
        clean_up
        ;;
    "help"|"-h"|"--help")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac