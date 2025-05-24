# 1) Base image
FROM python:3.11-slim

# 2) Install Chrome + dependencies
RUN apt-get update && \
    apt-get install -y wget gnupg ca-certificates \
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
      libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
      libxfixes3 libgbm1 libpango1.0-0 libasound2 \
      fonts-liberation lsb-release xdg-utils && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub \
      | apt-key add - && \
    echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" \
      > /etc/apt/sources.list.d/google-chrome.list && \
    apt-get update && \
    apt-get install -y google-chrome-stable && \
    rm -rf /var/lib/apt/lists/*

# 3) Tell undetected_chromedriver where Chrome lives
ENV CHROME_BIN=/usr/bin/google-chrome-stable
# (Optional but recommended for Chrome in containers)
ENV UDC_NO_SANDBOX=1

# 4) Install Python deps
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copy your code
COPY . .

# 6) Launch your Flask app under Gunicorn, with $PORT expansion
#    Use shell form so Docker will expand $PORT from the env.
CMD gunicorn server:app --bind 0.0.0.0:$PORT
