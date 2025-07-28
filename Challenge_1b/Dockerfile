# Specify the platform to ensure AMD64 architecture compatibility
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# --- OFFLINE MODEL CACHING ---
# Copy the model download script into the container
COPY download_model.py .

# Run the script to download and cache the model.
# The internet is available for this step.
RUN python download_model.py
# --- END OFFLINE MODEL CACHING ---

# --- FORCE OFFLINE MODE FOR RUNTIME ---
# Set environment variables AFTER the download is complete.
# This forces the transformers library into full offline mode for the final CMD,
# preventing any network calls when the container is run with --network none.
ENV TRANSFORMERS_OFFLINE=1
ENV HF_HUB_OFFLINE=1

# Copy the main application script
COPY main.py .

# Set the default command to run when the container starts.
# This will execute the main() function in a fully offline environment.
CMD ["python", "main.py"]
