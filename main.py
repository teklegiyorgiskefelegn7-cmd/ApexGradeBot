import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
import google.generativeai as genai

# 1. መዝገብ (Logging) - ስህተቶችን ለመከታተል
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. አንተ የላክሃቸው ቁልፎች (API Keys)
TELEGRAM_BOT_TOKEN = "8264772001:AAFKRYNh_YRbbBv-VDO8UvxHOrqbrjf7Q9U"
GEMINI_API_KEY = "AIzaSyAm_1CSE9hDA1GQqy8AM5VOnULBPteP6AI"
CHANNEL_USERNAME = "@ApexGradeEthiopia"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# 3. ሰብስክራይብ ማድረጋቸውን የሚያረጋግጥ ተግባር
async def is_subscribed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        if member.status in ['member', 'administrator', 'creator']:
            return True
    except Exception as e:
        logging.error(f"Subscription check error: {e}")
    
    keyboard = [[InlineKeyboardButton("Join Channel 📢", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"⚠️ ቦቱን ለመጠቀም መጀመሪያ የ {CHANNEL_USERNAME} ቤተሰብ መሆን አለብህ።\n"
        "እባክህ Join በልና ድጋሚ ሞክር!",
        reply_markup=reply_markup
    )
    return False

# 4. የ /start ትዕዛዝ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_subscribed(update, context):
        user_name = update.effective_user.first_name
        await update.message.reply_text(
            f"ሰላም {user_name}! እንኳን ወደ Apex Grade Ethiopia በሰላም መጣህ።\n"
            "የፈለግከውን ጥያቄ መጠየቅ ወይም PDF ፋይል መላክ ትችላለህ።"
        )

# 5. ጥያቄዎችን ማስተናገድ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    user_text = update.message.text
    sent_message = await update.message.reply_text("በማሰብ ላይ ነኝ... ⏳")

    try:
        response = model.generate_content(f"እንደ ኢትዮጵያ ዩኒቨርሲቲ መምህር በመሆን ለዚህ ጥያቄ ግልጽ መልስ ስጥ፡ {user_text}")
        await sent_message.edit_text(response.text)
    except Exception as e:
        await sent_message.edit_text("ይቅርታ፣ መልሱን በማመንጨት ላይ ስህተት ተፈጥሯል። እባክህ ቆይተህ ሞክር።")
        logging.error(f"Gemini Error: {e}")

# 6. PDF ፋይሎችን ማስተናገድ
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    document = update.message.document
    if document.mime_type == 'application/pdf':
        sent_message = await update.message.reply_text("PDF ፋይሉ ደርሶኛል፣ እያነበብኩት ነው... 📖")
        # ለወደፊቱ እዚህ ጋር የፋይል ንባብ ዝርዝር ኮድ ይጨመራል
        await sent_message.edit_text("ፋይሉን ተቀብያለሁ! አሁን ከዚህ PDF ምን ማወቅ ትፈልጋለህ? ጥያቄህን መጠየቅ ትችላለህ።")
    else:
        await update.message.reply_text("እባክህ PDF ፋይል ብቻ ላክልኝ።")

if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    
    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    application.add_handler(MessageHandler(filters.ALL, start))

    print("Apex Grade Bot is running...")
    application.run_polling()
