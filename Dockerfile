# official Python runtime as a parent image
FROM python:3.9-slim-buster

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages 
RUN pip install -r requirements.txt

# Make port 5000 available
EXPOSE 5000

# Define environment variable for JWT secret key
ENV JWT_SECRET_KEY="your-super-secret-jwt-key-for-fastapi"

# Run the FastAPI application with Uvicorn
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]
