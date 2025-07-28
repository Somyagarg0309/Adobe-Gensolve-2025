# @title download_model.py
# This script is run only once during the Docker build process.
# Its purpose is to download the sentence-transformer model and save it
# inside the Docker image's cache, so it can be used offline later.

from sentence_transformers import SentenceTransformer
import os

# Define the model name and the cache directory inside the container
MODEL_NAME = "all-MiniLM-L6-v2"
CACHE_DIR = "/app/model_cache"

# Create the cache directory if it doesn't exist
os.makedirs(CACHE_DIR, exist_ok=True)

print(f"Downloading sentence-transformer model: {MODEL_NAME} to {CACHE_DIR}...")

# This line downloads the model and saves it to the specified cache directory.
# The `cache_folder` argument is crucial for ensuring the model is saved
# in a predictable location within our Docker image.
model = SentenceTransformer(MODEL_NAME, cache_folder=CACHE_DIR)

print("Model downloaded and cached successfully.")
