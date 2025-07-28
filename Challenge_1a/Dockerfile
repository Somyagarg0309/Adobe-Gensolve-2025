# Specify the platform to ensure AMD64 architecture compatibility
FROM --platform=linux/amd64 python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script into the container at /app
COPY main.py .

# Set the default command to run when the container starts.
# This will execute the main() function in the script, which handles
# processing the input/output directories automatically.
CMD ["python", "main.py"]
