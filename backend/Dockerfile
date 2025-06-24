# Use an official Python runtime as a parent image
# Using the "slim" version is a good practice for smaller image sizes
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container at /app
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir makes the image smaller
# --upgrade pip ensures we have the latest version
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend application code into the container at /app
# This includes all your service folders, logs folder, .env file, etc.
COPY . .

# The CMD instruction specifies the default command to run when the container starts.
# We will override this in docker-compose.yml for each specific service,
# but it's good practice to have a default.
# For example, this would start the monitoring engine by default.
CMD ["python", "monitoring_engine.py"]