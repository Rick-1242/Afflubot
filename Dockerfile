# Use a lightweight official Python image
FROM python:3.12.2-slim

# Set environment variables to optimize Python execution
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Europe/Rome

# Set the working directory to the project root in the container
WORKDIR /app

# Copy only requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install dependencies without keeping the cache to reduce image size
RUN pip install --no-cache-dir -r requirements.txt

# Copy the necessary project files
COPY src/ ./src/

# As required, set the working directory to src/ before running the app
WORKDIR /app/src

# Start the scheduler
CMD ["python", "scheduler.py"]
