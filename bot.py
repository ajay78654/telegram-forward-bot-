import logging
import time
from telegram import Update, ParseMode
from telegram.ext import Updater, CommandHandler, CallbackContext
from config import BOT_TOKEN, DEFAULT_BATCH_SIZE, DEFAULT_DELAY, SOURCE_CHANNEL, TARGET_CHANNEL

# Set up logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Dictionary to store user settings
user_settings = {}
is_forwarding = False  # Flag to indicate if forwarding is in progress

# Command to set batch size
def set_batch_size(update: Update, context: CallbackContext):
    try:
        batch_size = int(context.args[0])
        user_settings['batch_size'] = batch_size
        update.message.reply_text(f"Batch size set to {batch_size}. Now, please set the delay time using /delay <seconds>.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /batchsize <number>")

# Command to set delay time
def set_delay(update: Update, context: CallbackContext):
    try:
        delay_time = int(context.args[0])
        user_settings['delay_time'] = delay_time
        update.message.reply_text(f"Delay time set to {delay_time} seconds. Now, please set the source channel using /source <channel_id>.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /delay <seconds>")

# Command to set source channel
def set_source_channel(update: Update, context: CallbackContext):
    try:
        source_channel = context.args[0]
        user_settings['source_channel'] = source_channel
        update.message.reply_text(f"Source channel set to {source_channel}. Now, please set the target channel using /target <channel_id>.")
    except IndexError:
        update.message.reply_text("Usage: /source <channel_id>")

# Command to set target channel
def set_target_channel(update: Update, context: CallbackContext):
    try:
        target_channel = context.args[0]
        user_settings['target_channel'] = target_channel
        update.message.reply_text(f"Target channel set to {target_channel}. Now, please set the start message ID using /start <message_id>.")
    except IndexError:
        update.message.reply_text("Usage: /target <channel_id>")

# Command to set start message ID
def set_start_message(update: Update, context: CallbackContext):
    try:
        start_message = int(context.args[0])
        user_settings['start_message'] = start_message
        update.message.reply_text(f"Start message ID set to {start_message}. Now, please set the end message ID using /end <message_id>.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /start <message_id>")

# Command to set end message ID
def set_end_message(update: Update, context: CallbackContext):
    try:
        end_message = int(context.args[0])
        user_settings['end_message'] = end_message
        update.message.reply_text(f"End message ID set to {end_message}. Everything is set! Now, you can start forwarding messages using /forward.")
    except (IndexError, ValueError):
        update.message.reply_text("Usage: /end <message_id>")

# Command to stop forwarding
def stop_forwarding(update: Update, context: CallbackContext):
    global is_forwarding
    is_forwarding = False
    update.message.reply_text("Forwarding has been stopped.")

# Forward messages in batches with delay, and within start and end message ID range
def forward_messages(update: Update, context: CallbackContext):
    global is_forwarding
    is_forwarding = True  # Set the flag to indicate forwarding is in progress
    
    source_channel = user_settings.get('source_channel', SOURCE_CHANNEL)
    target_channel = user_settings.get('target_channel', TARGET_CHANNEL)
    batch_size = user_settings.get('batch_size', DEFAULT_BATCH_SIZE)
    delay_time = user_settings.get('delay_time', DEFAULT_DELAY)
    start_message = user_settings.get('start_message')
    end_message = user_settings.get('end_message')

    if not source_channel or not target_channel:
        update.message.reply_text("Source and Target channels must be set using /source and /target commands.")
        return

    if not start_message or not end_message:
        update.message.reply_text("Start and End message IDs must be set using /start and /end commands.")
        return

    # Forward messages in the specified range
    total_messages_forwarded = 0
    total_messages = end_message - start_message + 1
    
    for message_id in range(start_message, end_message + 1):
        if not is_forwarding:  # Check if forwarding has been stopped
            update.message.reply_text("Forwarding has been interrupted.")
            return
        
        try:
            # Copy the message instead of forwarding it
            message = context.bot.get_message(chat_id=source_channel, message_id=message_id)
            context.bot.send_message(chat_id=target_channel, text=message.text, parse_mode=ParseMode.HTML)

            total_messages_forwarded += 1
            
            # Send progress update
            update.message.reply_text(f"Forwarded {total_messages_forwarded} of {total_messages} messages. {total_messages - total_messages_forwarded} remaining.")
            
        except Exception as e:
            logger.warning(f"Could not copy message {message_id}: {e}")

        if total_messages_forwarded % batch_size == 0:
            time.sleep(delay_time)

    update.message.reply_text(f"Finished forwarding! A total of {total_messages_forwarded} messages were forwarded.")

# Main function to start the bot
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    dp.add_handler(CommandHandler("batchsize", set_batch_size))
    dp.add_handler(CommandHandler("delay", set_delay))
    dp.add_handler(CommandHandler("source", set_source_channel))
    dp.add_handler(CommandHandler("target", set_target_channel))
    dp.add_handler(CommandHandler("start", set_start_message))
    dp.add_handler(CommandHandler("end", set_end_message))
    dp.add_handler(CommandHandler("forward", forward_messages))
    dp.add_handler(CommandHandler("stop", stop_forwarding))  # Add the stop command

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
