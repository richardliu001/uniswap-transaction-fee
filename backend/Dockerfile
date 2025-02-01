# Use official Python slim image
FROM python:3.9-slim

# Set environment variables to avoid writing .pyc files and enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy the entire application code
COPY . .

# Expose port 8000
EXPOSE 8000

# Run the application using uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
