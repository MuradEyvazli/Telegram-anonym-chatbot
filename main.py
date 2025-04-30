import logging
import signal
import sys
from telegram.ext import (
    Application, CommandHandler, MessageHandler, 
    CallbackQueryHandler, filters
)

from config import TOKEN, START_COMMAND, HELP_COMMAND, FIND_COMMAND, STOP_COMMAND, NEXT_COMMAND, FILTER_COMMAND, PROFILE_COMMAND, CLEAR_COMMAND
from handlers.command_handlers import (
    start_command, help_command, find_command, stop_command, next_command, filter_command, profile_command_handler, clear_command
)
from handlers.message_handlers import handle_message, handle_callback_query
from utils.helpers import setup_logging
from database import db

def signal_handler(sig, frame):
    """Gracefully handle shutdown."""
    print('Shutting down...')
    db.close()
    sys.exit(0)

def main() -> None:
    """Start the bot."""
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Starting the bot...")
    
    # Setup signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)  # CTRL+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Create the Application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler(START_COMMAND, start_command))
    application.add_handler(CommandHandler(HELP_COMMAND, help_command))
    application.add_handler(CommandHandler(FIND_COMMAND, find_command))
    application.add_handler(CommandHandler(STOP_COMMAND, stop_command))
    application.add_handler(CommandHandler(NEXT_COMMAND, next_command))
    application.add_handler(CommandHandler(FILTER_COMMAND, filter_command))
    application.add_handler(CommandHandler(PROFILE_COMMAND, profile_command_handler))
    application.add_handler(CommandHandler(CLEAR_COMMAND, clear_command))
    
    # Add message handler (for all message types)
    application.add_handler(MessageHandler(
        filters.ALL & ~filters.COMMAND & filters.ChatType.PRIVATE, 
        handle_message
    ))
    
    # Add callback query handler (for inline keyboard buttons)
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    
    # Log errors
    application.add_error_handler(lambda update, context: 
        logger.error(f"Update {update} caused error {context.error}")
    )
    
    # NOT: Periyodik eşleşme kontrolü şimdilik devre dışı bırakıldı
    # setup_periodic_match_check(application, interval=15)
    
    # Run the bot until the user presses Ctrl-C
    logger.info("Bot started, polling for updates...")
    try:
        application.run_polling(poll_interval=1)
    finally:
        # Bu blok bot kapandığında çalışır
        db.close()
        logger.info("Database connection closed.")

if __name__ == '__main__':
    main()