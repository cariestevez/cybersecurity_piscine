# Create a virtual environment
python3 -m venv cybersecurity_env

# Activate
source cybersecurity_env/bin/activate

# You're now in the virtual environment
# Install packages specific to this project
pip install requests
pip install exifread
pip install beautifulsoup4

# Exit virtual environment
deactivate