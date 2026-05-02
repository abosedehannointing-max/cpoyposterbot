import os
import io
import logging
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from fpdf import FPDF
import PyPDF2

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Maximum file size (20MB for free tier)
MAX_FILE_SIZE = 20 * 1024 * 1024

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Hello! I'm a PDF Converter Bot!\n\n"
        "📄 Send me a PDF → I'll extract text\n"
        "📝 Send me text → I'll make a PDF\n\n"
        "Just send any PDF or text message!"
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    document = update.message.document
    
    if not document.mime_type == "application/pdf":
        await update.message.reply_text("⚠️ Please send a PDF file.")
        return
    
    if document.file_size > MAX_FILE_SIZE:
        await update.message.reply_text(f"⚠️ File too large! Max {MAX_FILE_SIZE // (1024*1024)}MB.")
        return
    
    await update.message.reply_text("⏳ Processing PDF...")
    
    try:
        # Download PDF
        file = await context.bot.get_file(document.file_id)
        pdf_bytes = await file.download_as_bytearray()
        
        # Extract text
        text = ""
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n\n"
        
        if not text.strip():
            await update.message.reply_text("❌ No text found in this PDF.")
            return
        
        # Send text (split if too long)
        if len(text) > 4096:
            for i in range(0, len(text), 4096):
                await update.message.reply_text(text[i:i+4096])
        else:
            await update.message.reply_text(f"📄 Extracted Text:\n\n{text}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error processing PDF. Try again.")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    
    if text.startswith("/"):
        return
    
    await update.message.reply_text("⏳ Creating PDF...")
    
    try:
        # Create PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, text)
        
        # Get PDF as bytes
        pdf_output = pdf.output(dest='S').encode('latin1')
        
        # Send PDF
        await update.message.reply_document(
            document=io.BytesIO(pdf_output),
            filename="converted.pdf",
            caption="✅ Here's your PDF!"
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text("❌ Error creating PDF. Try again.")

async def set_commands(app):
    await app.bot.set_my_commands([BotCommand("start", "Start the bot")])

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.post_init = set_commands
    
    logger.info("Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
