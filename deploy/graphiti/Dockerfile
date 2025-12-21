FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY graphiti_service.py ./api/services/
COPY graphiti_router.py ./api/routers/
COPY main.py .

# Create __init__.py files for Python imports
RUN mkdir -p api/services api/routers && \
    touch api/__init__.py api/services/__init__.py api/routers/__init__.py

EXPOSE 8001

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
