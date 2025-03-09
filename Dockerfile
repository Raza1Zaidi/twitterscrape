# Use a slim Python image as base
FROM python:3.11-slim

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    lsb-release \
    xdg-utils \
    libxss1

# Install Google Chrome stable
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Set environment variable so webdriver_manager knows where chrome is
ENV GOOGLE_CHROME_BIN="/usr/bin/google-chrome"

# Create working directory
WORKDIR /app

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your app
COPY . .

# Expose the port that your Flask app will run on
EXPOSE 8000

# Start the Flask app using Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8000"]
