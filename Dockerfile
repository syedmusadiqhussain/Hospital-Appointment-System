# Use Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Initialize the database (this runs once during build)
# Note: SQLite data will reset if the app restarts. For persistent data, you'd need a cloud DB.
RUN python database.py

# Create a writable directory for permission issues (optional but good practice)
RUN chmod 777 .

# Expose the port Hugging Face expects (7860)
EXPOSE 7860

# Start the server on port 7860
CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "7860"]
