# src/main.py

import logging
from .interface import create_app

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Note: The 'create_app' function is imported and called by run.py