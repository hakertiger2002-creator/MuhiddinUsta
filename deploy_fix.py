# deploy_fix.py - Render uchun tezkor fix
import os
import sys
import sqlite3

def fix_database():
    """Database muammolarini tuzatish"""
    
    print("🔧 Database fix jarayoni...")
    
    # Database yo'llari
    render_db_path = "/opt/render/project/src/database.db"
    persistent_path = "/opt/render/project/src/persistent_data/database.db"
    
    # 1. Agar persistent_data papkasi yo'q bo'lsa, yaratish
    os.makedirs("/opt/render/project/src/persistent_data", exist_ok=True)
    
    # 2. Agar asosiy database bo'sh bo'lsa, persistent'dan nusxalash
    if os.path.exists(persistent_path) and os.path.exists(render_db_path):
        # Ikki database'ni solishtirish
        import sqlite3
        
        conn1 = sqlite3.connect(render_db_path)
        cursor1 = conn1.cursor()
        cursor1.execute("SELECT COUNT(*) FROM contents")
        count1 = cursor1.fetchone()[0]
        conn1.close()
        
        conn2 = sqlite3.connect(persistent_path)
        cursor2 = conn2.cursor()
        cursor2.execute("SELECT COUNT(*) FROM contents")
        count2 = cursor2.fetchone()[0]
        conn2.close()
        
        print(f"📊 Asosiy database: {count1} ta kontent")
        print(f"📊 Persistent database: {count2} ta kontent")
        
        # Agar persistent'dada ko'p kontent bo'lsa, nusxalash
        if count2 > count1:
            print(f"🔄 Persistent database'dan asosiyga nusxalash...")
            import shutil
            shutil.copy2(persistent_path, render_db_path)
            print("✅ Database nusxalandi!")
    
    # 3. Agar hech qanday database bo'lmasa, qo'shimcha yo'llardan qidirish
    elif not os.path.exists(render_db_path):
        possible_backups = [
            "/opt/render/project/src/persistent_data/database.db",
            "database.db",
            "/data/database.db",
            "/tmp/database.db",
        ]
        
        for backup in possible_backups:
            if os.path.exists(backup):
                print(f"✅ Backup topildi: {backup}")
                import shutil
                shutil.copy2(backup, render_db_path)
                print("✅ Database restore qilindi!")
                break
    
    print("✅ Fix jarayoni tugadi!")

if __name__ == "__main__":
    fix_database()