import sqlite3
import json
from typing import Dict, Optional, List, Tuple, Any
from config import IDLE, WAITING, CHATTING, SETUP_GENDER, SETUP_AGE, SETUP_PREFERENCES

class Database:
    def __init__(self, db_path='bot_database.db'):
        """Initialize database with SQLite connection."""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Satırları sözlük olarak almak için
        
        # In-memory yapılar (geçici veri için)
        self.waiting_users: List[int] = []
        self.active_chats: Dict[int, int] = {}
        
        # Veritabanı tablolarını oluştur
        self._create_tables()
        
        # Aktif sohbetleri ve bekleyen kullanıcıları yükle
        self._load_waiting_and_active()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()
        
        # Kullanıcılar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            state TEXT NOT NULL,
            setup_complete BOOLEAN NOT NULL DEFAULT 0
        )
        ''')
        
        # Kullanıcı profilleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS profiles (
            user_id INTEGER PRIMARY KEY,
            gender TEXT,
            age INTEGER,
            profile_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Kullanıcı filtreleri tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS filters (
            user_id INTEGER PRIMARY KEY,
            preferred_gender TEXT,
            min_age INTEGER,
            max_age INTEGER,
            filter_data TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Aktif sohbetler tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            user_id INTEGER PRIMARY KEY,
            partner_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        # Bekleyen kullanıcılar tablosu
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS waiting (
            user_id INTEGER PRIMARY KEY,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        )
        ''')
        
        self.conn.commit()
    
    def _load_waiting_and_active(self):
        """Veritabanından bekleyen kullanıcıları ve aktif sohbetleri yükle."""
        cursor = self.conn.cursor()
        
        # Bekleyen kullanıcıları yükle
        cursor.execute("SELECT user_id FROM waiting")
        self.waiting_users = [row['user_id'] for row in cursor.fetchall()]
        
        # Aktif sohbetleri yükle
        cursor.execute("SELECT user_id, partner_id FROM chats")
        for row in cursor.fetchall():
            self.active_chats[row['user_id']] = row['partner_id']
    
    def add_user(self, user_id: int) -> None:
        """Add a new user to the database if they don't exist."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            cursor.execute(
                "INSERT INTO users (user_id, state, setup_complete) VALUES (?, ?, ?)",
                (user_id, SETUP_GENDER, 0)
            )
            self.conn.commit()
    
    def get_user_state(self, user_id: int) -> str:
        """Get the current state of a user."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT state FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        return result['state'] if result else SETUP_GENDER
    
    def set_user_state(self, user_id: int, state: str) -> None:
        """Set the state of a user."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET state = ? WHERE user_id = ?",
            (state, user_id)
        )
        self.conn.commit()
    
    def get_partner(self, user_id: int) -> Optional[int]:
        """Get the partner ID for a user."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT partner_id FROM chats WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        return result['partner_id'] if result else None
    
    def set_partner(self, user_id: int, partner_id: Optional[int]) -> None:
        """Set the partner for a user."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        if partner_id is None:
            cursor.execute("DELETE FROM chats WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT user_id FROM chats WHERE user_id = ?", (user_id,))
            if cursor.fetchone():
                cursor.execute(
                    "UPDATE chats SET partner_id = ? WHERE user_id = ?",
                    (partner_id, user_id)
                )
            else:
                cursor.execute(
                    "INSERT INTO chats (user_id, partner_id) VALUES (?, ?)",
                    (user_id, partner_id)
                )
        
        # Bellek içi veriyi de güncelle
        if partner_id is None:
            if user_id in self.active_chats:
                del self.active_chats[user_id]
        else:
            self.active_chats[user_id] = partner_id
            
        self.conn.commit()
    
    def add_to_waiting(self, user_id: int) -> None:
        """Add a user to the waiting list."""
        self.add_user(user_id)  # Make sure user exists
        
        if user_id not in self.waiting_users:
            self.waiting_users.append(user_id)
            
            cursor = self.conn.cursor()
            cursor.execute("SELECT user_id FROM waiting WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO waiting (user_id) VALUES (?)", (user_id,))
            
            self.set_user_state(user_id, WAITING)
            self.conn.commit()
    
    def remove_from_waiting(self, user_id: int) -> None:
        """Remove a user from the waiting list."""
        if user_id in self.waiting_users:
            self.waiting_users.remove(user_id)
            
            cursor = self.conn.cursor()
            cursor.execute("DELETE FROM waiting WHERE user_id = ?", (user_id,))
            self.conn.commit()
    
    def set_user_profile(self, user_id: int, field: str, value: Any) -> None:
        """Set a field in the user's profile."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        
        # Önce mevcut profili al
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        gender = None
        age = None
        profile_data = {}
        
        if result:
            gender = result['gender']
            age = result['age']
            if result['profile_data']:
                try:
                    profile_data = json.loads(result['profile_data'])
                except:
                    profile_data = {}
        
        # Alanı güncelle
        if field == 'gender':
            gender = value
        elif field == 'age':
            age = value
        else:
            profile_data[field] = value
        
        # Profile tablosunu güncelle
        if result:
            cursor.execute(
                "UPDATE profiles SET gender = ?, age = ?, profile_data = ? WHERE user_id = ?",
                (gender, age, json.dumps(profile_data), user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO profiles (user_id, gender, age, profile_data) VALUES (?, ?, ?, ?)",
                (user_id, gender, age, json.dumps(profile_data))
            )
        
        # Eğer cinsiyet veya yaş güncellendiyse, filtreleri de güncelle
        if field == 'gender' or field == 'age':
            self.set_user_filters(user_id, {field: value})
            
        self.conn.commit()
    
    def get_user_profile(self, user_id: int) -> Dict[str, Any]:
        """Get the user's complete profile."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        profile = {}
        if result:
            if result['gender']:
                profile['gender'] = result['gender']
            if result['age']:
                profile['age'] = result['age']
            if result['profile_data']:
                try:
                    additional_data = json.loads(result['profile_data'])
                    profile.update(additional_data)
                except:
                    pass
        
        return profile
    
    def get_profile_field(self, user_id: int, field: str) -> Any:
        """Get a specific field from the user's profile."""
        profile = self.get_user_profile(user_id)
        return profile.get(field)
    
    def is_setup_complete(self, user_id: int) -> bool:
        """Check if the user has completed the profile setup."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT setup_complete FROM users WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        return bool(result['setup_complete']) if result else False
    
    def mark_setup_complete(self, user_id: int) -> None:
        """Mark the user's profile setup as complete."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE users SET setup_complete = 1, state = ? WHERE user_id = ?",
            (IDLE, user_id)
        )
        self.conn.commit()
    
    def set_user_filters(self, user_id: int, filters: Dict) -> None:
        """Kullanıcı için eşleşme filtrelerini ayarla."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        
        # Önce mevcut filtreleri al
        cursor.execute("SELECT * FROM filters WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        preferred_gender = None
        min_age = None
        max_age = None
        filter_data = {}
        
        if result:
            preferred_gender = result['preferred_gender']
            min_age = result['min_age']
            max_age = result['max_age']
            if result['filter_data']:
                try:
                    filter_data = json.loads(result['filter_data'])
                except:
                    filter_data = {}
        
        # Filtreleri güncelle
        if 'preferred_gender' in filters:
            preferred_gender = filters['preferred_gender']
        if 'min_age' in filters:
            min_age = filters['min_age']
        if 'max_age' in filters:
            max_age = filters['max_age']
        if 'gender' in filters:
            filter_data['gender'] = filters['gender']
        if 'age' in filters:
            filter_data['age'] = filters['age']
        
        # Diğer filtre alanlarını ekle
        for key, value in filters.items():
            if key not in ['preferred_gender', 'min_age', 'max_age', 'gender', 'age']:
                filter_data[key] = value
        
        # Filtreleri veritabanına kaydet
        if result:
            cursor.execute(
                "UPDATE filters SET preferred_gender = ?, min_age = ?, max_age = ?, filter_data = ? WHERE user_id = ?",
                (preferred_gender, min_age, max_age, json.dumps(filter_data), user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO filters (user_id, preferred_gender, min_age, max_age, filter_data) VALUES (?, ?, ?, ?, ?)",
                (user_id, preferred_gender, min_age, max_age, json.dumps(filter_data))
            )
            
        self.conn.commit()
    
    def get_user_filters(self, user_id: int) -> Dict:
        """Kullanıcının filtrelerini getir."""
        self.add_user(user_id)  # Make sure user exists
        
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM filters WHERE user_id = ?", (user_id,))
        result = cursor.fetchone()
        
        filters = {}
        if result:
            if result['preferred_gender']:
                filters['preferred_gender'] = result['preferred_gender']
            if result['min_age']:
                filters['min_age'] = result['min_age']
            if result['max_age']:
                filters['max_age'] = result['max_age']
            if result['filter_data']:
                try:
                    additional_data = json.loads(result['filter_data'])
                    filters.update(additional_data)
                except:
                    pass
        
        return filters
    
    def get_matching_waiting_user(self, user_id: int) -> Optional[int]:
        """Filtrelere göre eşleşen bekleyen bir kullanıcı bul."""
        user_filters = self.get_user_filters(user_id)
        user_profile = self.get_user_profile(user_id)
        
        # Bekleyen kullanıcılar listesinin bir kopyasını al
        for waiting_id in list(self.waiting_users):
            if waiting_id == user_id:
                continue  # Kendisiyle eşleştirme yapmaz
                
            # Kullanıcı hala bekliyor mu kontrol et
            if self.get_user_state(waiting_id) != WAITING:
                if waiting_id in self.waiting_users:
                    self.remove_from_waiting(waiting_id)
                continue
            
            # Karşı tarafın filtreleri ve profili
            waiting_filters = self.get_user_filters(waiting_id)
            waiting_profile = self.get_user_profile(waiting_id)
            
            # Filtre kontrolü
            if self.check_filter_match(user_id, waiting_id, user_profile, user_filters, 
                                     waiting_profile, waiting_filters):
                return waiting_id
                
        return None
    
    def check_filter_match(self, user1_id: int, user2_id: int, 
                          user1_profile: Dict, user1_filters: Dict,
                          user2_profile: Dict, user2_filters: Dict) -> bool:
        """İki kullanıcının filtreleri ve profillerinin eşleşip eşleşmediğini kontrol et."""
        # Her iki kullanıcı da filtre belirtmediyse, her zaman eşleşir
        if not user1_filters and not user2_filters:
            return True
        
        # Cinsiyet tercihi kontrolü
        if 'preferred_gender' in user1_filters and 'gender' in user2_profile:
            user1_pref = user1_filters['preferred_gender']
            user2_gender = user2_profile['gender']
            
            # Eğer tercih 'any' değilse ve cinsiyetler eşleşmiyorsa
            if user1_pref != 'any' and user1_pref != user2_gender:
                return False
        
        # Tersini de kontrol et
        if 'preferred_gender' in user2_filters and 'gender' in user1_profile:
            user2_pref = user2_filters['preferred_gender']
            user1_gender = user1_profile['gender']
            
            if user2_pref != 'any' and user2_pref != user1_gender:
                return False
        
        # Yaş aralığı kontrolü
        if 'min_age' in user1_filters and 'age' in user2_profile:
            if int(user2_profile['age']) < int(user1_filters['min_age']):
                return False
                
        if 'max_age' in user1_filters and 'age' in user2_profile:
            if int(user2_profile['age']) > int(user1_filters['max_age']):
                return False
        
        # Karşılıklı yaş kontrolü
        if 'min_age' in user2_filters and 'age' in user1_profile:
            if int(user1_profile['age']) < int(user2_filters['min_age']):
                return False
                
        if 'max_age' in user2_filters and 'age' in user1_profile:
            if int(user1_profile['age']) > int(user2_filters['max_age']):
                return False
        
        # Tüm kontrolleri geçtiysek, eşleşme vardır
        return True
    
    def get_waiting_user(self, exclude_id: int) -> Optional[int]:
        """Get a user who is waiting for a chat, except the specified user."""
        for user_id in self.waiting_users:
            if user_id != exclude_id:
                return user_id
        return None
    
    def create_chat(self, user1_id: int, user2_id: int) -> None:
        """Create a chat between two users."""
        # Set states and partners
        self.set_user_state(user1_id, CHATTING)
        self.set_user_state(user2_id, CHATTING)
        self.set_partner(user1_id, user2_id)
        self.set_partner(user2_id, user1_id)
        
        # Remove from waiting list
        self.remove_from_waiting(user1_id)
        self.remove_from_waiting(user2_id)
        
        # Add to active chats
        self.active_chats[user1_id] = user2_id
        self.active_chats[user2_id] = user1_id
    
    def end_chat(self, user_id: int) -> Optional[int]:
        """End an active chat for a user and return the partner's ID."""
        partner_id = self.get_partner(user_id)
        
        if partner_id:
            # Reset both users
            self.set_user_state(user_id, IDLE)
            self.set_partner(user_id, None)
            
            self.set_user_state(partner_id, IDLE)
            self.set_partner(partner_id, None)
            
            # Remove from active chats
            if user_id in self.active_chats:
                del self.active_chats[user_id]
            if partner_id in self.active_chats:
                del self.active_chats[partner_id]
            
            return partner_id
        
        return None
    
    def close(self):
        """Veritabanı bağlantısını kapat."""
        if self.conn:
            self.conn.close()

# Create a singleton instance of the database
db = Database()

# Uygulama kapanırken veritabanını kapatmak için
import atexit
atexit.register(db.close)