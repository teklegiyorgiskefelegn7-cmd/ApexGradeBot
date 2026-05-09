import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# 1. መዝገብ (Logging) - ስህተትን ለመከታተል
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 2. ቁልፎችን ከ Render Environment መቀበል
# ማሳሰቢያ፡ ቁልፎቹን እዚህ ኮድ ውስጥ አትጻፋቸው፤ Render ላይ በሞላኸው መሰረት ይሰራሉ
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
CHANNEL_USERNAME = "@ApexGradeEthiopia"  # የቻናልህ ስም

genai.configure(api_key=GEMINI_API_KEY)
# እዚህ ጋር 1.5-flash በማድረጋችን የ Quota ስህተቱ ይጠፋል
model = genai.GenerativeModel('gemini-1.5-flash')

# 3. በቻናል ሰብስክራይብ ማድረጋቸውን ማረጋገጫ
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
        f"⚠️ ቦቱን ለመጠቀም መጀመሪያ የ {CHANNEL_USERNAME} ቤተሰብ መሆን አለብህ!\nእባክህ Join ብለህ በድጋሚ ሞክር።",
        reply_markup=reply_markup
    )
    return False

# 4. የ /start ትዕዛዝ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_subscribed(update, context):
        user_name = update.effective_user.first_name
        await update.message.reply_text(
            f"ሰላም {user_name}! እንኳን ወደ Apex Grade Ethiopia በሰላም መጣህ።\nየፈለግከውን ጥያቄ መጠየቅ ወይም PDF ፋይል መላክ ትችላለህ።"
        )

# 5. የጽሁፍ ጥያቄዎችን ማስተናገጃ
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return

    user_text = update.message.text
    sent_message = await update.message.reply_text("በማሰብ ላይ ነኝ... ⏳")

    try:
        # ለተማሪዎች እንዲመች ማንነቱን መግለጽ
        prompt = f"አንተ ለኢትዮጵያ ተማሪዎች የተዘጋጀህ 'Apex Grade AI' ነህ። ለሚከተለው ጥያቄ ግልጽ መልስ ስጥ፦ {user_text}"
        response = model.generate_content(prompt)
        await sent_message.edit_text(response.text)
    except Exception as e:
        await sent_message.edit_text("ይቅርታ፣ መልስ በማመንጨት ላይ ስህተት ተፈጥሯል። እባክህ ትንሽ ቆይተህ ሞክር።")
        logging.error(f"Gemini Error: {e}")

# 6. PDF ፋይሎችን ማስተናገጃ (ለወደፊቱ)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_subscribed(update, context):
        return
    await update.message.reply_text("PDF ፋይል ተቀብያለሁ! በቅርቡ PDF የማንበብ አገልግሎት እጀምራለሁ።")

if __name__ == '__main__':
    if not TELEGRAM_BOT_TOKEN:
        print("Error: TELEGRAM_BOT_TOKEN not found in environment variables!")
    else:
        application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
        
        application.add_handler(CommandHandler('start', start))
        application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        application.add_handler(MessageHandler(filters.Document.PDF, handle_document))
        
        print("Bot is running...")
        application.run_polling()
