#!/bin/bash

# BATLI Launcher Script
# This script installs (if necessary) and runs the BATLI Flask application.

# Update PATH to include standard directories
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"

# Function to check for command existence
command_exists () {
    command -v "$1" &> /dev/null ;
}

echo "Please leave this window open while BATLI is running."
sleep 2

echo "Checking system..."
sleep 1

# Detect OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS_TYPE="Linux"
else
    echo "Operating system not supported by this script."
    exit 1
fi

echo "$OS_TYPE detected."

# Function to check dependencies
check_dependencies() {
    if [[ "$OS_TYPE" == "macOS" ]]; then
        # Check for Homebrew
        if ! command_exists brew ; then
            echo "Homebrew not found. Please install Homebrew from https://brew.sh/ and rerun the application."
            exit 1
        fi
        # Check for Python 3
        if ! command_exists python3 ; then
            echo "Python 3 not found. Please install Python 3 and rerun the application."
            exit 1
        fi
        # Check for Git
        if ! command_exists git ; then
            echo "Git not found. Installing Git via Homebrew..."
            brew install git
        fi
    elif [[ "$OS_TYPE" == "Linux" ]]; then
        # Check for Python 3
        if ! command_exists python3 ; then
            echo "Python 3 not found. Please install Python 3 (e.g., sudo apt install python3) and rerun the application."
            exit 1
        fi
        # Check for pip3
        if ! command_exists pip3 ; then
            echo "pip3 not found. Please install pip3 (e.g., sudo apt install python3-pip) and rerun the application."
            exit 1
        fi
        # Check for Git
        if ! command_exists git ; then
            echo "Git not found. Please install Git (e.g., sudo apt install git) and rerun the application."
            exit 1
        fi
        # Check for lsof
        if ! command_exists lsof ; then
            echo "lsof not found. Please install lsof (e.g., sudo apt install lsof) and rerun the application."
            exit 1
        fi
        # Check for nc (netcat)
        if ! command_exists nc ; then
            echo "nc (netcat) not found. Please install netcat (e.g., sudo apt install netcat) and rerun the application."
            exit 1
        fi
        # Check for xdg-open or gnome-open
        if ! command_exists xdg-open && ! command_exists gnome-open ; then
            echo "xdg-open or gnome-open not found. Please install xdg-utils or GNOME utilities to open the browser automatically."
            # We won't exit here, but the script will inform the user later.
        fi
    fi
}

# Check dependencies
check_dependencies

# Set BATLI directory in the user's home directory
BATLI_DIR="$HOME/BATLI"
echo "BATLI will be installed in your home directory at $BATLI_DIR."

# Check if BATLI repository exists
if [ -d "$BATLI_DIR" ]; then
    echo "BATLI repository found at $BATLI_DIR. Updating repository..."
    cd "$BATLI_DIR" || { echo "Failed to enter BATLI directory"; exit 1; }
    git pull origin main
else
    echo "Cloning the BATLI GitHub repository into $BATLI_DIR..."
    git clone https://github.com/pescoll/BATLI.git "$BATLI_DIR"
    cd "$BATLI_DIR" || { echo "Failed to enter BATLI directory"; exit 1; }
fi

# Set up virtual environment if not already set up
if [ ! -d "venv" ]; then
    echo "Setting up virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Verify that the virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    echo "Failed to activate the virtual environment."
    exit 1
fi

# Install required Python packages
echo "Checking Python dependencies..."
pip install --upgrade pip

if ! pip show flask > /dev/null 2>&1; then
    echo "Installing required Python packages..."
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    else
        pip install flask pandas seaborn matplotlib numpy werkzeug
    fi
else
    echo "Required Python packages already installed."
fi

# Kill any process using port 5001
echo "Checking for processes using port 5001..."
if lsof -i :5001 -sTCP:LISTEN -t >/dev/null ; then
    echo "Port 5001 is in use. Attempting to terminate the process..."
    lsof -i :5001 -sTCP:LISTEN -t | xargs kill -9
    echo "Process terminated."
else
    echo "Port 5001 is free."
fi

# Function to wait for the Flask app to start
wait_for_port() {
    local port=$1
    local max_attempts=60
    local attempt=1

    echo "Waiting for Flask app to start on port $port..."

    while ! nc -z localhost "$port"; do
        if [ $attempt -ge $max_attempts ]; then
            echo "Flask app did not start within expected time. Exiting."
            exit 1
        fi
        echo "Attempt $attempt/$max_attempts: Flask app not ready yet. Retrying in 1 second..."
        attempt=$((attempt+1))
        sleep 1
    done

    echo "Flask app is now running on port $port."
}

# Start the Flask application in the background
echo "Starting BATLI..."

# Set environment variables
export FLASK_APP=app.py
export FLASK_ENV=development

# Run Flask app in the background
python -m flask run --port=5001 &
FLASK_PID=$!

# Wait for the Flask app to start
wait_for_port 5001

echo "Please leave this window open while BATLI is running."
sleep 1

# Open the web browser to the Flask app URL
echo "Opening the web browser to http://localhost:5001"

# Detect OS and open browser accordingly
if [[ "$OS_TYPE" == "macOS" ]]; then
    # macOS
    open http://localhost:5001
elif [[ "$OS_TYPE" == "Linux" ]]; then
    # Linux
    if command_exists xdg-open ; then
        xdg-open http://localhost:5001
    elif command_exists gnome-open ; then
        gnome-open http://localhost:5001
    else
        echo "Could not detect a command to open the browser. Please open http://localhost:5001 manually."
    fi
fi

# Wait for the Flask process to finish
wait $FLASK_PID
