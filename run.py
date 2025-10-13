
import logging
from src.interface import create_app

# Set up logging before starting the app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    app = create_app()
    print("🚀 Starting Flask application...")
    # The 'create_app' function sets the template path to '../templates' correctly.
    app.run(debug=True)