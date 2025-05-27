# Use the official Python image
FROM python:3.10

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    git-lfs \
    ccache \
    && rm -rf /var/lib/apt/lists/*

# Initialize Git LFS
RUN git lfs install

# Copy only the requirements file to leverage Docker caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# COPY .env /app/.env # Will be passed at runtime

# Expose the FastAPI port
EXPOSE 8000

# Start FastAPI with Uvicorn
CMD ["python", "app.py"]
