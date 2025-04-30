from typing import Final
import os
from dotenv import load_dotenv
import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables and print current directory for debugging
logger.info(f"Current directory: {os.getcwd()}")
load_dotenv()

# Bot configuration - Getting from environment variables
TOKEN: Final = os.getenv('TOKEN')
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')

# Debug info to check if environment variables are loaded
logger.info(f"Token loaded: {'Yes' if TOKEN else 'No'}")
logger.info(f"Bot username loaded: {'Yes' if BOT_USERNAME else 'No'}")

# Fallback to hardcoded values if environment variables are not loaded
# This should be temporary during debugging
if not TOKEN:
    logger.warning("TOKEN not found in .env, using fallback value")
    TOKEN = '7795666174:AAGYuOj0yDr8RPRrESNyuvBxx1SEQTcJiSU'

if not BOT_USERNAME:
    logger.warning("BOT_USERNAME not found in .env, using fallback value")
    BOT_USERNAME = '@Picasso Chat'

# Rest of your configuration remains the same
# States
IDLE = 'idle'           # User is not in a chat
WAITING = 'waiting'     # User is waiting for a partner
CHATTING = 'chatting'   # User is in a chat with someone
SETUP_GENDER = 'setup_gender'  # User is setting up gender
SETUP_AGE = 'setup_age'        # User is setting up age
SETUP_PREFERENCES = 'setup_preferences'  # User is setting up preferences

# Commands
START_COMMAND = 'start'
HELP_COMMAND = 'help'
FIND_COMMAND = 'find'    # Find a chat partner
STOP_COMMAND = 'stop'    # Stop current chat
NEXT_COMMAND = 'next'    # Find a new partner
FILTER_COMMAND = 'filter' # Set chat filters
PROFILE_COMMAND = 'profile' # View or edit profile
CLEAR_COMMAND = 'clear'  # Clear profile and settings

# Messages
WELCOME_MESSAGE = "Hoş geldiniz! Bu bot sayesinde anonim olarak diğer kullanıcılarla sohbet edebilirsiniz. Başlamak için size birkaç soru soracağım."

# Rest of the code from previous config.py
GENDER_QUESTION = "Cinsiyetiniz nedir?"
GENDER_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Erkek", callback_data="gender_male")],
    [InlineKeyboardButton("Kadın", callback_data="gender_female")],
    [InlineKeyboardButton("Belirtmek İstemiyorum", callback_data="gender_any")]
])

# All other constants continue...
# ...
AGE_QUESTION = "Yaşınız kaç? (Lütfen sadece sayı yazın, örneğin: 25)"

AGE_RANGE_QUESTION = "Hangi yaş aralığındaki kişilerle konuşmak istersiniz?"
AGE_RANGE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("18-25", callback_data="age_range_18_25")],
    [InlineKeyboardButton("26-35", callback_data="age_range_26_35")],
    [InlineKeyboardButton("36-50", callback_data="age_range_36_50")],
    [InlineKeyboardButton("50+", callback_data="age_range_50_plus")],
    [InlineKeyboardButton("Farketmez", callback_data="age_range_any")]
])

GENDER_PREFERENCE_QUESTION = "Hangi cinsiyetteki kişilerle konuşmak istersiniz?"
GENDER_PREFERENCE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Erkek", callback_data="pref_gender_male")],
    [InlineKeyboardButton("Kadın", callback_data="pref_gender_female")],
    [InlineKeyboardButton("Farketmez", callback_data="pref_gender_any")]
])

SETUP_COMPLETE_MESSAGE = "Profil kurulumunuz tamamlandı! Artık sohbet etmeye başlayabilirsiniz.\n\nKomutlar:\n/find - Sohbet partneri bul\n/profile - Profilinizi görüntüleyin veya düzenleyin\n/stop - Mevcut sohbeti sonlandır\n/next - Yeni bir partner bul\n/help - Yardım mesajını göster\n/clear - Profilinizi sıfırlayın"

