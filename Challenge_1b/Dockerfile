# Specify the platform to ensure AMD64 architecture compatibility
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# This step will download the sentence-transformer model, so the container runs offline.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script into the container at /app
COPY main.py .

# Set the default command to run when the container starts.
# This executes the main() function, which processes /app/input and writes to /app/output.
CMD ["python", "main.py"]
