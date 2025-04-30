from typing import Optional, Tuple, Dict
from telegram import Update
from telegram.ext import ContextTypes

from database import db
from config import (
    IDLE, WAITING, CHATTING,
    WAITING_MESSAGE, PARTNER_FOUND_MESSAGE, CHAT_ENDED_MESSAGE,
    NO_CHAT_MESSAGE, ALREADY_SEARCHING_MESSAGE, ALREADY_CHATTING_MESSAGE,
    WAITING_WITH_FILTERS
)

async def find_chat_partner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Find a chat partner for the user."""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    # Check if user is already chatting
    if user_state == CHATTING:
        await update.message.reply_text(ALREADY_CHATTING_MESSAGE)
        return
    
    # Check if user is already waiting
    if user_state == WAITING:
        await update.message.reply_text(ALREADY_SEARCHING_MESSAGE)
        return
    
    # Add user to waiting list
    db.add_to_waiting(user_id)
    
    # Get user filters if any
    user_filters = db.get_user_filters(user_id)
    
    # Different message if filters are active
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
            await update.message.reply_text(
                f"Filtreleriniz: {', '.join(filter_desc)}\n" + WAITING_WITH_FILTERS
            )
        else:
            await update.message.reply_text(WAITING_MESSAGE)
    else:
        await update.message.reply_text(WAITING_MESSAGE)
    
    # Try to find a chat partner with filters
    partner_id = db.get_matching_waiting_user(user_id)
    
    if partner_id:
        # Create a chat between the two users
        db.create_chat(user_id, partner_id)
        
        # Notify both users
        await update.message.reply_text(PARTNER_FOUND_MESSAGE)
        await context.bot.send_message(chat_id=partner_id, text=PARTNER_FOUND_MESSAGE)

async def end_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End the current chat."""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    if user_state != CHATTING:
        await update.message.reply_text(NO_CHAT_MESSAGE)
        return
    
    # End the chat and get partner ID
    partner_id = db.end_chat(user_id)
    
    # Notify both users
    await update.message.reply_text(CHAT_ENDED_MESSAGE)
    if partner_id:
        await context.bot.send_message(chat_id=partner_id, text=CHAT_ENDED_MESSAGE)

async def next_chat_partner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """End current chat and find a new partner."""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    if user_state == CHATTING:
        # First end the current chat
        await end_chat(update, context)
    
    # Then find a new partner
    await find_chat_partner(update, context)

