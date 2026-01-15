# recreate_simple_database.py
import os
import sqlite3

def recreate_simple_database():
    # Eski faylni o'chirish
    if os.path.exists("database.db"):
        os.remove("database.db")
        print("✅ Eski database fayli o'chirildi")
    
    # Yangi database yaratish
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT,
            language TEXT DEFAULT 'uz',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0
        )
    ''')
    
    # Kontentlar jadvali (soddalashtirilgan)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            content_type TEXT,
            file_id TEXT,
            caption TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
  # Admin foydalanuvchi qo'shish
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, full_name, phone_number, language, is_blocked)
        VALUES (?, ?, ?, ?, ?)
    ''', (123456789, "Muhiddin Admin", Config.MASTER_PHONE, "uz", 0))
    
    conn.commit()
    conn.close()
    
    print("✅ Yangi database yaratildi")
    print("✅ Jadval strukturalari to'g'ri o'rnatildi")
    print("✅ Admin foydalanuvchi qo'shildi")
    print("✅ Database muvaffaqiyatli yangilandi!")

if __name__ == "__main__":
    recreate_simple_database()