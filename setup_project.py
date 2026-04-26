import os

# Define project structure
structure = [
    "data/raw",          # to store 6 CSVs
    "data/processed",
    "src/database",      # SQL connection logic
    "src/processing",    # OOP data cleaning
    "src/models",        # ML logic
    "notebooks",
    "app"                # Streamlit app
]

# Create directories
for folder in structure:
    os.makedirs(folder, exist_ok=True)

# Generate requirements.txt
requirements = """pandas
numpy
sqlalchemy
psycopg2-binary
scikit-learn
xgboost
streamlit
"""

with open("requirements.txt", "w") as f:
    f.write(requirements)

# Generate .env template
env_template = """# Database Credentials
DB_HOST=localhost
DB_PORT=5432
DB_NAME=geopolitical_risk
DB_USER=your_username
DB_PASSWORD=your_password
"""

with open(".env", "w") as f:
    f.write(env_template)

print("✅ Project structure, requirements.txt, and .env template created successfully.")