async def set_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Set user filters for matching."""
    user_id = update.effective_user.id
    args = context.args
    
    # User is already in a chat, don't allow filter changes
    if db.get_user_state(user_id) == CHATTING:
        await update.message.reply_text(
            "Aktif bir sohbetteyken filtreleri değiştiremezsiniz. "
            "Önce /stop ile sohbeti sonlandırın."
        )
        return
    
    # No arguments, show help
    if not args:
        from config import FILTER_HELP_MESSAGE
        await update.message.reply_text(FILTER_HELP_MESSAGE)
        return
    
    # Reset filters
    if args[0].lower() == "reset":
        db.set_user_filters(user_id, {})
        from config import FILTER_RESET_SUCCESS
        await update.message.reply_text(FILTER_RESET_SUCCESS)
        return
    
    # Parse basic filters: gender and age
    if len(args) >= 2:
        filters = {}
        
        # Gender
        gender = args[0].lower()
        if gender in ["erkek", "kadın", "any"]:
            filters["gender"] = gender
        else:
            await update.message.reply_text(
                f"Geçersiz cinsiyet: {gender}. Geçerli değerler: erkek, kadın, any"
            )
            return
        
        # Age
        try:
            age = int(args[1])
            if age < 13 or age > 100:  # Age restrictions for safety
                await update.message.reply_text("Yaş 13 ile 100 arasında olmalıdır.")
                return
            filters["age"] = age
        except ValueError:
            await update.message.reply_text(f"Geçersiz yaş: {args[1]}. Bir sayı girmelisiniz.")
            return
        
        # Optional parameters
        for arg in args[2:]:
            if "=" in arg:
                key, value = arg.split("=", 1)
                
                # Age range filters
                if key == "min_age":
                    try:
                        min_age = int(value)
                        if min_age < 13 or min_age > 100:
                            await update.message.reply_text("Minimum yaş 13 ile 100 arasında olmalıdır.")
                            continue
                        filters["min_age"] = min_age
                    except ValueError:
                        await update.message.reply_text(f"Geçersiz minimum yaş: {value}")
                        continue
                
                elif key == "max_age":
                    try:
                        max_age = int(value)
                        if max_age < 13 or max_age > 100:
                            await update.message.reply_text("Maksimum yaş 13 ile 100 arasında olmalıdır.")
                            continue
                        filters["max_age"] = max_age
                    except ValueError:
                        await update.message.reply_text(f"Geçersiz maksimum yaş: {value}")
                        continue
        
        # Basic validation
        if "min_age" in filters and "max_age" in filters:
            if filters["min_age"] > filters["max_age"]:
                await update.message.reply_text("Minimum yaş maksimum yaştan büyük olamaz.")
                return
        
        # Save filters
        db.set_user_filters(user_id, filters)
        
        # Confirm to user
        filter_desc = []
        if 'gender' in filters:
            filter_desc.append(f"Cinsiyet: {filters['gender']}")
        if 'age' in filters:
            filter_desc.append(f"Yaş: {filters['age']}")
        if 'min_age' in filters:
            filter_desc.append(f"Min Yaş: {filters['min_age']}")
        if 'max_age' in filters:
            filter_desc.append(f"Max Yaş: {filters['max_age']}")
        
        from config import FILTER_SET_SUCCESS
        await update.message.reply_text(
            f"Filtreleriniz: {', '.join(filter_desc)}\n{FILTER_SET_SUCCESS}"
        )
    else:
        from config import FILTER_HELP_MESSAGE
        await update.message.reply_text(
            "Yetersiz parametre. Doğru kullanım:\n\n" + FILTER_HELP_MESSAGE
        )

async def find_chat_partner_with_query(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Callback query ile sohbet partneri bul."""
    user_id = query.from_user.id
    user_state = db.get_user_state(user_id)
    
    # Kullanıcı zaten sohbet ediyorsa
    if user_state == CHATTING:
        await query.edit_message_text("Zaten bir sohbet içindesiniz.")
        return
    
    # Kullanıcı zaten bekliyorsa
    if user_state == WAITING:
        await query.edit_message_text("Zaten bir sohbet partneri aranıyor. Lütfen bekleyin.")
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
    
    # Eşleşen partner bul - uygun birisi oturum açıp beklemekteyse
    partner_id = db.get_matching_waiting_user(user_id)
    
    if partner_id:
        # İki kullanıcı arasında sohbet oluştur
        db.create_chat(user_id, partner_id)
        
        # Her iki kullanıcıyı da bilgilendir
        await query.edit_message_text(PARTNER_FOUND_MESSAGE)
        await context.bot.send_message(chat_id=partner_id, text=PARTNER_FOUND_MESSAGE)

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Forward a message to the chat partner."""
    user_id = update.effective_user.id
    user_state = db.get_user_state(user_id)
    
    if user_state != CHATTING:
        # User is not in a chat, remind them to find a partner
        if user_state != WAITING:  # Don't send this if they're already waiting
            await update.message.reply_text(NO_CHAT_MESSAGE)
        return
    
    partner_id = db.get_partner(user_id)
    if not partner_id:
        # Something went wrong, reset user state
        db.set_user_state(user_id, IDLE)
        await update.message.reply_text(NO_CHAT_MESSAGE)
        return
    
    # Forward the message content based on its type
    if update.message.text:
        await context.bot.send_message(chat_id=partner_id, text=update.message.text)
    elif update.message.photo:
        # Get the largest photo (last in the array)
        photo = update.message.photo[-1]
        caption = update.message.caption or ""
        await context.bot.send_photo(
            chat_id=partner_id, 
            photo=photo.file_id, 
            caption=caption
        )
    elif update.message.sticker:
        await context.bot.send_sticker(
            chat_id=partner_id, 
            sticker=update.message.sticker.file_id
        )
    elif update.message.voice:
        await context.bot.send_voice(
            chat_id=partner_id, 
            voice=update.message.voice.file_id, 
            caption=update.message.caption
        )
    elif update.message.video:
        await context.bot.send_video(
            chat_id=partner_id, 
            video=update.message.video.file_id, 
            caption=update.message.caption
        )
    elif update.message.animation:
        await context.bot.send_animation(
            chat_id=partner_id, 
            animation=update.message.animation.file_id, 
            caption=update.message.caption
        )
    else:
        # For unsupported message types
        await context.bot.send_message(
            chat_id=partner_id, 
            text="Karşı taraf desteklenmeyen bir mesaj türü gönderdi."
        )