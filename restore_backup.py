# restore_backup.py faylini yarating va RUN qiling
import os
import shutil
import glob

def find_latest_backup():
    """Eng so'nggi backup faylini topish"""
    backup_files = glob.glob("backups/*.db") + glob.glob("*.db.backup") + glob.glob("database_backup_*.db")
    
    if not backup_files:
        print("❌ Hech qanday backup topilmadi!")
        return None
    
    # Eng yangi faylni topish
    latest = max(backup_files, key=os.path.getctime)
    print(f"✅ Eng yangi backup: {latest}")
    return latest

def restore_database():
    """Database'ni restore qilish"""
    
    # 1. Backup topish
    backup_file = find_latest_backup()
    if not backup_file:
        return False
    
    # 2. Hozirgi database yo'lini aniqlash
    if os.getenv('RENDER', '').lower() == 'true':
        # Render uchun
        current_db_path = "/opt/render/project/src/database.db"
    else:
        current_db_path = "database.db"
    
    print(f"📁 Hozirgi database yo'li: {current_db_path}")
    
    # 3. Restore qilish
    try:
        # Papkani yaratish
        os.makedirs(os.path.dirname(current_db_path), exist_ok=True)
        
        # Backup'dan nusxalash
        shutil.copy2(backup_file, current_db_path)
        
        print(f"✅ Database restore qilindi!")
        print(f"📊 Fayl hajmi: {os.path.getsize(current_db_path) / 1024:.2f} KB")
        
        # 4. Tekshirish
        import sqlite3
        conn = sqlite3.connect(current_db_path)
        cursor = conn.cursor()
        
        # Kontentlarni hisoblash
        cursor.execute("SELECT COUNT(*) FROM contents")
        content_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        print(f"📂 Kontentlar: {content_count} ta")
        print(f"👥 Foydalanuvchilar: {user_count} ta")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Restore xatosi: {e}")
        return False

if __name__ == "__main__":
    restore_database()