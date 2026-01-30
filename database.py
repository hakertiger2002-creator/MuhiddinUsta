import sqlite3
import datetime
from typing import List, Tuple, Optional
import os  # ✅ BU QATORNI QO'SHING!
import logging

logger = logging.getLogger(__name__)

class Database:
    def __init__(self, db_path: str = None):
        # ✅ RENDER uchun PERSISTENT yo'l
        render = os.getenv('RENDER', '').lower() == 'true'
        
        if render:
            # ✅ MUHIM: Render'da PERSISTENT yo'l
            # Bu yo'l deploy'lar orasida saqlanadi
            db_path = "/opt/render/project/src/persistent_data/database.db"
            
            # Papkani majburiy yaratish
            os.makedirs("/opt/render/project/src/persistent_data", exist_ok=True)
            
            logger.info(f"🎯 RENDER mode: Database yo'li: {db_path}")
            
            # Agar fayl yo'q bo'lsa, qo'shni papkadan qidirish
            if not os.path.exists(db_path):
                # Oldingi deploy'lardan qidirish
                possible_locations = [
                    "/opt/render/project/src/database.db",  # Oldingi joy
                    "database.db",  # Relative path
                ]
                
                for loc in possible_locations:
                    if os.path.exists(loc):
                        logger.info(f"📦 Oldingi database topildi: {loc}")
                        # Oldingi database'ni yangi joyga ko'chirish
                        import shutil
                        shutil.copy2(loc, db_path)
                        break
        else:
            # Local development
            if db_path is None:
                db_path = "database.db"
        
        self.db_path = db_path
        logger.info(f"📁 Database fayli: {db_path}")
        
        try:
            self.conn = sqlite3.connect(db_path, check_same_thread=False)
            logger.info("✅ Database connection ochildi")
            self.create_tables()
        except Exception as e:
            logger.error(f"❌ Database connection xatosi: {e}")
            raise
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Users jadvali
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            full_name TEXT,
            phone_number TEXT,
            language TEXT DEFAULT 'uz',
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0
        )''')
        
        # Contents jadvali - MUHIM!
        cursor.execute('''CREATE TABLE IF NOT EXISTS contents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            content_type TEXT,
            file_id TEXT,
            caption TEXT,
            added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')
        
        # Locations jadvali
        cursor.execute('''CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            full_name TEXT,
            phone_number TEXT,
            latitude REAL,
            longitude REAL,
            status TEXT DEFAULT 'pending',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            admin_notified INTEGER DEFAULT 0
        )''')
        
        self.conn.commit()
        logger.info("✅ Database jadvallari yaratildi/tekshirildi")
        
        # Statistikani log qilish
        cursor.execute("SELECT COUNT(*) FROM contents")
        content_count = cursor.fetchone()[0]
        logger.info(f"📊 Database'dagi kontentlar soni: {content_count}")
        
    def backup(self):
        """Database'ni zaxira nusxasini olish"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"backups/backup_database_{timestamp}.db"
        
        # Backups papkasini yaratish
        os.makedirs("backups", exist_ok=True)
        
        shutil.copy2("database.db", backup_file)
        print(f"✅ Database backed up to {backup_file}")
        
        # Eski backup'larni tozalash
        self._cleanup_old_backups()
        
        return backup_file
    
    def _cleanup_old_backups(self, max_backups=5):
        """Eski backup fayllarini o'chirish"""
        if not os.path.exists("backups"):
            return
        
        backup_files = []
        for file in os.listdir("backups"):
            if file.startswith("backup_database_") and file.endswith(".db"):
                file_path = os.path.join("backups", file)
                backup_files.append((file_path, os.path.getctime(file_path)))
        
        backup_files.sort(key=lambda x: x[1], reverse=True)
        
        if len(backup_files) > max_backups:
            for file_path, _ in backup_files[max_backups:]:
                os.remove(file_path)
                print(f"🗑️ Eski backup o'chirildi: {os.path.basename(file_path)}")
    
    def restore(self, backup_file):
        """Backup'dan restore qilish"""
        if not os.path.exists(backup_file):
            print("❌ Backup fayli topilmadi!")
            return False
        
        # Database yopish
        self.conn.close()
        
        # Asl faylni o'chirish
        if os.path.exists("database.db"):
            os.remove("database.db")
        
        # Backup'dan restore
        shutil.copy2(backup_file, "database.db")
        
        # Yangi connection ochish
        self.conn = sqlite3.connect("database.db", check_same_thread=False)
        
        print(f"✅ Database restored from {backup_file}")
        return True    
    
    def add_user(self, user_id: int, full_name: str, phone_number: str, language: str = 'uz'):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, full_name, phone_number, language) 
            VALUES (?, ?, ?, ?)
        ''', (user_id, full_name, phone_number, language))
        self.conn.commit()
    
    def get_user(self, user_id: int) -> Optional[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()
    
    def update_user_language(self, user_id: int, language: str):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET language = ? WHERE user_id = ?', (language, user_id))
        self.conn.commit()
    
    def is_user_registered(self, user_id: int) -> bool:
        user = self.get_user(user_id)
        return user is not None
    
    def get_all_users(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users')
        return cursor.fetchall()
    
    def get_active_users(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_blocked = 0')
        return cursor.fetchall()
    
    def get_blocked_users(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_blocked = 1')
        return cursor.fetchall()
    
    def block_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        
    def unblock_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
    
    def add_content(self, category: str, content_type: str, file_id: str, caption: str = ''):
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO contents (category, content_type, file_id, caption) 
            VALUES (?, ?, ?, ?)
        ''', (category, content_type, file_id, caption))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_contents_by_category(self, category: str, limit: int = 10, offset: int = 0) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM contents 
            WHERE category = ?
            ORDER BY added_at DESC 
            LIMIT ? OFFSET ?
        ''', (category, limit, offset))
        return cursor.fetchall()
    
    def count_contents_by_category(self, category: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM contents WHERE category = ?', (category,))
        return cursor.fetchone()[0]
    
    def get_content_by_id(self, content_id: int) -> Optional[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM contents WHERE id = ?', (content_id,))
        return cursor.fetchone()
    
    def get_all_categories(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT DISTINCT category FROM contents')
        return [row[0] for row in cursor.fetchall()]
    
    def delete_content(self, content_id: int):
        cursor = self.conn.cursor()
        cursor.execute('DELETE FROM contents WHERE id = ?', (content_id,))
        self.conn.commit()
    
    def get_all_contents(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM contents ORDER BY added_at DESC')
        return cursor.fetchall()
    
    def add_location(self, user_id: int, full_name: str, phone_number: str, 
                     latitude: float, longitude: float):
        cursor = self.conn.cursor()
        
        # Avval foydalanuvchining eski joylashuvini o'chiramiz
        cursor.execute('DELETE FROM locations WHERE user_id = ?', (user_id,))
        
        # Yangi joylashuvni qo'shamiz
        cursor.execute('''
            INSERT INTO locations (user_id, full_name, phone_number, latitude, longitude) 
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, full_name, phone_number, latitude, longitude))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def get_location_by_id(self, location_id: int):
        """ID bo'yicha joylashuvni olish"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM locations WHERE id = ?', (location_id,))
        return cursor.fetchone()
    
    def get_latest_locations(self, limit: int = 10):
        """Eng so'nggi joylashuvlarni olish"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM locations 
            ORDER BY sent_at DESC 
            LIMIT ?
        ''', (limit,))
        return cursor.fetchall()
    
    def get_pending_locations(self):
        """Kutilayotgan joylashuvlarni olish"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM locations WHERE status = "pending" ORDER BY sent_at DESC')
        return cursor.fetchall()
    
    def update_location_status(self, location_id: int, status: str):
        """Joylashuv holatini yangilash"""
        cursor = self.conn.cursor()
        cursor.execute('UPDATE locations SET status = ? WHERE id = ?', (status, location_id))
        self.conn.commit()
    
    def delete_old_locations(self, days: int = 7):
        """Eski joylashuvlarni o'chirish"""
        cursor = self.conn.cursor()
        cursor.execute('''
            DELETE FROM locations 
            WHERE sent_at < datetime('now', ?)
        ''', (f'-{days} days',))
        self.conn.commit()
        return cursor.rowcount
    
    def close(self):
        self.conn.close()
        
    # database.py fayliga quyidagi funksiyalarni qo'shing yoki mavjudlarini tekshiring:

    def get_user(self, user_id: int) -> Optional[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        return cursor.fetchone()

    def block_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        print(f"DEBUG: User {user_id} bloklandi")

    def unblock_user(self, user_id: int):
        cursor = self.conn.cursor()
        cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
        self.conn.commit()
        print(f"DEBUG: User {user_id} blokdan olindi")

    def get_blocked_users(self) -> List[Tuple]:
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE is_blocked = 1')
        return cursor.fetchall()    
        
    # database.py fayliga yangi funksiyalar qo'shing:

    def get_recent_users(self, days: int = 7) -> List[Tuple]:
        """So'nggi kunlarda ro'yxatdan o'tgan foydalanuvchilar"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM users 
            WHERE datetime(registered_at) > datetime('now', ?) 
            AND is_blocked = 0
            ORDER BY registered_at DESC
        ''', (f'-{days} days',))
        return cursor.fetchall()

    def get_users_by_language(self, language: str) -> List[Tuple]:
        """Til bo'yicha foydalanuvchilar"""
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM users WHERE language = ? AND is_blocked = 0', (language,))
        return cursor.fetchall()

    def get_user_stats(self) -> dict:
        """Foydalanuvchi statistikasi"""
        cursor = self.conn.cursor()
        
        # Jami foydalanuvchilar
        cursor.execute('SELECT COUNT(*) FROM users')
        total = cursor.fetchone()[0]
        
        # Faol foydalanuvchilar
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 0')
        active = cursor.fetchone()[0]
        
        # Bloklanganlar
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_blocked = 1')
        blocked = cursor.fetchone()[0]
        
        # So'nggi 24 soat
        cursor.execute('SELECT COUNT(*) FROM users WHERE datetime(registered_at) > datetime("now", "-1 day")')
        last_24h = cursor.fetchone()[0]
        
        # Til bo'yicha
        cursor.execute('SELECT language, COUNT(*) FROM users GROUP BY language')
        by_language = cursor.fetchall()
        
        return {
            'total': total,
            'active': active,
            'blocked': blocked,
            'last_24h': last_24h,
            'by_language': dict(by_language)
        }    

# Global database instance
db = Database()