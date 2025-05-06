FROM python:3.12


RUN apt-get update && apt-get install -y 
libglib2.0-0 
libnss3 
libatk1.0-0 
libatk-bridge2.0-0 
libxkbcommon0 
libxcomposite1 
libxdamage1 
libxfixes3 
libxrandr2 
libgbm1 
libpango-1.0-0 
libcairo2 
libasound2 
libcups2 
&& apt-get clean 
&& rm -rf /var/lib/apt/lists/*



RUN pip install playwright==1.47.0 && 
playwright install-deps && 
playwright install chromium



WORKDIR /app

Copy requirements and install Python dependencies

COPY requirements.txt . RUN pip install --no-cache-dir -r requirements.txt

Copy bot script

COPY bot.py .

Command to run the bot

CMD ["python", "bot.py"]
