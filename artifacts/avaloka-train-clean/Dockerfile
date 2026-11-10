# Avaloka-generated inference container
FROM python:3.11-slim

WORKDIR /app
COPY requirements.lock ./
RUN pip install --no-cache-dir -r requirements.lock

COPY model/ ./model/
COPY service.py ./

EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request,sys; \
  sys.exit(0) if urllib.request.urlopen('http://localhost:8080/health').status==200 else sys.exit(1)"
CMD ["uvicorn", "service:app", "--host", "0.0.0.0", "--port", "8080"]
