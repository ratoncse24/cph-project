FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Run Alembic migrations before starting
CMD ["sh", "-c", "alembic upgrade heads && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
    