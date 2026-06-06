FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create directories for static assets and database
RUN mkdir -p static/animations static/ilustracoes static/personagens static/css static/js

EXPOSE 8000

CMD ["uvicorn", "core.presentation.web.main:app", "--host", "0.0.0.0", "--port", "8000"]
