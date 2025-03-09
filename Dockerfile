FROM python:3.11-slim

# Install system dependencies and Google Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    ca-certificates \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libnspr4 \
    libnss3 \
    lsb-release \
    xdg-utils \
    libxss1

RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && apt-get install -y google-chrome-stable

# Set environment variable for Chrome
ENV GOOGLE_CHROME_BIN="/usr/bin/google-chrome"

WORKDIR /app

COPY requirements.txt .

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Explicitly install gunicorn to avoid missing module issue
RUN pip install --no-cache-dir gunicorn

COPY . .

EXPOSE 10000

# Start Gunicorn
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers=4", "--timeout=120"]
