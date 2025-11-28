
import logging
from src.interface import create_app

# Set up logging before starting the app
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

app = create_app()

if __name__ == "__main__":
    
    print("🚀 Starting Flask application...")
    
    app.run(debug=True)