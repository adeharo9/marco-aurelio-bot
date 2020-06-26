FROM python:3.8.3-slim-buster

# Copy dirs and files to image
WORKDIR /app
COPY dotenvpy ./dotenvpy
COPY .env .
COPY main.py .
COPY requirements.txt .
COPY Dockerfile .
COPY LICENSE .
COPY README.md .

# Install packages
RUN pip install -r requirements.txt

# Attach volume to bot directory
VOLUME /app/marcoaurelio

# Expose server ports and start command
CMD ["python", "main.py"]
