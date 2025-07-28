# Specify the platform to ensure AMD64 architecture compatibility
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# --- FORCE OFFLINE MODE ---
# Set environment variables to prevent any network calls by the transformers library
# This is the key fix for the "Failed to resolve 'huggingface.co'" error.
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- OFFLINE MODEL CACHING ---
# Copy the model download script into the container
COPY download_model.py .

# Run the script to download and cache the model.
# This is the only time the container will need an internet connection.
RUN python download_model.py
# --- END OFFLINE MODEL CACHING ---

# Copy the main application script
COPY main.py .

# Set the default command to run when the container starts.
# This will execute the main() function, which processes /app/input and writes to /app/output.
CMD ["python", "main.py"]
