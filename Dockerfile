# Use official lightweight Python image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir certifi

# Install the c++ packages to enable compilation of the wheels for annoy and cffi
RUN apt-get update && apt-get install -y build-essential gcc g++

# Install setuptools that assist in creating python module wheels
RUN pip install --upgrade pip setuptools wheel

# Copy dependencies and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and data files
COPY ./app /app

# Expose the internal port the app runs on
EXPOSE 8045

# Command to run the application
# This is changed to start differently due to the need to import polars first. 06032026.
#CMD ["uvicorn", "main:fastapi_app", "--host", "0.0.0.0", "--port", "8045"]

CMD ["python", "main.py"]
