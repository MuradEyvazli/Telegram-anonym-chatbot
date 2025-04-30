import logging
import asyncio
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes

from config import PARTNER_FOUND_MESSAGE, WAITING

def setup_logging() -> None:
    """Setup basic logging for the bot."""
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

def get_user_info(update: Update) -> Dict[str, Any]:
    """Extract user information from update."""
    user = update.effective_user
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'language_code': user.language_code
    }

def log_user_activity(update: Update, activity: str) -> None:
    """Log user activity for monitoring."""
    user_info = get_user_info(update)
    user_id = user_info['id']
    username = user_info.get('username', 'No username')
    
    logging.info(f"User {user_id} ({username}) {activity}")

# Yeni eklenen fonksiyon
async def periodic_match_check(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Periyodik olarak bekleyen kullanıcılar için eşleşme kontrolü yap."""
    from database import db  # İçe aktarım döngüsünü önlemek için burada içe aktarıyoruz
    
    # Bekleyen tüm kullanıcıları kontrol et
    waiting_users = list(db.waiting_users)  # Bir kopya al
    
    for user_id in waiting_users:
        # Kullanıcının hala bekleme durumunda olduğundan emin ol
        if db.get_user_state(user_id) != WAITING:
            continue
        
        # Eşleşme bul
        partner_id = db.get_matching_waiting_user(user_id)
        
        if partner_id:
            # Eşleşme bulundu, sohbeti başlat
            db.create_chat(user_id, partner_id)
            
            # Her iki kullanıcıyı da bilgilendir
            await context.bot.send_message(chat_id=user_id, text=PARTNER_FOUND_MESSAGE)
            await context.bot.send_message(chat_id=partner_id, text=PARTNER_FOUND_MESSAGE)
            
            # Bildirimden sonra bu kullanıcılar için döngüyü sonlandır
            # waiting_users listesinin bir kopyasını aldığımız için asıl liste etkilenmez
            logging.info(f"Periodic check: Matched user {user_id} with {partner_id}")

def setup_periodic_match_check(application, interval=30):
    """Uygulama başlatılırken periyodik eşleşme kontrolünü ayarla."""
    job_queue = application.job_queue
    job_queue.run_repeating(periodic_match_check, interval=interval)
    logging.info(f"Periodic match checking scheduled every {interval} seconds")