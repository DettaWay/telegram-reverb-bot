import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import os

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL of the Delay & Reverb Time Calculator
CALCULATOR_URL = "https://anotherproducer.com/online-tools-for-musicians/delay-reverb-time-calculator/"

# Simple HTTP server for health check
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"Bot is running")

def run_health_check():
    server = HTTPServer(("0.0.0.0", 8080), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! I'm a Delay & Reverb Calculator bot. Send me a BPM value (e.g., 120) "
        "and I'll fetch the reverb and delay settings from Another Producer's calculator."
    )

async def scrape_calculator(bpm: str) -> str:
    """Scrape the calculator page for the given BPM and return the results."""
    await asyncio.sleep(1)  # Delay to avoid rate limits
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            await page.goto(CALCULATOR_URL)
            await page.wait_for_selector('input[name="bpm"]', timeout=10000)
            await page.fill('input[name="bpm"]', bpm)
            await page.wait_for_timeout(1000)
            reverb_table = await page.query_selector('table')
            reverb_rows = await reverb_table.query_selector_all('tr')
            reverb_data = ["Reverb Settings:"]
            for row in reverb_rows[1:]:
                cells = await row.query_selector_all('td')
                if len(cells) == 4:
                    size = await cells[0].inner_text()
                    pre_delay = await cells[1].inner_text()
                    decay = await cells[2].inner_text()
                    total = await cells[3].inner_text()
                    reverb_data.append(
                        f"{size}: Pre-Delay: {pre_delay}, Decay Time: {decay}, Total: {total}"
                    )
            delay_table = await page.query_selector_all('table')[1]
            delay_rows = await delay_table.query_selector_all('tr')
            delay_data = ["\nDelay Settings:"]
            for row in delay_rows[1:]:
                cells = await row.query_selector_all('td')
                if len(cells) == 4:
                    note = await cells[0].inner_text()
                    notes = await cells[1].inner_text()
                    dotted = await cells[2].inner_text()
                    triplets = await cells[3].inner_text()
                    delay_data.append(
                        f"{note}: Notes: {notes}, Dotted: {dotted}, Triplets: {triplets}"
                    )
            await browser.close()
            return "\n".join(reverb_data + delay_data)
    except Exception as e:
        logger.error(f"Error scraping calculator: {e}")
        return "Sorry, I couldn't fetch the data. Please try again later."

async def handle_bpm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages containing BPM values."""
    bpm = update.message.text.strip()
    try:
        bpm_float = float(bpm)
        if bpm_float <= 0:
            await update.message.reply_text("Please send a positive BPM value (e.g., 120).")
            return
    except ValueError:
        await update.message.reply_text("Please send a valid BPM number (e.g., 120).")
        return
    await update.message.reply_text(f"Fetching reverb and delay settings for BPM {bpm}...")
    result = await scrape_calculator(bpm)
    await update.message.reply_text(result)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Run the bot."""
    # Start health check server in a separate thread
    health_thread = threading.Thread(target=run_health_check, daemon=True)
    health_thread.start()

    # Get bot token from environment variable
    bot_token = os.getenv('BOT_TOKEN')
    if not bot_token:
        logger.error("BOT_TOKEN environment variable not set")
        os._exit(1)

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bpm))
    application.add_error_handler(error_handler)

    # Start the bot with error handling for conflicts
    try:
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except Exception as e:
        logger.error(f"Polling failed: {e}")
        if "Conflict" in str(e):
            logger.error("Another bot instance is running. Stopping this instance.")
            os._exit(1)

if __name__ == '__main__':
    main()
