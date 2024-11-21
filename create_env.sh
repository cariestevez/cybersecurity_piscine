# Exit the current virtual environment
deactivate

# Remove broken virtual environment
rm -rf cybersecurity_env

# Create a virtual environment
python3 -m venv cybersecurity_env

# Activate
source cybersecurity_env/bin/activate

# Update pip
pip install --upgrade pip

# Install packages specific to this project
pip install requests
pip install exifread
pip install beautifulsoup4
pip install cryptography
pip install Fernet
pip install colorama

# Exit virtual environment
deactivate