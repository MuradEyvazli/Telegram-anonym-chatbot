from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from database import db
from config import (
    SETUP_GENDER, SETUP_AGE, SETUP_PREFERENCES, IDLE, WAITING, CHATTING,
    GENDER_QUESTION, AGE_QUESTION, AGE_RANGE_QUESTION, GENDER_PREFERENCE_QUESTION,
    SETUP_COMPLETE_MESSAGE, FIND_AFTER_SETUP_QUESTION, PROFILE_MESSAGE,
    GENDER_KEYBOARD, AGE_RANGE_KEYBOARD, GENDER_PREFERENCE_KEYBOARD,
    FIND_AFTER_SETUP_KEYBOARD, PROFILE_KEYBOARD, WAITING_WITH_FILTERS, WAITING_MESSAGE,
    PARTNER_FOUND_MESSAGE
)
from chat_manager import find_chat_partner

async def handle_setup_flow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı kurulum akışını yönet."""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    # Kullanıcı durumuna göre işlem yap
    if user_state == SETUP_GENDER:
        await ask_gender(update, context)
    elif user_state == SETUP_AGE:
        await ask_age(update, context)
    elif user_state == SETUP_PREFERENCES:
        await ask_preferences(update, context)

async def ask_gender(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıya cinsiyetini sor."""
    await update.message.reply_text(
        GENDER_QUESTION,
        reply_markup=GENDER_KEYBOARD
    )

async def process_gender_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, gender: str) -> None:
    """Cinsiyet seçimini işle ve yaş sorma aşamasına geç."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Cinsiyeti kaydet
    gender_map = {
        'male': 'erkek',
        'female': 'kadın',
        'any': 'belirtilmemiş'
    }
    
    gender_value = gender_map.get(gender, 'belirtilmemiş')
    db.set_user_profile(user_id, 'gender', gender_value)
    
    # Kullanıcı durumunu güncelle
    db.set_user_state(user_id, SETUP_AGE)
    
    # Yaş sorusunu gönder
    await query.answer()
    await query.edit_message_text(AGE_QUESTION)

async def ask_age(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcıya yaşını sor (sadece text mesaj durumunda)."""
    # Bu fonksiyon normalde doğrudan çağrılmaz, process_gender_selection'dan sonra kullanıcı yaş gönderdiğinde
    # handle_age_response çağrılır
    pass

