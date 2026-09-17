FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Dependencies first, in their own layer. Docker caches it, so changing a
# line of application code does not reinstall everything.
COPY requirements-service.txt .
RUN pip install --no-cache-dir -r requirements-service.txt

COPY shared/ shared/
COPY products/policydesk/ products/policydesk/

# Never run a web service as root. A bug that lets someone run a command
# then runs it as a user who owns nothing.
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s CMD \
  python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

CMD ["python3", "-m", "uvicorn", "app:app", "--app-dir", "products/policydesk", \
     "--host", "0.0.0.0", "--port", "8000"]