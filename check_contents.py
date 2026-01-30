# check_contents.py faylini yarating
from database import db

def check_contents():
    print("📊 DATABASE HOLATINI TEKSHIRISH")
    print("=" * 40)
    
    # Kontentlar soni
    contents = db.get_all_contents()
    print(f"📂 Jami kontentlar: {len(contents)}")
    
    # Kategoriya bo'yicha
    categories = db.get_all_categories()
    print(f"📁 Kategoriyalar: {len(categories)}")
    
    for cat in categories:
        count = db.count_contents_by_category(cat)
        print(f"  • {cat}: {count} ta")
    
    # Foydalanuvchilar
    users = db.get_all_users()
    print(f"👥 Jami foydalanuvchilar: {len(users)}")
    
    # Joylashuvlar
    from database import db
    import sqlite3
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM locations")
    locations_count = cursor.fetchone()[0]
    print(f"📍 Joylashuvlar: {locations_count} ta")
    
    print("=" * 40)
    print("✅ Barcha ma'lumotlar saqlangan!")

if __name__ == "__main__":
    check_contents()