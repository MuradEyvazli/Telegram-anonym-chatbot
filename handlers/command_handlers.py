from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import db
from config import WELCOME_MESSAGE, HELP_MESSAGE, SETUP_GENDER, CHATTING, IDLE
from chat_manager import find_chat_partner, end_chat, next_chat_partner, set_filters
from handlers.profile_handlers import profile_command, handle_setup_flow

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a welcome message when the command /start is issued."""
    user_id = update.effective_user.id
    
    # Make sure the user is in the database
    db.add_user(user_id)
    
    # Kullanıcıya daha ayrıntılı bir hoşgeldiniz mesajı gönder
    custom_welcome = (
        "Hoş geldiniz! Bu bot sayesinde anonim olarak diğer kullanıcılarla sohbet edebilirsiniz. "
        "Başlamak için size birkaç soru soracağım.\n\n"
        "📋 Komutlar:\n"
        "/start - Profil kurulumunu başlat\n"
        "/find - Sohbet partneri bul\n"
        "/profile - Profilinizi görüntüle/düzenle\n"
        "/stop - Mevcut sohbeti sonlandır\n"
        "/next - Yeni bir partner bul\n"
        "/help - Yardım mesajını göster\n"
        "/clear - Profilinizi sıfırlayın"
    )
    
    await update.message.reply_text(custom_welcome)
    
    # /start komutuna her basıldığında profil kurulumunu başlat
    # Kurulum zaten tamamlanmış olsa bile kullanıcıya tekrar kurulum fırsatı ver
    db.set_user_state(user_id, SETUP_GENDER)
    await handle_setup_flow(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a help message when the command /help is issued."""
    await update.message.reply_text(HELP_MESSAGE)

async def find_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Find a chat partner when the command /find is issued."""
    user_id = update.effective_user.id
    
    # Kullanıcı kurulumu tamamlamadıysa
    if not db.is_setup_complete(user_id):
        await update.message.reply_text("Sohbet başlatmadan önce profilinizi oluşturmanız gerekiyor.")
        db.set_user_state(user_id, SETUP_GENDER)
        await handle_setup_flow(update, context)
        return
    
    # Kurulum tamamlandıysa normal eşleştirme akışına devam et
    await find_chat_partner(update, context)

async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Stop the current chat when the command /stop is issued."""
    await end_chat(update, context)

async def next_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End current chat and find a new partner when /next is issued."""
    user_id = update.effective_user.id
    
    # Kullanıcı kurulumu tamamlamadıysa
    if not db.is_setup_complete(user_id):
        await update.message.reply_text("Sohbet başlatmadan önce profilinizi oluşturmanız gerekiyor.")
        db.set_user_state(user_id, SETUP_GENDER)
        await handle_setup_flow(update, context)
        return
    
    await next_chat_partner(update, context)

async def filter_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set filters for finding a chat partner."""
    user_id = update.effective_user.id
    
    # Kullanıcı kurulumu tamamlamadıysa
    if not db.is_setup_complete(user_id):
        await update.message.reply_text("Filtreleri ayarlamadan önce profilinizi oluşturmanız gerekiyor.")
        db.set_user_state(user_id, SETUP_GENDER)
        await handle_setup_flow(update, context)
        return
    
    await set_filters(update, context)

async def profile_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """View and edit user profile."""
    await profile_command(update, context)

async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı profilini ve tercihlerini temizle."""
    user_id = update.effective_user.id
    
    # Kullanıcının mevcut durumunu kontrol et
    user_state = db.get_user_state(user_id)
    
    # Eğer kullanıcı sohbetteyse, önce sohbeti sonlandır
    if user_state == CHATTING:
        await end_chat(update, context)
    
    # Veritabanında kullanıcı verilerini sıfırla
    cursor = db.conn.cursor()
    
    # Kullanıcının filtrelerini, profilini ve bekleme durumunu temizle
    cursor.execute("DELETE FROM filters WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
    cursor.execute("DELETE FROM waiting WHERE user_id = ?", (user_id,))
    
    # Kullanıcının durumunu ve kurulum durumunu sıfırla
    cursor.execute(
        "UPDATE users SET state = ?, setup_complete = 0 WHERE user_id = ?",
        (IDLE, user_id)
    )
    
    # Bellek içi verilerden de temizle
    if user_id in db.waiting_users:
        db.waiting_users.remove(user_id)
    
    db.conn.commit()
    
    # Kullanıcıya bilgi ver ve yeniden başlatma seçeneği sun
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Evet, profili yeniden oluştur", callback_data="restart_profile")],
        [InlineKeyboardButton("Hayır, daha sonra", callback_data="no_restart")]
    ])
    
    await update.message.reply_text(
        "✅ Profiliniz ve tüm tercihleriniz başarıyla temizlendi. Yeni bir profil oluşturmak ister misiniz?",
        reply_markup=keyboard
    )