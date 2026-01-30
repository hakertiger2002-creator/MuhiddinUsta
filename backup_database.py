# backup_database.py faylini yarating
import shutil
import datetime
import os

def backup_database():
    # Backup papkasini yaratish
    os.makedirs("backups", exist_ok=True)
    
    # Backup fayli nomi
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"backups/database_backup_{timestamp}.db"
    
    # Database ni nusxalash
    shutil.copy2("database.db", backup_file)
    
    print(f"✅ Database backup qilindi: {backup_file}")
    return backup_file

if __name__ == "__main__":
    backup_database()