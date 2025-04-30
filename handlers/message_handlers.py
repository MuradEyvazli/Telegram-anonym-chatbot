from telegram import Update
from telegram.ext import ContextTypes

from database import db
from config import SETUP_AGE
from chat_manager import forward_message
from handlers.profile_handlers import process_age_response, handle_setup_flow

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages and forward them to chat partners."""
    # Skip messages in group chats or channels
    if update.effective_chat.type != "private":
        return
    
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    # Kullanıcı kurulum aşamasında mı?
    if user_state == SETUP_AGE:
        # Bu yaş girme aşamasıdır, sayısal değer beklenir
        await process_age_response(update, context)
        return
    elif not db.is_setup_complete(user_id):
        # Kurulum tamamlanmadıysa, kurulum işlemine devam et
        await handle_setup_flow(update, context)
        return
    
    # Forward the message to the chat partner
    await forward_message(update, context)

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callback queries from inline keyboards."""
    # Bu fonksiyon profile_handlers.py'daki handle_callback_query tarafından yönetilir
    from handlers.profile_handlers import handle_callback_query as profile_callback_handler
    await profile_callback_handler(update, context)