FIND_AFTER_SETUP_QUESTION = "Hemen sohbet etmeye başlamak ister misiniz?"
FIND_AFTER_SETUP_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Evet, hemen başla", callback_data="start_chat_now")],
    [InlineKeyboardButton("Hayır, daha sonra", callback_data="start_chat_later")]
])

PROFILE_MESSAGE = "Profiliniz:\n{}\n\nProfil bilgilerinizi değiştirmek ister misiniz?"
PROFILE_KEYBOARD = InlineKeyboardMarkup([
    [InlineKeyboardButton("Cinsiyeti Değiştir", callback_data="change_gender")],
    [InlineKeyboardButton("Yaşı Değiştir", callback_data="change_age")],
    [InlineKeyboardButton("Tercihleri Değiştir", callback_data="change_preferences")],
    [InlineKeyboardButton("Kapat", callback_data="close_profile")]
])

HELP_MESSAGE = """Komutlar:
/start - Profil kurulumunu başlat
/find - Sohbet partneri bul
/profile - Profilinizi görüntüleyin veya düzenleyin
/stop - Mevcut sohbeti sonlandır
/next - Yeni bir partner bul
/clear - Profilinizi ve tercihlerinizi sıfırlayın
/help - Bu yardım mesajını göster"""

WAITING_MESSAGE = "Sohbet partneri aranıyor... Lütfen bekleyin."
PARTNER_FOUND_MESSAGE = "Bir sohbet partneri bulundu! Şimdi konuşabilirsiniz. Sohbeti sonlandırmak için /stop, yeni bir partner bulmak için /next yazın."
CHAT_ENDED_MESSAGE = "Sohbet sonlandırıldı."
NO_CHAT_MESSAGE = "Şu anda aktif bir sohbetiniz yok. /find komutu ile sohbet partneri bulabilirsiniz."
ALREADY_SEARCHING_MESSAGE = "Zaten bir sohbet partneri aranıyor. Lütfen bekleyin."
ALREADY_CHATTING_MESSAGE = "Zaten bir sohbet içindesiniz. Önce /stop komutu ile mevcut sohbeti sonlandırın."

# Filtre mesajları
FILTER_HELP_MESSAGE = """Sohbet filtrelerinizi ayarlamak için:
/filter cinsiyet yaş

Cinsiyet seçenekleri:
- erkek: Erkek kullanıcılarla eşleş
- kadın: Kadın kullanıcılarla eşleş
- any: Herhangi bir cinsiyetle eşleş

Yaş:
- Kendi yaşınızı belirtin

Örnek:
/filter erkek 25 - 25 yaşında erkek olduğunuzu belirtir
/filter kadın 30 - 30 yaşında kadın olduğunuzu belirtir

İsteğe bağlı parametreler:
min_age - Minimum yaş sınırı: /filter erkek 25 min_age=20
max_age - Maksimum yaş sınırı: /filter erkek 25 max_age=35

Tüm filtreleri temizlemek için:
/filter reset
"""

FILTER_SET_SUCCESS = "Filtreleriniz başarıyla ayarlandı. /find komutunu kullanarak eşleşmeye başlayabilirsiniz."
FILTER_RESET_SUCCESS = "Tüm filtreleriniz temizlendi. Artık herhangi bir kullanıcıyla eşleşebilirsiniz."
WAITING_WITH_FILTERS = "Belirlediğiniz filtrelere göre sohbet partneri aranıyor... Lütfen bekleyin."

# Profil temizleme
PROFILE_CLEAR_SUCCESS = "Profiliniz ve tüm tercihleriniz başarıyla temizlendi."
PROFILE_CLEAR_CONFIRM = "Profilinizi ve tüm tercihlerinizi temizlemek istediğinizden emin misiniz? Bu işlem geri alınamaz."

# Callback verileri
CALLBACK_PATTERNS = {
    'GENDER': 'gender_',
    'AGE_RANGE': 'age_range_',
    'PREF_GENDER': 'pref_gender_',
    'START_CHAT': 'start_chat_',
    'CHANGE_PROFILE': 'change_',
    'CLOSE_PROFILE': 'close_profile',
    'RESTART_PROFILE': 'restart_profile',
    'NO_RESTART': 'no_restart'
}