🚗 Real-Time Traffic Route Optimizer
This is a Python Flask web application designed to find and compare optimal driving routes in a specified geographic area. It goes beyond simple shortest-path calculations by implementing a custom A* pathfinding algorithm that balances travel time, distance, and traffic congestion to provide a suite of alternative routing options.

The application leverages OpenStreetMap data (via OSMnx) for the road network and can integrate with external APIs (like TomTom) for real-time traffic or use local simulations.

✨ Key Features
*Custom A Algorithm:** Finds routes based on a weighted cost function combining time, distance, and traffic score.

Multiple Route Options: Generates and compares four distinct route types:

Balanced: Optimized for overall best compromise.

Time-Optimized: Fastest route (highest priority on time).

Traffic-Avoiding: Route that minimizes travel through simulated or real traffic zones.

Distance-Optimized: Shortest route (simple Dijkstra's by distance).

Real-Time Data Ready: Structured to integrate with external traffic APIs (e.g., TomTom) for dynamic edge weighting.

Interactive Mapping: Visualizes all calculated routes on an interactive map using Folium.

Geocoding: Uses geopy to convert human-readable addresses into coordinates for pathfinding.

🛠️ Prerequisites
To run this project, you need:

Python 3.8+

pip (Python package installer)

Git (for cloning the repository)

📦 Installation & Setup
Follow these steps in your terminal to get the project running locally.

1. Clone the Repository
git clone [https://github.com/YOUR_USERNAME/traffic-route-optimizer.git](https://github.com/YOUR_USERNAME/traffic-route-optimizer.git)
cd traffic-route-optimizer

2. Create and Activate a Virtual Environment
It is highly recommended to use a virtual environment to manage dependencies cleanly.

# Create the environment
python -m venv venv

# Activate the environment (on Windows Command Prompt/PowerShell)
.\venv\Scripts\activate
# Activate the environment (on macOS/Linux)
# source venv/bin/activate

3. Install Dependencies
Install all required packages from a requirements.txt file (you may need to create this first, see note below).

pip install Flask networkx osmnx numpy requests geopy folium

(If you were using a requirements.txt file, the command would be pip install -r requirements.txt)

⚙️ Configuration
The application uses configuration variables defined in src/config.py.

API Keys
If you want to use real-time traffic data, you must provide a TomTom API key. Otherwise, the application will default to using simulated traffic data.

In src/config.py:

# src/config.py

# Replace '' with your actual TomTom API Key if you have one
TOMTOM_API_KEY = '' 

Logging
The application uses Python's built-in logging module. Logging is configured in run.py to output INFO level messages and higher to your console, which is helpful for diagnostics.

▶️ Running the Application
Ensure your virtual environment is active.

Run the main application file:

python run.py

The console will display a link (usually http://127.0.0.1:5000/). Open this link in your web browser.

Enter the Location (e.g., New York, USA), Departure Address, and Destination Address to generate and compare the optimized routes.

📂 Project Structure
File/Folder

Description

run.py -> The entry point for the Flask application.

src/ -> Contains all core Python logic.

src/interface.py -> Flask application setup and all routing logic (GET/POST requests).

src/routes.py -> Contains the A* and Dijkstra pathfinding implementations.

src/traffics.py -> Handles OSMNx graph loading and traffic data application (simulation or API).

src/config.py -> Stores application settings, defaults, and API key placeholders.

src/utils.py -> General utility functions (e.g., Haversine distance).

src/visualization.py -> Generates the interactive map using Folium.

templates/ -> Stores HTML templates (e.g., index.html).

static/ -> Stores CSS and JavaScript assets.

.gitignore -> Ensures unnecessary local files (like venv/ and caches) are not tracked by Git.