# Use the official Python base image
FROM python:3.11-slim-buster

# Set the working directory
WORKDIR /app

# Copy requirements.txt into the working directory
COPY requirements.txt requirements.txt

# Install the required packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the Streamlit port
EXPOSE 8000

# Start the fastapi app
CMD ["uvicorn", "main:app", "--reload"]