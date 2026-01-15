# database.py faylini shunday o'zgartiring:

import sqlite3
import datetime
from typing import List, Tuple, Optional

class Database:
    def __init__(self, db_path: str = "database.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
    
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
        
        # Kontentlar jadvali - protection_level ustuni O'CHIRILDI
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
        
        # Joylashuvlar jadvali
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS locations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                full_name TEXT,
                phone_number TEXT,
                latitude REAL,
                longitude REAL,
                status TEXT DEFAULT 'pending',
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                admin_notified INTEGER DEFAULT 0
            )
        ''')
        
        self.conn.commit()
    
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