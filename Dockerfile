# Sets up Python, dependencies, and system packages for Playwright
FROM python:3.12

RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libatk1.0-0 libatk-bridge2.0-0 libxkbcommon0 \
    libxcomposite1 libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2 libcups2 libdrm2 libfontconfig1 libfreetype6 \
    libgtk-3-0 libpangocairo-1.0-0 libx11-xcb1 libxcursor1 libxi6 libxtst6 && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    python -m playwright install chromium

COPY bot.py .

EXPOSE 8080

CMD ["python", "bot.py"]
