Run below commands 

# Linux (Ubuntu)
sudo apt-get update
sudo apt-get install libjpeg-dev zlib1g-dev libfreetype6-dev pkg-config
python3 -m venv .venv
source .venv/bin/activate
pip install Pillow<9.6.0  # Try a specific version first to test
pip install -r requirements.txt #Try again with rest of the requirements
