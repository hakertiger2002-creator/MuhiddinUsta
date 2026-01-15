# config.py
import os
from dotenv import load_dotenv
from config import Config

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    ADMIN_ID = int(os.getenv("ADMIN_ID"))
    RENDER = os.getenv("RENDER", "False").lower() == "true"
    
    # Database
    DATABASE_PATH = "database.db"
    
    # Bot sozlamalari
    WEBHOOK_URL = None  # Agar webhook ishlatilsa
    PORT = 8080 if RENDER else 8000
    HOST = "0.0.0.0" if RENDER else "127.0.0.1"
    
    # Himoya sozlamalari
    PROTECTION_LEVEL = 3  # 1-3 oralig'ida (3 - eng yuqori)
    
    # Til sozlamalari
    DEFAULT_LANGUAGE = 'uz'
    SUPPORTED_LANGUAGES = ['uz', 'ru']
    
    # ✅ YANGI: Usta nomi va telefon raqami
    MASTER_NAME = "Muhiddin Usta"
    MASTER_PHONE = "+998880445550"
    BOT_USERNAME = "MuhiddinUsta_bot"