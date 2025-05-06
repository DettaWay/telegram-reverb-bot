import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from playwright.async_api import async_playwright
import asyncio

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# URL of the Delay & Reverb Time Calculator
CALCULATOR_URL = "https://anotherproducer.com/online-tools-for-musicians/delay-reverb-time-calculator/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the /start command is issued."""
    await update.message.reply_text(
        "Hi! I'm a Delay & Reverb Calculator bot. Send me a BPM value (e.g., 120) "
        "and I'll fetch the reverb and delay settings from Another Producer's calculator."
    )

async def scrape_calculator(bpm: str) -> str:
    """Scrape the calculator page for the given BPM and return the results."""
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()

            # Navigate to the calculator page
            await page.goto(CALCULATOR_URL)

            # Wait for the BPM input field to be visible
            await page.wait_for_selector('input[name="bpm"]', timeout=10000)

            # Input the BPM value
            await page.fill('input[name="bpm"]', bpm)

            # Wait for the tables to update (give time for JavaScript to process)
            await page.wait_for_timeout(1000)

            # Scrape the reverb settings table
            reverb_table = await page.query_selector('table')
            reverb_rows = await reverb_table.query_selector_all('tr')
            reverb_data = ["Reverb Settings:"]
            for row in reverb_rows[1:]:  # Skip header row
                cells = await row.query_selector_all('td')
                if len(cells) == 4:
                    size = await cells[0].inner_text()
                    pre_delay = await cells[1].inner_text()
                    decay = await cells[2].inner_text()
                    total = await cells[3].inner_text()
                    reverb_data.append(
                        f"{size}: Pre-Delay: {pre_delay}, Decay Time: {decay}, Total: {total}"
                    )

            # Scrape the delay settings table
            delay_table = await page.query_selector_all('table')[1]
            delay_rows = await delay_table.query_selector_all('tr')
            delay_data = ["\\nDelay Settings:"]
            for row in delay_rows[1:]:  # Skip header row
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

            # Combine and return the results
            return "\\n".join(reverb_data + delay_data)

    except Exception as e:
        logger.error(f"Error scraping calculator: {e}")
        return "Sorry, I couldn't fetch the data. Please try again later."

async def handle_bpm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle user messages containing BPM values."""
    bpm = update.message.text.strip()

    # Validate BPM (must be a positive number)
    try:
        bpm_float = float(bpm)
        if bpm_float <= 0:
            await update.message.reply_text("Please send a positive BPM value (e.g., 120).")
            return
    except ValueError:
        await update.message.reply_text("Please send a valid BPM number (e.g., 120).")
        return

    # Inform user that processing is starting
    await update.message.reply_text(f"Fetching reverb and delay settings for BPM {bpm}...")

    # Scrape the calculator
    result = await scrape_calculator(bpm)

    # Send the results
    await update.message.reply_text(result)

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log errors caused by updates."""
    logger.error(f"Update {update} caused error {context.error}")

def main() -> None:
    """Run the bot."""
    # Replace 'YOUR_BOT_TOKEN' with your actual Telegram bot token
    bot_token = '7826142507:AAHzjIylO9zhE1vhsyqoBi4X8Z_1FnCgFz8'

    # Create the Application
    application = Application.builder().token(bot_token).build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bpm))
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