async def process_age_response(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcının yaş yanıtını işle."""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    # Yaş doğrulama
    try:
        age = int(text)
        if age < 13 or age > 100:
            await update.message.reply_text("Lütfen 13 ile 100 arasında bir yaş girin.")
            return
            
        # Yaşı kaydet
        db.set_user_profile(user_id, 'age', age)
        
        # Sonraki aşamaya geç
        db.set_user_state(user_id, SETUP_PREFERENCES)
        
        # Yaş aralığı tercihini sor
        await update.message.reply_text(
            AGE_RANGE_QUESTION,
            reply_markup=AGE_RANGE_KEYBOARD
        )
        
    except ValueError:
        await update.message.reply_text("Lütfen sadece sayı girin. Örneğin: 25")

async def process_age_range_selection(update: Update, context: ContextTypes.DEFAULT_TYPE, age_range: str) -> None:
    """Yaş aralığı seçimini işle."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Yaş aralığını işle
    min_age, max_age = 18, 100  # Varsayılan değerler
    
    if age_range == '18_25':
        min_age, max_age = 18, 25
    elif age_range == '26_35':
        min_age, max_age = 26, 35
    elif age_range == '36_50':
        min_age, max_age = 36, 50
    elif age_range == '50_plus':
        min_age, max_age = 50, 100
    # 'any' durumunda varsayılan değerler kullanılır
    
    # Filtreleri kaydet
    db.set_user_filters(user_id, {'min_age': min_age, 'max_age': max_age})
    
    # Cinsiyet tercihini sor
    await query.answer()
    await query.edit_message_text(
        GENDER_PREFERENCE_QUESTION,
        reply_markup=GENDER_PREFERENCE_KEYBOARD
    )

async def process_gender_preference(update: Update, context: ContextTypes.DEFAULT_TYPE, gender_pref: str) -> None:
    """Cinsiyet tercihi seçimini işle."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    # Cinsiyet tercihini işle
    gender_map = {
        'male': 'erkek',
        'female': 'kadın',
        'any': 'any'
    }
    
    gender_value = gender_map.get(gender_pref, 'any')
    db.set_user_filters(user_id, {'preferred_gender': gender_value})
    
    # Kurulumu tamamla
    db.mark_setup_complete(user_id)
    
    # Kurulum tamamlandı mesajı ve sohbet başlatma seçeneği
    await query.answer()
    await query.edit_message_text(
        SETUP_COMPLETE_MESSAGE,
        reply_markup=FIND_AFTER_SETUP_KEYBOARD
    )

async def start_chat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, choice: str) -> None:
    """Kurulum sonrası sohbet başlatma seçimini işle."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    if choice == 'now':
        # Mesajı güncelle ve sohbet aramaya başla
        await query.edit_message_text("Sohbet partneri aranıyor...")
        # find_chat_partner fonksiyonunu Update nesnesi ile çağırma
        await find_chat_partner_with_query(query, context)
    else:
        # Sadece mesajı güncelle
        await query.edit_message_text("İstediğiniz zaman /find komutunu kullanarak sohbet başlatabilirsiniz.")

async def find_chat_partner_with_query(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback query ile sohbet partneri bul."""
    user_id = query.from_user.id
    user_state = db.get_user_state(user_id)
    
    # Kullanıcı zaten sohbet ediyorsa
    if user_state == CHATTING:
        await query.edit_message_text("Zaten bir sohbet içindesiniz.")
        return
    
    # Kullanıcı zaten bekliyorsa, aktif olarak yeni bir partner ara
    if user_state == WAITING:
        # Aktif olarak yeni eşleşme ara
        partner_id = db.get_matching_waiting_user(user_id)
        
        if partner_id:
            # Eşleşme bulundu, sohbeti başlat
            db.create_chat(user_id, partner_id)
            
            # Her iki kullanıcıyı da bilgilendir
            await query.edit_message_text(PARTNER_FOUND_MESSAGE)
            await context.bot.send_message(chat_id=partner_id, text=PARTNER_FOUND_MESSAGE)
            return
        else:
            await query.edit_message_text("Henüz uygun bir eşleşme bulunamadı. Beklemede kalıyorsunuz...")
            return
    
    # Kullanıcıyı bekleme listesine ekle
    db.add_to_waiting(user_id)
    
    # Kullanıcı filtrelerini al
    user_filters = db.get_user_filters(user_id)
    
    # Kullanıcıya bekleme mesajı gönder
    if user_filters:
        filter_desc = []
        if 'gender' in user_filters:
            filter_desc.append(f"Cinsiyet: {user_filters['gender']}")
        if 'age' in user_filters:
            filter_desc.append(f"Yaş: {user_filters['age']}")
        if 'min_age' in user_filters:
            filter_desc.append(f"Min Yaş: {user_filters['min_age']}")
        if 'max_age' in user_filters:
            filter_desc.append(f"Max Yaş: {user_filters['max_age']}")
        if 'preferred_gender' in user_filters:
            filter_desc.append(f"Tercih Edilen Cinsiyet: {user_filters['preferred_gender']}")
            
        if filter_desc:
            await query.edit_message_text(
                f"Filtreleriniz: {', '.join(filter_desc)}\n" + WAITING_WITH_FILTERS
            )
        else:
            await query.edit_message_text(WAITING_MESSAGE)
    else:
        await query.edit_message_text(WAITING_MESSAGE)
    
    # Eşleşen partner bul
    partner_id = db.get_matching_waiting_user(user_id)
    
    if partner_id:
        # İki kullanıcı arasında sohbet oluştur
        db.create_chat(user_id, partner_id)
        
        # Her iki kullanıcıyı da bilgilendir
        await query.edit_message_text(PARTNER_FOUND_MESSAGE)
        await context.bot.send_message(chat_id=partner_id, text=PARTNER_FOUND_MESSAGE)

async def profile_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Kullanıcı profilini görüntüle ve düzenleme seçenekleri sun."""
    user_id = update.effective_user.id
    
    # Kullanıcı kurulumu tamamlamadıysa, kurulum akışını başlat
    if not db.is_setup_complete(user_id):
        db.set_user_state(user_id, SETUP_GENDER)
        await handle_setup_flow(update, context)
        return
    
    # Profil bilgilerini al
    profile = db.get_user_profile(user_id)
    filters = db.get_user_filters(user_id)
    
    # Profil bilgilerini biçimlendir
    gender = profile.get('gender', 'Belirtilmemiş')
    age = profile.get('age', 'Belirtilmemiş')
    
    preferred_gender = filters.get('preferred_gender', 'Farketmez')
    min_age = filters.get('min_age', 'Belirtilmemiş')
    max_age = filters.get('max_age', 'Belirtilmemiş')
    
    # Yaş aralığı metnini oluştur
    age_range_text = "Farketmez"
    if min_age != 'Belirtilmemiş' and max_age != 'Belirtilmemiş':
        age_range_text = f"{min_age} - {max_age}"
    
    # Profil mesajını oluştur
    profile_text = (
        f"👤 Profiliniz:\n\n"
        f"Cinsiyet: {gender}\n"
        f"Yaş: {age}\n\n"
        f"Eşleşme Tercihleriniz:\n"
        f"Tercih ettiğiniz cinsiyet: {preferred_gender}\n"
        f"Tercih ettiğiniz yaş aralığı: {age_range_text}"
    )
    
    # Profil mesajını ve düzenleme seçeneklerini gönder
    await update.message.reply_text(
        profile_text,
        reply_markup=PROFILE_KEYBOARD
    )

async def process_profile_change(update: Update, context: ContextTypes.DEFAULT_TYPE, change_type: str) -> None:
    """Profil değişiklik talebini işle."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    await query.answer()
    
    if change_type == 'gender':
        # Cinsiyet değiştirme işlemi
        await query.edit_message_text(
            "Yeni cinsiyetinizi seçin:",
            reply_markup=GENDER_KEYBOARD
        )
    elif change_type == 'age':
        # Yaş değiştirme işlemi
        await query.edit_message_text(AGE_QUESTION)
        db.set_user_state(user_id, SETUP_AGE)
    elif change_type == 'preferences':
        # Tercih değiştirme işlemi - yaş aralığı ile başla
        await query.edit_message_text(
            AGE_RANGE_QUESTION,
            reply_markup=AGE_RANGE_KEYBOARD
        )
    elif change_type == 'close':
        # Profil görünümünü kapat
        await query.edit_message_text("Profil görünümü kapatıldı.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback query işleyicisi."""
    query = update.callback_query
    data = query.data
    user_id = query.from_user.id
    
    # Callback veri öneklerine göre işlem yap
    if data.startswith("gender_"):
        gender = data.split("_")[1]
        await process_gender_selection(update, context, gender)
    
    elif data.startswith("age_range_"):
        age_range = data.split("_")[2:] 
        age_range_str = "_".join(age_range)
        await process_age_range_selection(update, context, age_range_str)
    
    elif data.startswith("pref_gender_"):
        gender_pref = data.split("_")[2]
        await process_gender_preference(update, context, gender_pref)
    
    elif data.startswith("start_chat_"):
        choice = data.split("_")[2]
        await start_chat_callback(update, context, choice)
    
    elif data.startswith("change_"):
        change_type = data.split("_")[1]
        await process_profile_change(update, context, change_type)
    
    elif data == "close_profile":
        await process_profile_change(update, context, "close")
    
    # Profil yeniden başlatma callback'i
    elif data == "restart_profile":
        # Yeniden profil kurulumu başlat
        db.set_user_state(user_id, SETUP_GENDER)
        await query.answer()
        await query.edit_message_text("Profil kurulumu başlatılıyor...")
        # Ayrı bir mesaj olarak gönder, böylece message_id farklı olur
        await query.message.reply_text(GENDER_QUESTION, reply_markup=GENDER_KEYBOARD)
    
    elif data == "no_restart":
        await query.answer()
        await query.edit_message_text("Anlaşıldı! İstediğiniz zaman /start komutunu kullanarak profil kurulumunu başlatabilirsiniz.")