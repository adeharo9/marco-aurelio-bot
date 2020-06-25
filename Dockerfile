FROM python:3.8.3-slim-buster

# Copy files to image
WORKDIR /app
COPY .env .
COPY env.py .
COPY main.py .
COPY requirements.txt .
COPY Dockerfile .
COPY LICENSE .
COPY README.md .

# Install packages
RUN pip install -r requirements.txt

# Attach volume to bot directory
VOLUME /app/marcoaurelio
# Attach volume to strings directory
VOLUME /app/strings
# Attach volume to utils directory
VOLUME /app/utils

# Expose server ports and start command
EXPOSE 80
EXPOSE 443
CMD ["python", "main.py"]
