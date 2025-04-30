# Picasso Anonim Chat Bot

Picasso Anonim Chat Bot, Telegram platformunda kullanıcıların birbirleriyle anonim olarak sohbet etmelerini sağlayan bir bot projesidir. Kullanıcılar cinsiyet, yaş gibi temel profil bilgilerini ayarlayabilir ve tercihlerine göre eşleşme yapabilirler.

## 🌟 Özellikler

- **Anonim Sohbet**: Kullanıcılar birbirleriyle kimliklerini açıklamadan sohbet edebilir
- **Profil Sistemi**: Cinsiyet ve yaş bilgisi tanımlama
- **Eşleşme Tercihleri**: Cinsiyet ve yaş aralığı bazlı filtreleme
- **Kolay Kullanım**: Basit komutlar ve sezgisel kullanıcı arayüzü
- **Türkçe Arayüz**: Tamamen Türkçe dil desteği

## 📋 Komutlar

- `/start` - Profil kurulumunu başlat
- `/find` - Sohbet partneri bul
- `/profile` - Profilinizi görüntüleyin veya düzenleyin
- `/stop` - Mevcut sohbeti sonlandır
- `/next` - Yeni bir partner bul
- `/clear` - Profilinizi ve tercihlerinizi sıfırlayın
- `/help` - Yardım mesajını göster
- `/filter` - Eşleşme tercihlerinizi ayarlayın

## 🚀 Kurulum

### Gereksinimler

- Python 3.8+
- python-telegram-bot kütüphanesi
- python-dotenv kütüphanesi

### Adımlar

1. Repoyu klonlayın:


2. Gerekli kütüphaneleri yükleyin:
```bash
pip install -r requirements.txt
```

3. `.env` dosyasını oluşturun:
```bash
cp .env
```

4. `.env` dosyasını düzenleyerek Telegram Bot Token bilginizi ekleyin:
```
TOKEN=your_bot_token_here
BOT_USERNAME=@your_bot_username
```

5. Botu çalıştırın:
```bash
python main.py
```

## 📚 Proje Yapısı

```
picasso_anonim_chat/
├── main.py                   # Ana uygulama dosyası
├── config.py                 # Yapılandırma değişkenleri ve sabitler
├── database.py               # Veritabanı işlemleri
├── .env                      # Çevre değişkenleri (gizli)
├── .env.example              # Örnek çevre değişkenleri dosyası
├── requirements.txt          # Bağımlılıklar
├── utils/
│   ├── __init__.py
│   └── helpers.py            # Yardımcı fonksiyonlar
└── handlers/
    ├── __init__.py
    ├── command_handlers.py   # Komut işleyicileri
    ├── message_handlers.py   # Mesaj işleyicileri
    └── profile_handlers.py   # Profil işleyicileri
```

## 🔒 Güvenlik

- Kullanıcı bilgileri gizli tutulur
- Bot, kullanıcıların gerçek kimliklerini veya iletişim bilgilerini paylaşmalarını engellemez, kullanıcıların kendi güvenliğinden kendileri sorumludur
- Token bilgileri `.env` dosyasında saklanır ve GitHub'a yüklenmez

## 🤝 Katkıda Bulunma

1. Bu repoyu forklayın
2. Yeni bir branch oluşturun (`git checkout -b feature/amazing-feature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some amazing feature'`)
4. Branch'inize push edin (`git push origin feature/amazing-feature`)
5. Pull Request açın
