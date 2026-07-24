# Base Image
FROM python:3.11.9-slim

# Working directory inside container
WORKDIR /app

# Copy requirements first
COPY requirements.txt .

# Install packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy remaining project
COPY . .

# Expose FastAPI port
EXPOSE 6004

# Run application
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "6004", "--reload"]