from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import random
import time
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
GIRLFRIEND_CHAT_ID = os.getenv('GIRLFRIEND_CHAT_ID')
ADMIN_CHAT_ID = os.getenv('ADMIN_CHAT_ID')

# Initialize the log directory
LOG_DIR = 'logs'
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def log_reply(date, type_of_reply):
    """Log the reply status to a file."""
    log_file = os.path.join(LOG_DIR, f'{datetime.now().year}-{datetime.now().month:02d}.txt')
    with open(log_file, 'a') as file:
        file.write(f"{date} - {type_of_reply}\n")

def start(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id == GIRLFRIEND_CHAT_ID:
        context.bot.send_message(chat_id=chat_id, text="Hello! I'm here to make your day special. 😊")
    else:
        context.bot.send_message(chat_id=chat_id, text="Sorry, this bot is exclusively for someone special.")

def send_good_morning(context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Same to You", callback_data='same_to_you_morning')],
        [InlineKeyboardButton("Very Good Morning", callback_data='very_good_morning')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=GIRLFRIEND_CHAT_ID, text="Good Morning! 🌞", reply_markup=reply_markup)
    log_reply(datetime.now().strftime('%Y-%m-%d'), 'Good Morning')
    context.job_queue.run_once(morning_reminder, 1800)  # 30 minutes reminder

def morning_reminder(context: CallbackContext) -> None:
    context.bot.send_message(chat_id=GIRLFRIEND_CHAT_ID, text="Subah ho gayi jaag bhi jao! Mai aapka intezaar kar raha hoon. ❤️")

def send_good_night(context: CallbackContext) -> None:
    keyboard = [
        [InlineKeyboardButton("Same to You", callback_data='same_to_you_night')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    context.bot.send_message(chat_id=GIRLFRIEND_CHAT_ID, text="Good Night! 🌙", reply_markup=reply_markup)
    log_reply(datetime.now().strftime('%Y-%m-%d'), 'Good Night')
    context.job_queue.run_once(night_reminder, 1800)  # 30 minutes reminder

def night_reminder(context: CallbackContext) -> None:
    now = datetime.now().strftime('%H:%M')
    if now < '23:58':  # Check if before 11:58 PM
        context.bot.send_message(chat_id=GIRLFRIEND_CHAT_ID, text="Bahut der ho gayi hai, ab so jao! 😴")

def button_callback(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    query.answer()
    
    if query.data == 'same_to_you_morning':
        query.edit_message_text(text="Aapka din acha gujare! 🌟")
    elif query.data == 'very_good_morning':
        query.edit_message_text(text="Very Good Morning! Have a nice day! 😊")
    elif query.data == 'same_to_you_night':
        query.edit_message_text(text="Sweet dreams! 🌠")

def message_handler(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id == GIRLFRIEND_CHAT_ID:
        context.bot.send_message(chat_id=chat_id, text="Mai aapka WhatsApp pe intezaar kar raha hoon! 💬")

def generate_monthly_report():
    """Generate a monthly report for the admin."""
    log_file = os.path.join(LOG_DIR, f'{datetime.now().year}-{datetime.now().month:02d}.txt')
    if not os.path.exists(log_file):
        return "No data available for this month."
    
    with open(log_file, 'r') as file:
        lines = file.readlines()
    
    report = "Monthly Report:\n\n"
    for line in lines:
        report += line
    
    return report

def report(update: Update, context: CallbackContext) -> None:
    chat_id = str(update.message.chat_id)
    if chat_id == ADMIN_CHAT_ID:
        report_text = generate_monthly_report()
        context.bot.send_message(chat_id=chat_id, text=report_text)
    elif chat_id == GIRLFRIEND_CHAT_ID:
        context.bot.send_message(chat_id=chat_id, text="Reports will be sent at the end of the month.")
    else:
        context.bot.send_message(chat_id=chat_id, text="You are not authorized to use this command.")

def monthly_report_for_gf(context: CallbackContext) -> None:
    report_text = generate_monthly_report()
    context.bot.send_message(chat_id=GIRLFRIEND_CHAT_ID, text=f"Monthly Report:\n{report_text}")

def schedule_reports(update: Update, context: CallbackContext) -> None:
    now = datetime.now()
    next_month = (now + timedelta(days=31)).replace(day=1)
    next_month_end = next_month - timedelta(days=1)
    time_until_next_month_end = (next_month_end - now).total_seconds()
    
    # Schedule the monthly report for the girlfriend
    context.job_queue.run_once(monthly_report_for_gf, time_until_next_month_end)

def main() -> None:
    updater = Updater(BOT_TOKEN, use_context=True)

    dispatcher = updater.dispatcher
    job_queue = updater.job_queue
    
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CallbackQueryHandler(button_callback))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
    dispatcher.add_handler(CommandHandler("report", report))

    # Schedule Good Morning and Good Night messages
    job_queue.run_daily(send_good_morning, time=random_time(7, 8))
    job_queue.run_daily(send_good_night, time=random_time(23, 0))
    
    # Schedule monthly report for girlfriend
    schedule_reports(None, updater.dispatcher)

    updater.start_polling()
    updater.idle()

def random_time(start_hour, end_hour):
    """Returns a random time between two hours."""
    now = datetime.now()
    start_time = now.replace(hour=start_hour, minute=0, second=0, microsecond=0)
    end_time = now.replace(hour=end_hour, minute=0, second=0, microsecond=0)
    
    # If the end_time is before the start_time, adjust for the next day
    if end_time <= start_time:
        end_time += timedelta(days=1)
    
    return start_time + timedelta(seconds=random.randint(0, int((end_time - start_time).total_seconds())))

if __name__ == '__main__':
    main()
