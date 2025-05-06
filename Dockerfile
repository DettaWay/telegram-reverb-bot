FROM python:3.12-slim

# Install system dependencies for Playwright
RUN apt-get update && apt-get install -y \n    libglib2.0-0 \n    libnss3 \n    libatk1.0-0 \n    libatk-bridge2.0-0 \n    libxkbcommon0 \n    libxcomposite1 \n    libxdamage1 \n    libxfixes3 \n    libxrandr2 \n    libgbm1 \n    libpango-1.0-0 \n    libcairo2 \n    libasound2 \n    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers
RUN playwright install chromium

# Copy bot script
COPY bot.py .

# Command to run the bot
CMD ["python", "bot.py"]
