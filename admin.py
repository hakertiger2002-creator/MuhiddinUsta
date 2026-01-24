# admin.py - TO'LIQ YANGILASH (JOYLASHUVLAR PANELI BILAN)

from aiogram import Bot, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    Message, CallbackQuery,
    PhotoSize, Video, Document,
    InlineKeyboardMarkup, InlineKeyboardButton,
    Location
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

from database import db
import asyncio
import logging
from datetime import datetime, timedelta

# ✅ TO'G'RI: AdminStates class'ini bu yerda yaratamiz (FAQAT BIR MARTTA)
class AdminStates(StatesGroup):
    # Kontent qo'shish
    adding_content = State()
    waiting_for_content = State()
    waiting_for_caption = State()
    
    # Xabar yuborish
    sending_message = State()
    waiting_broadcast_text = State()
    waiting_broadcast_photo = State()
    waiting_broadcast_video = State()
    waiting_broadcast_document = State()
    
    # Bloklash
    blocking_user = State()
    unblocking_user = State()
    
    # Kontent o'chirish
    deleting_content = State()
    waiting_content_id = State()
    
    # Odam qo'shish
    adding_user = State()
    waiting_for_user_fullname = State()
    waiting_for_user_phone = State()
    waiting_for_user_language = State()

# ✅ Bot va admin ID uchun global o'zgaruvchilar
bot_instance = None  # Bot instansiyasini saqlash uchun
ADMIN_ID = None

def set_bot_and_admin(bot_instance_param, admin_id):
    """Bot va admin ID ni sozlash"""
    global bot_instance, ADMIN_ID
    bot_instance = bot_instance_param
    ADMIN_ID = admin_id

# Logging
logger = logging.getLogger(__name__)

# ==================== ASOSIY KLAVIATURALAR ====================

def get_admin_keyboard():
    """Asosiy admin panel klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Foydalanuvchilar Ma'lumotlari"), KeyboardButton(text="📨 Xabar Yuborish")],
            [KeyboardButton(text="➕ Kontent Qo'shish"), KeyboardButton(text="🗑️ Kontent O'chirish")],
            [KeyboardButton(text="👥 Odam Qo'shish"), KeyboardButton(text="📋 Kontentlar Ro'yxati")],
            [KeyboardButton(text="🚫 Bloklash"), KeyboardButton(text="✅ Blokdan Ochish")],
            [KeyboardButton(text="📍 Joylashuvlarni Boshqarish"), KeyboardButton(text="🔙 Asosiy Menyuga Qaytish")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_locations_management_keyboard():
    """Joylashuvlarni boshqarish klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 Eng so'nggi joylashuv"), KeyboardButton(text="📋 Barcha joylashuvlar")],
            [KeyboardButton(text="🔄 Joylashuvlarni yangilash"), KeyboardButton(text="🗑️ Eski joylashuvlar")],
            [KeyboardButton(text="✅ Tasdiqlanganlar"), KeyboardButton(text="❌ Rad etilganlar")],
            [KeyboardButton(text="⏳ Kutilayotganlar"), KeyboardButton(text="🔙 Admin Menyuga")]
        ],
        resize_keyboard=True,
        persistent=True
    )

def get_content_categories_keyboard(action: str = "add"):
    """Kontent kategoriyalari klaviaturasi"""
    if action == "add":
        text = "📂 Kontent qo'shish uchun kategoriyani tanlang:"
        keyboard = [
            [KeyboardButton(text="🛠️ Klassik Tamirlash"), KeyboardButton(text="🎨 Lepka Yopishtirish")],
            [KeyboardButton(text="🏠 Gipsi Carton Fason"), KeyboardButton(text="💻 HiTech Tamirlash")],
            [KeyboardButton(text="🔨 To'liq Tamirlash"), KeyboardButton(text="📹 Video Joylash")],
            [KeyboardButton(text="🔙 Orqaga")]
        ]
    else:  # delete
        text = "🗑️ O'chirish uchun kategoriyani tanlang:"
        keyboard = [
            [KeyboardButton(text="🛠️ Klassik Tamirlash"), KeyboardButton(text="🎨 Lepka Yopishtirish")],
            [KeyboardButton(text="🏠 Gipsi Carton Fason"), KeyboardButton(text="💻 HiTech Tamirlash")],
            [KeyboardButton(text="🔨 To'liq Tamirlash"), KeyboardButton(text="📹 Video Joylash")],
            [KeyboardButton(text="🔙 Orqaga")]
        ]
    
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True), text

def get_content_type_keyboard():
    """Kontent turi klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼️ Rasm"), KeyboardButton(text="📹 Video")],
            [KeyboardButton(text="📄 Dokument"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def get_back_keyboard():
    """Orqaga klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def get_user_language_keyboard():
    """Foydalanuvchi tili uchun klaviatura"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")],
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

# ==================== JOYLASHUVLAR PANELI ====================

async def show_latest_locations(message: Message):
    """Eng so'nggi joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations(limit=10)
    
    if not locations:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Yangilash",
                    callback_data="refresh_locations_admin"
                )
            ]
        ])
        
        await message.answer(
            "📍 <b>Hech qanday joylashuv yo'q.</b>\n\n"
            "Foydalanuvchilar joylashuv yuborganda, bu yerda ko'rinadi.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Eng so'nggi joylashuvni ko'rsatish
    latest_location = locations[0]
    await show_location_details(message, latest_location, "latest")

async def show_location_details(message: Message, location_data, source="list"):
    """Joylashuv tafsilotlarini ko'rsatish"""
    location_id = location_data[0]
    user_name = location_data[2]
    phone = location_data[3]
    latitude = location_data[4]
    longitude = location_data[5]
    status = location_data[6]
    sent_time = location_data[7]
    
    # Vaqtni formatlash
    if isinstance(sent_time, str):
        date_part = sent_time.split()[0]
        time_part = sent_time.split()[1][:5] if len(sent_time.split()) > 1 else "00:00"
    else:
        date_part = str(sent_time)[:10]
        time_part = str(sent_time)[11:16]
    
    # Status ranglari
    status_icons = {
        'pending': '🟡 Kutilmoqda',
        'accepted': '🟢 Tasdiqlangan', 
        'rejected': '🔴 Rad etilgan'
    }
    status_display = status_icons.get(status, status)
    
    # Joylashuv haqida ma'lumot
    location_info = f"""📍 <b>JOYLASHUV #{location_id}</b>

{status_display}
👤 <b>Foydalanuvchi:</b> {user_name}
📞 <b>Telefon:</b> {phone}
📅 <b>Sana:</b> {date_part}
⏰ <b>Vaqt:</b> {time_part}
🌐 <b>Koordinatalar:</b>
   • Kenglik: {latitude}
   • Uzunlik: {longitude}

🎯 <b>Harakatlar:</b>"""

    # Inline klaviatura
    keyboard_buttons = []
    
    # Joylashuvni ko'rish
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="📍 Joylashuvni ko'rish",
            callback_data=f"view_location:{location_id}"
        )
    ])
    
    # Status tugmalari (faqat kutilayotgan joylashuv uchun)
    if status == 'pending':
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"accept_location:{location_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"reject_location:{location_id}"
            )
        ])
    
    # Navigatsiya tugmalari
    nav_buttons = []
    
    if source == "latest":
        nav_buttons.append(
            InlineKeyboardButton(
                text="📋 Barcha joylashuvlar",
                callback_data="view_all_locations_admin"
            )
        )
    
    nav_buttons.append(
        InlineKeyboardButton(
            text="🔄 Yangilash",
            callback_data="refresh_locations_admin"
        )
    )
    
    if nav_buttons:
        keyboard_buttons.append(nav_buttons)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(location_info, reply_markup=keyboard, parse_mode="HTML")

async def show_all_locations_admin(message: Message):
    """Barcha joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations(limit=50)
    
    if not locations:
        await message.answer("📭 Hech qanday joylashuv yo'q.")
        return
    
    # Kategoriya bo'yicha filtrlash tugmalari
    category_keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏳ Kutilayotgan", callback_data="filter_status:pending"),
            InlineKeyboardButton(text="✅ Tasdiqlangan", callback_data="filter_status:accepted"),
            InlineKeyboardButton(text="❌ Rad etilgan", callback_data="filter_status:rejected")
        ],
        [
            InlineKeyboardButton(text="📊 Barchasi", callback_data="filter_status:all"),
            InlineKeyboardButton(text="📅 Bugungi", callback_data="filter_today")
        ],
        [
            InlineKeyboardButton(text="📍 Eng so'nggi", callback_data="view_latest_location"),
            InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_locations_admin")
        ]
    ])
    
    # Statistikani hisoblash
    pending_count = len([loc for loc in locations if loc[6] == 'pending'])
    accepted_count = len([loc for loc in locations if loc[6] == 'accepted'])
    rejected_count = len([loc for loc in locations if loc[6] == 'rejected'])
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = len([loc for loc in locations if str(loc[7]).startswith(today)])
    
    stats_text = f"""📊 <b>JOYLASHUV STATISTIKASI</b>

📍 <b>Jami joylashuvlar:</b> {len(locations)}
⏳ <b>Kutilayotgan:</b> {pending_count}
✅ <b>Tasdiqlangan:</b> {accepted_count}
❌ <b>Rad etilgan:</b> {rejected_count}
📅 <b>Bugungi:</b> {today_count}

🔍 <b>Filtr:</b> Barchasi"""

    await message.answer(stats_text, reply_markup=category_keyboard, parse_mode="HTML")
    
    # Joylashuvlar ro'yxati (faqat 10 tasi)
    locations_text = "<b>📋 JOYLASHUVLAR RO'YXATI:</b>\n\n"
    
    for i, loc in enumerate(locations[:10], 1):
        location_id = loc[0]
        user_name = loc[2]
        phone = loc[3]
        status = loc[6]
        
        # Status belgilari
        status_icon = "🟡" if status == 'pending' else "🟢" if status == 'accepted' else "🔴"
        
        # Telefon formatlash
        formatted_phone = phone if len(phone) <= 15 else f"{phone[:12]}..."
        
        locations_text += f"{i}. {status_icon} <b>#{location_id}</b> - {user_name}\n"
        locations_text += f"   📞 {formatted_phone}\n"
        
        # Vaqt
        sent_time = loc[7]
        if isinstance(sent_time, str):
            time_part = sent_time.split()[1][:5] if len(sent_time.split()) > 1 else ""
            if time_part:
                locations_text += f"   ⏰ {time_part}\n"
        
        locations_text += "   ─" * 15 + "\n"
    
    if len(locations) > 10:
        locations_text += f"\n📄 ... va yana {len(locations) - 10} ta joylashuv"
    
    # Joylashuvlar ro'yxati uchun tugmalar
    list_keyboard_buttons = []
    
    # Har bir joylashuv uchun tugma (faqat 5 tasi)
    for loc in locations[:5]:
        location_id = loc[0]
        user_name = loc[2]
        status = loc[6]
        
        status_icon = "🟡" if status == 'pending' else "🟢" if status == 'accepted' else "🔴"
        
        list_keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{status_icon} #{location_id} ({user_name[:15]}{'...' if len(user_name) > 15 else ''})",
                callback_data=f"view_location:{location_id}"
            )
        ])
    
    list_keyboard_buttons.append([
        InlineKeyboardButton(text="📍 Eng so'nggisi", callback_data="view_latest_location"),
        InlineKeyboardButton(text="🔄 Yangilash", callback_data="refresh_locations_admin")
    ])
    
    list_keyboard = InlineKeyboardMarkup(inline_keyboard=list_keyboard_buttons)
    
    await message.answer(locations_text, reply_markup=list_keyboard, parse_mode="HTML")

async def show_pending_locations(message: Message):
    """Kutilayotgan joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_pending_locations()
    
    if not locations:
        await message.answer("⏳ Hech qanday kutilayotgan joylashuv yo'q.")
        return
    
    text = f"⏳ <b>KUTILAYOTGAN JOYLASHUVLAR ({len(locations)} ta)</b>\n\n"
    
    for i, loc in enumerate(locations, 1):
        location_id = loc[0]
        user_name = loc[2]
        phone = loc[3]
        sent_time = loc[7].split()[1][:5] if isinstance(loc[7], str) else str(loc[7])[11:16]
        
        text += f"{i}. 🟡 <b>#{location_id}</b> - {user_name}\n"
        text += f"   📞 {phone} | ⏰ {sent_time}\n"
        text += "   ─" * 15 + "\n"
    
    # Tugmalar
    keyboard_buttons = []
    
    for loc in locations[:3]:
        location_id = loc[0]
        user_name = loc[2]
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📍 #{location_id} ({user_name[:10]}...)",
                callback_data=f"view_location:{location_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="✅ Hammasini tasdiqlash", callback_data="accept_all_pending"),
        InlineKeyboardButton(text="❌ Hammasini rad etish", callback_data="reject_all_pending")
    ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(text="📋 Barcha joylashuvlar", callback_data="view_all_locations_admin"),
        InlineKeyboardButton(text="📍 Eng so'nggisi", callback_data="view_latest_location")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

async def show_accepted_locations(message: Message):
    """Tasdiqlangan joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations(limit=50)
    accepted_locations = [loc for loc in locations if loc[6] == 'accepted']
    
    if not accepted_locations:
        await message.answer("✅ Hech qanday tasdiqlangan joylashuv yo'q.")
        return
    
    text = f"✅ <b>TASDIQLANGAN JOYLASHUVLAR ({len(accepted_locations)} ta)</b>\n\n"
    
    for i, loc in enumerate(accepted_locations[:10], 1):
        location_id = loc[0]
        user_name = loc[2]
        phone = loc[3]
        sent_time = loc[7].split()[1][:5] if isinstance(loc[7], str) else str(loc[7])[11:16]
        
        text += f"{i}. 🟢 <b>#{location_id}</b> - {user_name}\n"
        text += f"   📞 {phone} | ⏰ {sent_time}\n"
        text += "   ─" * 15 + "\n"
    
    if len(accepted_locations) > 10:
        text += f"\n📄 ... va yana {len(accepted_locations) - 10} ta joylashuv"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Barcha joylashuvlar", callback_data="view_all_locations_admin"),
            InlineKeyboardButton(text="📍 Eng so'nggisi", callback_data="view_latest_location")
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

async def show_rejected_locations(message: Message):
    """Rad etilgan joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations(limit=50)
    rejected_locations = [loc for loc in locations if loc[6] == 'rejected']
    
    if not rejected_locations:
        await message.answer("❌ Hech qanday rad etilgan joylashuv yo'q.")
        return
    
    text = f"❌ <b>RAD ETILGAN JOYLASHUVLAR ({len(rejected_locations)} ta)</b>\n\n"
    
    for i, loc in enumerate(rejected_locations[:10], 1):
        location_id = loc[0]
        user_name = loc[2]
        phone = loc[3]
        sent_time = loc[7].split()[1][:5] if isinstance(loc[7], str) else str(loc[7])[11:16]
        
        text += f"{i}. 🔴 <b>#{location_id}</b> - {user_name}\n"
        text += f"   📞 {phone} | ⏰ {sent_time}\n"
        text += "   ─" * 15 + "\n"
    
    if len(rejected_locations) > 10:
        text += f"\n📄 ... va yana {len(rejected_locations) - 10} ta joylashuv"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Barcha joylashuvlar", callback_data="view_all_locations_admin"),
            InlineKeyboardButton(text="📍 Eng so'nggisi", callback_data="view_latest_location")
        ],
        [
            InlineKeyboardButton(text="🗑️ Barchasini o'chirish", callback_data="delete_all_rejected")
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

async def delete_old_locations(message: Message):
    """Eski joylashuvlarni o'chirish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🗑️ 7 kun oldingilarni o'chirish", callback_data="delete_old:7"),
            InlineKeyboardButton(text="🗑️ 30 kun oldingilarni o'chirish", callback_data="delete_old:30")
        ],
        [
            InlineKeyboardButton(text="❌ Rad etilganlarni o'chirish", callback_data="delete_all_rejected"),
            InlineKeyboardButton(text="🔙 Orqaga", callback_data="locations_management_back")
        ]
    ])
    
    total_locations = len(db.get_latest_locations(limit=1000))
    
    await message.answer(
        f"🗑️ <b>ESKI JOYLASHUVLARNI O'CHIRISH</b>\n\n"
        f"📊 Jami joylashuvlar: {total_locations}\n\n"
        f"<i>Qaysi joylashuvlarni o'chirmoqchisiz?</i>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ==================== KONTENT QO'SHISH ====================

# Kontent qo'shishni boshlash
async def start_adding_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # FSM holatini aniq o'rnatish
    await state.set_state(AdminStates.adding_content)
    
    keyboard, text = get_content_categories_keyboard("add")
    
    await message.answer(text, reply_markup=keyboard)

# Kategoriyani tanlash
async def process_content_category(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Kategoriya mapping
    categories_map = {
        # Admin panel tugmalari
        "🛠️ Klassik Tamirlash": "classic",
        "🎨 Lepka Yopishtirish": "glue", 
        "🏠 Gipsi Carton Fason": "gypsum",
        "💻 HiTech Tamirlash": "hitech",
        "🔨 To'liq Tamirlash": "full",
        "📹 Video Joylash": "video",
        
        # Asosiy menyu tugmalari (O'zbek)
        "Klassik Tamirlash": "classic",
        "Lepka Yopishtirish": "glue",
        "Gipsi Carton Fason": "gypsum", 
        "HiTech Tamirlash": "hitech",
        "To'liq Tamirlash": "full",
        "Video Ishlar": "video",
        
        # Asosiy menyu tugmalari (Rus)
        "Классический Ремонт": "classic",
        "Поклейка Обоев": "glue",
        "Гипсокартон Фасон": "gypsum",
        "HiTech Ремонт": "hitech",
        "Полный Ремонт": "full",
        "Видео Работы": "video"
    }
    
    current_state = await state.get_state()
    
    # AGAR ADMIN PANEL HOLATIDA BO'LSA (adding_content)
    if current_state == AdminStates.adding_content.state:
        if message.text in categories_map:
            # Kategoriyani saqlash
            category_code = categories_map[message.text]
            await state.update_data(category=category_code)
            await state.set_state(AdminStates.waiting_for_content)
            
            await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
            return
        elif message.text == "🔙 Orqaga":
            await state.clear()
            await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
            return
        else:
            if "To'liq Tamirlash" in message.text or "Полный Ремонт" in message.text:
                await state.update_data(category="full")
                await state.set_state(AdminStates.waiting_for_content)
                await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
                return
    
    await message.answer("❌ Kategoriya tanlashda xatolik!")

# Kontent turini tanlash
async def process_content_type(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    content_types = {
        "🖼️ Rasm": "photo",
        "📹 Video": "video",
        "📄 Dokument": "document"
    }
    
    if message.text not in content_types:
        if message.text == "🔙 Orqaga":
            keyboard, text = get_content_categories_keyboard("add")
            await message.answer(text, reply_markup=keyboard)
            await state.set_state(AdminStates.adding_content)
            return
        await message.answer("❌ Iltimos, ro'yxatdagi turlardan birini tanlang!")
        return
    
    await state.update_data(content_type=content_types[message.text])
    
    await message.answer("📤 Iltimos, faylni yuboring (rasm, video yoki dokument):", reply_markup=get_back_keyboard())
    await state.set_state(AdminStates.waiting_for_caption)

async def process_content_file(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Agar foydalanuvchi orqaga qaytishni xohlasa
    if message.text and message.text == "🔙 Orqaga":
        await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
        await state.set_state(AdminStates.waiting_for_content)
        return
    
    data = await state.get_data()
    category = data.get('category')
    content_type = data.get('content_type')
    
    file_id = None
    caption = message.caption or ""
    
    # Fayl ID sini olish
    if content_type == "photo" and message.photo:
        file_id = message.photo[-1].file_id
    elif content_type == "video" and message.video:
        file_id = message.video.file_id
    elif content_type == "document" and message.document:
        file_id = message.document.file_id
    else:
        await message.answer("❌ Iltimos, to'g'ri formatdagi faylni yuboring!", reply_markup=get_back_keyboard())
        return
    
    # Faqat admin yozgan caption saqlanadi
    protected_caption = caption
    
    # Bazaga saqlash
    try:
        content_id = db.add_content(category, content_type, file_id, protected_caption)
        
        # Kategoriya nomi
        category_names = {
            "classic": "Klassik Tamirlash",
            "glue": "Lepka Yopishtirish",
            "gypsum": "Gipsi Carton Fason",
            "hitech": "HiTech Tamirlash",
            "full": "To'liq Tamirlash",
            "video": "Video Joylash"
        }
        
        category_name = category_names.get(category, category)
        
        success_message = (
            f"✅ Kontent muvaffaqiyatli qo'shildi!\n\n"
            f"📁 Kategoriya: {category_name}\n"
            f"📄 Tur: {content_type}\n"
            f"🆔 ID: {content_id}"
        )
        
        if caption:
            success_message += f"\n📝 Izoh: {caption[:50] + '...' if len(caption) > 50 else caption}"
        
        await message.answer(success_message)
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    # Admin panelga qaytish
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await state.clear()

# ==================== FOYDALANUVCHILAR MA'LUMOTLARI ====================

# Foydalanuvchilar ma'lumotlari
async def show_users_info(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    users = db.get_all_users()
    if not users:
        await message.answer("📭 Hech qanday foydalanuvchi topilmadi.")
        return
    
    active_users = db.get_active_users()
    blocked_users = db.get_blocked_users()
    
    text = "📊 FOYDALANUVCHILAR STATISTIKASI\n\n"
    text += f"👥 Jami foydalanuvchilar: {len(users)}\n"
    text += f"✅ Faol foydalanuvchilar: {len(active_users)}\n"
    text += f"🚫 Bloklanganlar: {len(blocked_users)}\n"
    text += "------------------------------\n\n"
    text += "📋 So'ngi 10 ta foydalanuvchi:\n\n"
    
    for user in users[-10:]:
        status = "🚫 Bloklangan" if user[5] == 1 else "✅ Faol"
        reg_date = user[4].split()[0] if isinstance(user[4], str) else str(user[4])[:10]
        text += f"👤 ID: {user[0]}\nIsm: {user[1]}\nTel: {user[2]}\nTil: {user[3]}\nRo'yxatdan: {reg_date}\nHolat: {status}\n--------------------\n"
    
    await message.answer(text, parse_mode=ParseMode.HTML)

# ==================== ODAM QO'SHISH ====================

async def start_adding_user(message: Message, state: FSMContext):
    """Odam qo'shishni boshlash"""
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminStates.waiting_for_user_fullname)
    
    await message.answer(
        "👤 <b>YANGI FOYDALANUVCHI QO'SHISH</b>\n\n"
        "Iltimos, foydalanuvchining to'liq ismini kiriting:",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )

async def process_user_fullname(message: Message, state: FSMContext):
    """Foydalanuvchi ismini qabul qilish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()
        return
    
    # Ismni saqlash
    await state.update_data(full_name=message.text)
    
    await message.answer(
        "📞 <b>Telefon raqamini kiriting:</b>\n\n"
        "<i>Namuna: 901234567 yoki +998901234567</i>",
        parse_mode="HTML",
        reply_markup=get_back_keyboard()
    )
    
    await state.set_state(AdminStates.waiting_for_user_phone)

async def process_user_phone(message: Message, state: FSMContext):
    """Foydalanuvchi telefon raqamini qabul qilish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await start_adding_user(message, state)
        return
    
    # Telefon raqamini tozalash
    phone = message.text.strip()
    phone = phone.replace("+", "").replace(" ", "").replace("-", "")
    
    # Faqat raqamlar qolishi kerak
    if not phone.isdigit():
        await message.answer(
            "❌ <b>Noto'g'ri telefon raqami!</b>\n\n"
            "Iltimos, faqat raqamlardan foydalaning:\n"
            "<code>901234567</code> yoki <code>998901234567</code>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Uzbekiston raqamini tekshirish
    if len(phone) == 9:
        # 9 xonali (901234567) - +998 qo'shamiz
        phone = f"+998{phone}"
    elif len(phone) == 12 and phone.startswith("998"):
        # 12 xonali (998901234567) - + qo'shamiz
        phone = f"+{phone}"
    else:
        await message.answer(
            "❌ <b>Noto'g'ri uzunlik!</b>\n\n"
            "To'g'ri formatlar:\n"
            "• 9 xonali: <code>901234567</code>\n"
            "• 12 xonali: <code>998901234567</code>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        return
    
    await state.update_data(phone_number=phone)
    
    await message.answer(
        "🌐 <b>Tilni tanlang:</b>",
        parse_mode="HTML",
        reply_markup=get_user_language_keyboard()
    )
    
    await state.set_state(AdminStates.waiting_for_user_language)

async def process_user_language(message: Message, state: FSMContext):
    """Foydalanuvchi tilini qabul qilish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer(
            "📞 <b>Telefon raqamini kiriting:</b>\n\n"
            "<i>Namuna: 901234567 yoki +998901234567</i>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_user_phone)
        return
    
    lang_map = {
        "🇺🇿 O'zbek": "uz",
        "🇷🇺 Русский": "ru"
    }
    
    if message.text not in lang_map:
        await message.answer(
            "❌ Iltimos, ro'yxatdagi tillardan birini tanlang!",
            reply_markup=get_user_language_keyboard()
        )
        return
    
    language = lang_map[message.text]
    
    # Barcha ma'lumotlarni olish
    data = await state.get_data()
    full_name = data.get('full_name', 'Noma\'lum')
    phone_number = data.get('phone_number', 'Noma\'lum')
    
    if full_name == 'Noma\'lum' or phone_number == 'Noma\'lum':
        await message.answer(
            "❌ <b>Ma'lumotlar yetarli emas!</b>\n\n"
            "Iltimos, qaytadan urinib ko'ring.",
            parse_mode="HTML"
        )
        await state.clear()
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        return
    
    # Avtomatik user_id yaratish (9 xonali)
    import random
    user_id = random.randint(100000000, 999999999)
    
    # Bazaga qo'shish
    try:
        db.add_user(user_id, full_name, phone_number, language)
        
        # Bot username'ini olish
        try:
            from main import BOT_USERNAME
            bot_username = BOT_USERNAME if BOT_USERNAME else "UstaElbek_bot"
        except:
            bot_username = "UstaElbek_bot"
        
        # 1. Bot havolasi
        bot_deep_link = f"https://t.me/{bot_username}?start={user_id}"
        
        # 2. Telegram telefon havolasi
        clean_phone = phone_number.replace("+", "").replace(" ", "")
        telegram_link = f"https://t.me/+{clean_phone}"
        
        # Admin uchun asosiy xabar
        success_message = (
            f"✅ <b>YANGI FOYDALANUVCHI QO'SHILDI!</b>\n\n"
            f"👤 <b>Ism:</b> {full_name}\n"
            f"🆔 <b>ID:</b> {user_id}\n"
            f"📞 <b>Telefon:</b> {phone_number}\n"
            f"🌐 <b>Til:</b> {message.text}\n\n"
            f"📊 <b>Jami foydalanuvchilar:</b> {len(db.get_all_users())}"
        )
        
        await message.answer(success_message, parse_mode="HTML")
        
        # ✅ AVTOMATIK RAVISHDA FOYDALANUVCHI TELEGRAM PROFILIGA HAVOLA
        telegram_link_message = (
            f"🔗 <b>TELEGRAM PROFIL HAVOLASI:</b>\n\n"
            f"📱 <b>Foydalanuvchi telefon raqami:</b> {phone_number}\n"
            f"👤 <b>Ism:</b> {full_name}\n\n"
            f"🔗 <b>Telegram profil havolasi:</b>\n"
            f"<code>{telegram_link}</code>\n\n"
            f"🤖 <b>Bot havolasi:</b>\n"
            f"<code>{bot_deep_link}</code>\n\n"
            f"📝 <b>Ko'rsatma:</b>\n"
            f"1. Foydalanuvchining Telegram profiliga <code>{telegram_link}</code> havolasi orqali o'ting\n"
            f"2. Unga <code>{bot_deep_link}</code> havolasini yuboring\n"
            f"3. Foydalanuvchi havolani bosgandan so'ng botga qo'shiladi"
        )
        
        await message.answer(telegram_link_message, parse_mode="HTML")
        
        # ✅ TELEGRAM PROFIL HAVOLASINI KLIK QILISH UCHUN INLINE TUGMA
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📱 Telegram Profiliga O'tish",
                    url=telegram_link
                )
            ],
            [
                InlineKeyboardButton(
                    text="🤖 Bot Havolasini Nusxalash",
                    callback_data=f"copy_link:{bot_deep_link}"
                )
            ]
        ])
        
        await message.answer(
            f"🖱️ <b>Bir klik bilan ochish:</b>\n\n"
            f"Quyidagi tugma orqali foydalanuvchining Telegram profiliga o'ting va "
            f"unga bot havolasini yuboring:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    # Admin panelga qaytish
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await state.clear()

# ==================== XABAR YUBORISH ====================

async def start_broadcast(message: Message, state: FSMContext):
    """Xabar yuborishni boshlash"""
    if message.from_user.id != ADMIN_ID:
        return
    
    # Yangi klaviatura
    broadcast_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📝 Matnli reklama"), KeyboardButton(text="🖼️ Rasmli reklama")],
            [KeyboardButton(text="📹 Videoli reklama"), KeyboardButton(text="📄 Dokument reklama")],
            [KeyboardButton(text="👥 Kimlarga yuborish?"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        "📤 <b>REKLAMA YUBORISH PANELI</b>\n\n"
        "Quyidagi formatlardan birini tanlang:\n"
        "• 📝 <b>Matn</b> - oddiy matnli reklama\n"
        "• 🖼️ <b>Rasm</b> - rasm + matnli reklama\n"
        "• 📹 <b>Video</b> - video + matnli reklama\n"
        "• 📄 <b>Dokument</b> - fayl + matnli reklama\n\n"
        "👥 <b>Kimlarga yuborish?</b> - qabul qiluvchilarni tanlash",
        reply_markup=broadcast_keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.sending_message)

async def process_broadcast_recipients(message: Message, state: FSMContext):
    """Qabul qiluvchilarni tanlash"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "👥 Kimlarga yuborish?":
        recipients_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="👥 Barcha foydalanuvchilar"), KeyboardButton(text="✅ Faol foydalanuvchilar")],
                [KeyboardButton(text="🆕 Yangi foydalanuvchilar"), KeyboardButton(text="🎯 Kategoriya bo'yicha")],
                [KeyboardButton(text="🔙 Reklama menyusi")]
            ],
            resize_keyboard=True
        )
        
        active_users = db.get_active_users()
        all_users = db.get_all_users()
        new_users = all_users[-50:] if len(all_users) > 50 else all_users
        
        stats_message = (
            "👥 <b>QABUL QILUVCHI STATISTIKASI:</b>\n\n"
            f"✅ Faol foydalanuvchilar: {len(active_users)}\n"
            f"👥 Jami foydalanuvchilar: {len(all_users)}\n"
            f"🆕 So'nggi 50 foydalanuvchi: {len(new_users)}\n\n"
            "<i>Kimlarga reklama yubormoqchisiz?</i>"
        )
        
        await message.answer(stats_message, reply_markup=recipients_keyboard, parse_mode="HTML")
        
        # ✅ HOLATNI SAQLASH
        await state.set_state(AdminStates.sending_message)
        
        # Saqlash uchun statistikani
        await state.update_data(
            active_users_count=len(active_users),
            all_users_count=len(all_users),
            new_users_count=len(new_users)
        )
    
    elif message.text in ["👥 Barcha foydalanuvchilar", "✅ Faol foydalanuvchilar", "🆕 Yangi foydalanuvchilar"]:
        await state.update_data(broadcast_recipients=message.text)
        
        # Reklama turini tanlashga qaytish
        broadcast_keyboard = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="📝 Matnli reklama"), KeyboardButton(text="🖼️ Rasmli reklama")],
                [KeyboardButton(text="📹 Videoli reklama"), KeyboardButton(text="📄 Dokument reklama")],
                [KeyboardButton(text="🔙 Orqaga")]
            ],
            resize_keyboard=True
        )
        
        await message.answer(
            f"✅ <b>Tanlandi:</b> {message.text}\n\n"
            "Endi reklama formatini tanlang:",
            reply_markup=broadcast_keyboard,
            parse_mode="HTML"
        )
        
        # ✅ HOLATNI SAQLASH - muhim!
        await state.set_state(AdminStates.sending_message)
    
    elif message.text == "🔙 Reklama menyusi":
        await start_broadcast(message, state)
    
    elif message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()

# Xabarning turini tanlash
async def process_broadcast_type(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "📝 Matnli reklama":
        await message.answer(
            "✍️ <b>Matnli reklama yuborish:</b>\n\n"
            "Iltimos, reklama matnini kiriting (HTML formatida bo'lishi mumkin):\n\n"
            "<i>Namuna:</i>\n"
            "<code>🎉 Yangi chegirma!\n\n"
            "🏠 Tamirlash xizmatlari uchun 20% chegirma!\n"
            "📞 +998 88 044-55-50</code>",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_text)
        
    elif message.text == "🖼️ Rasmli reklama":
        await message.answer(
            "🖼️ <b>Rasmli reklama yuborish:</b>\n\n"
            "Iltimos, rasmni yuboring (rasm caption'ida reklama matni bo'lishi mumkin):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_photo)
        
    elif message.text == "📹 Videoli reklama":
        await message.answer(
            "📹 <b>Videoli reklama yuborish:</b>\n\n"
            "Iltimos, videoni yuboring (video caption'ida reklama matni bo'lishi mumkin):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_video)
        
    elif message.text == "📄 Dokument reklama":
        await message.answer(
            "📄 <b>Dokument reklama yuborish:</b>\n\n"
            "Iltimos, dokumentni yuboring (dokument caption'ida reklama matni bo'lishi mumkin):",
            reply_markup=get_back_keyboard()
        )
        await state.set_state(AdminStates.waiting_broadcast_document)
        
    elif message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()

# Matnli reklama
async def process_broadcast_text(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await start_broadcast(message, state)
        return
    
    # Reklama matnini saqlash
    await state.update_data(broadcast_text=message.text)
    
    # Tasdiqlash
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast:text"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])
    
    await message.answer(
        f"📤 <b>Reklama tayyor:</b>\n\n"
        f"{message.text}\n\n"
        f"✅ <b>Barcha foydalanuvchilarga yuborilsinmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# Rasmli reklama
async def process_broadcast_photo(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text and message.text == "🔙 Orqaga":
        await start_broadcast(message, state)
        return
    
    if not message.photo:
        await message.answer("❌ Iltimos, rasm yuboring!", reply_markup=get_back_keyboard())
        return
    
    # Rasm va caption'ni saqlash
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    await state.update_data(
        broadcast_type="photo",
        broadcast_file_id=photo_id,
        broadcast_caption=caption
    )
    
    # Tasdiqlash
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast:photo"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])
    
    preview_text = f"📸 <b>Rasmli reklama tayyor:</b>\n\n{caption}" if caption else "📸 <b>Rasmli reklama tayyor</b>"
    
    await message.answer_photo(
        photo=photo_id,
        caption=f"{preview_text}\n\n✅ <b>Barcha foydalanuvchilarga yuborilsinmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def process_broadcast_video(message: Message, state: FSMContext):
    """Video reklama qabul qilish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text and message.text == "🔙 Orqaga":
        await start_broadcast(message, state)
        return
    
    if not message.video:
        await message.answer("❌ Iltimos, video yuboring!", reply_markup=get_back_keyboard())
        return
    
    # Video va caption'ni saqlash
    video_id = message.video.file_id
    caption = message.caption or ""
    
    await state.update_data(
        broadcast_type="video",
        broadcast_file_id=video_id,
        broadcast_caption=caption
    )
    
    # Tasdiqlash
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast:video"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])
    
    preview_text = f"🎬 <b>Videoli reklama tayyor:</b>\n\n{caption}" if caption else "🎬 <b>Videoli reklama tayyor</b>"
    
    await message.answer_video(
        video=video_id,
        caption=f"{preview_text}\n\n✅ <b>Barcha foydalanuvchilarga yuborilsinmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

async def process_broadcast_document(message: Message, state: FSMContext):
    """Dokument reklama qabul qilish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text and message.text == "🔙 Orqaga":
        await start_broadcast(message, state)
        return
    
    if not message.document:
        await message.answer("❌ Iltimos, dokument yuboring!", reply_markup=get_back_keyboard())
        return
    
    # Dokument va caption'ni saqlash
    doc_id = message.document.file_id
    caption = message.caption or ""
    
    await state.update_data(
        broadcast_type="document",
        broadcast_file_id=doc_id,
        broadcast_caption=caption
    )
    
    # Tasdiqlash
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, yuborish", callback_data="confirm_broadcast:document"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])
    
    preview_text = f"📄 <b>Dokument reklama tayyor:</b>\n\n{caption}" if caption else "📄 <b>Dokument reklama tayyor</b>"
    
    await message.answer_document(
        document=doc_id,
        caption=f"{preview_text}\n\n✅ <b>Barcha foydalanuvchilarga yuborilsinmi?</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

# ==================== BLOKLASH ====================

# Bloklashni boshlash
async def start_blocking_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminStates.blocking_user)
    
    await message.answer(
        "🚫 Bloklash uchun foydalanuvchi ID sini yuboring:",
        reply_markup=get_back_keyboard()
    )

async def process_block_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await message.answer(f"❌ ID {user_id} bilan foydalanuvchi topilmadi!")
            return
        
        # Foydalanuvchini bloklash
        db.block_user(user_id)
        
        # ✅ YANGI: Bloklanganligi haqida foydalanuvchiga OGOHLANTIRISH XABARI yuborish
        try:
            lang = user_data[3]
            
            # Til bo'yicha xabar matnlari
            block_messages = {
                "uz": """🚫 <b>OGOHLANTIRISH!</b>

❌ <b>Sizning hisobingiz bloklandi!</b>

Botdan foydalana olmaysiz.

⚖️ <b>Bloklash sabablari:</b>
• Bot qoidalarini buzganingiz uchun
• Kontentlarni yuklab olganingiz yoki ko'chirganingiz uchun
• Noto'g'ri xatti-harakatlar uchun

📞 <b>Shikoyat yoki izoh uchun:</b>
+998 88 044-55-50

⚠️ <b>Eslatma:</b>
Agar sizda savollar bo'lsa yoki xatolik deb o'ylasangiz, yuqoridagi raqamga qo'ng'iroq qiling.

⏰ <b>Bloklash muddati:</b>
Cheklanmagan (admin tomonidan olib tashlanmaguncha)

📝 <b>Qayta ochilish uchun:</b>
• Admin bilan bog'laning
• Sababni tushuntiring
• Kafolat bering

<code>© Usta Muhiddin. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🚫 <b>ПРЕДУПРЕЖДЕНИЕ!</b>

❌ <b>Ваш аккаунт заблокирован!</b>

Вы не можете использовать бота.

⚖️ <b>Причины блокировки:</b>
• За нарушение правил бота
• За скачивание или копирование контента
• За неподобающее поведение

📞 <b>Для жалоб или комментариев:</b>
+998 88 044-55-50

⚠️ <b>Примечание:</b>
Если у вас есть вопросы или вы считаете это ошибкой, позвоните по указанному номеру.

⏰ <b>Срок блокировки:</b>
Неограниченный (пока не снят администратором)

📝 <b>Для разблокировки:</b>
• Свяжитесь с администратором
• Объясните причину
• Дайте гарантии

<code>© Usta Muhiddin. Все права защищены.</code>"""
            }
            
            # Foydalanuvchiga xabar yuborish
            await bot_instance.send_message(
                user_id, 
                block_messages[lang], 
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to send block message: {e}")
        
        # ✅ TO'G'RI: Admin uchun muvaffaqiyatli xabar
        success_message = (
            "✅ <b>Foydalanuvchi muvaffaqiyatli bloklandi!</b>\n\n"
            "👤 <b>Ism:</b> {}\n"
            "🆔 <b>ID:</b> {}\n"
            "📞 <b>Telefon:</b> {}\n"
            "🌐 <b>Til:</b> {}\n\n"
            "📨 <b>Foydalanuvchiga ogohlantirish xabari yuborildi!</b>"
        ).format(
            user_data[1],
            user_id,
            user_data[2],
            "🇺🇿 O'zbek" if user_data[3] == 'uz' else "🇷🇺 Русский"
        )
        
        await message.answer(success_message, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri ID kiriting (faqat raqam)!")
        return
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    await state.clear()
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# ==================== BLOKDAN OCHISH ====================

# Blokdan ochishni boshlash
async def start_unblocking_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminStates.unblocking_user)
    
    blocked_users = db.get_blocked_users()
    
    if not blocked_users:
        await message.answer("🚫 Hozirda hech qanday bloklangan foydalanuvchi yo'q.")
        return
    
    text = "🔒 Bloklangan foydalanuvchilar:\n\n"
    for user in blocked_users:
        text += f"👤 ID: {user[0]} | Ism: {user[1]} | Tel: {user[2]}\n"
    
    text += "\n✅ Blokdan ochish uchun foydalanuvchi ID sini yuboring:"
    
    await message.answer(text, reply_markup=get_back_keyboard())

async def process_unblock_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        user_data = db.get_user(user_id)
        
        if not user_data:
            await message.answer(f"❌ ID {user_id} bilan foydalanuvchi topilmadi!")
            return
        
        # Foydalanuvchini blokdan ochish
        db.unblock_user(user_id)
        
        # ✅ Blokdan ochilganligi haqida foydalanuvchiga CHIROYLI XABAR yuborish
        try:
            lang = user_data[3]
            
            # Til bo'yicha xabar matnlari
            unblock_messages = {
                "uz": """🎉 <b>Tabriklaymiz!</b>

✅ <b>Sizning hisobingiz blokdan olindi!</b>

Siz endi Usta Muhiddin botidan to'liq foydalana olasiz.

⚠️ <b>OGOHLANTIRISH:</b>
• Bot qoidalariga qat'iy rioya qiling
• Kontentlarni yuklab olish yoki ko'chirish taqiqlanadi
• Qonuniy huquqlarni buzish javobgarlikni keltirib chiqaradi

📞 <b>Yordam uchun:</b>
+998 88 044-55-50

🏠 <b>Xizmatlar:</b>
• Klassik tamirlash
• Lepka yopishtirish
• Gipsi carton fason
• HiTech tamirlash
• To'liq tamirlash

🎨 <b>Bizning maqsadimiz:</b>
Uyingizni chiroyli va zamonaviy qilish!

📍 <b>Manzil:</b> Toshkent

⏰ <b>Ish vaqtlari:</b>
Dushanba-Yakshanba: 9:00 - 18:00

💖 <b>Xursand mijoz - bizning maqsadimiz!</b>

<code>© Usta Muhiddin. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🎉 <b>Поздравляем!</b>

✅ <b>Ваш аккаунт разблокирован!</b>

Теперь вы можете полноценно пользоваться ботом Мастера Элбека.

⚠️ <b>ПРЕДУПРЕЖДЕНИЕ:</b>
• Строго соблюдайте правила бота
• Запрещено скачивать или копировать контент
• Нарушение законных прав влечет ответственность

📞 <b>Для помощи:</b>
+998 88 044-55-50

🏠 <b>Услуги:</b>
• Классический ремонт
• Поклейка обоев
• Гипсокартон фасон
• HiTech ремонт
• Полный ремонт

🎨 <b>Наша цель:</b>
Сделать ваш дом красивым и современным!

📍 <b>Адрес:</b> Ташкент

⏰ <b>Время работы:</b>
Понедельник-Воскресенье: 9:00 - 18:00

💖 <b>Довольный клиент - наша цель!</b>

<code>© Usta Muhiddin. Все права защищены.</code>"""
            }
            
            # Foydalanuvchiga xabar yuborish
            await bot_instance.send_message(
                user_id, 
                unblock_messages[lang], 
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to send unblock message: {e}")
        
        # Admin uchun muvaffaqiyatli xabar
        success_message = (
            "✅ <b>Foydalanuvchi muvaffaqiyatli blokdan olindi!</b>\n\n"
            "👤 <b>Ism:</b> {}\n"
            "🆔 <b>ID:</b> {}\n"
            "📞 <b>Telefon:</b> {}\n"
            "🌐 <b>Til:</b> {}\n\n"
            "📨 <b>Foydalanuvchiga xabar yuborildi!</b>"
        ).format(
            user_data[1],
            user_id,
            user_data[2],
            "🇺🇿 O'zbek" if user_data[3] == 'uz' else "🇷🇺 Русский"
        )
        
        await message.answer(success_message, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri ID kiriting (faqat raqam)!")
        return
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    await state.clear()
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# ==================== KONTENTLAR RO'YXATI ====================

# Kontentlar ro'yxati
async def show_contents_list(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    contents = db.get_all_contents()
    
    if not contents:
        await message.answer("📭 Hech qanday kontent topilmadi.")
        return
    
    # Kategoriya nomlari
    category_names = {
        "classic": "🛠️ Klassik Tamirlash",
        "glue": "🎨 Lepka Yopishtirish",
        "gypsum": "🏠 Gipsi Carton Fason",
        "hitech": "💻 HiTech Tamirlash",
        "full": "🔨 To'liq Tamirlash",
        "video": "📹 Video Joylash"
    }
    
    # Tur nomlari
    type_names = {
        "photo": "🖼️ Rasm",
        "video": "📹 Video",
        "document": "📄 Dokument"
    }
    
    text = "📋 Barcha kontentlar:\n\n"
    
    for content in contents[:20]:
        category = category_names.get(content[1], content[1])
        content_type = type_names.get(content[2], content[2])
        date = content[5].split()[0] if isinstance(content[5], str) else str(content[5])[:10]
        
        text += f"🆔 ID: {content[0]}\n"
        text += f"📁 {category}\n"
        text += f"📄 {content_type}\n"
        text += f"📅 {date}\n"
        if content[4]:
            caption_preview = content[4][:30] + "..." if len(content[4]) > 30 else content[4]
            text += f"📝 {caption_preview}\n"
        text += "------------------------------\n"
    
    if len(contents) > 20:
        text += f"\n📊 Jami: {len(contents)} ta kontent (faqat 20 tasi ko'rsatilgan)"
    
    await message.answer(text)

# ==================== KONTENT O'CHIRISH ====================

# Kontent o'chirishni boshlash
async def start_deleting_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    keyboard, text = get_content_categories_keyboard("delete")
    await message.answer(text, reply_markup=keyboard)
    await state.set_state(AdminStates.deleting_content)

# Kategoriya bo'yicha o'chirish
async def process_delete_category(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    # Kategoriya mapping
    categories_map = {
        "🛠️ Klassik Tamirlash": "classic",
        "🎨 Lepka Yopishtirish": "glue", 
        "🏠 Gipsi Carton Fason": "gypsum",
        "💻 HiTech Tamirlash": "hitech",
        "🔨 To'liq Tamirlash": "full",
        "📹 Video Joylash": "video"
    }
    
    if message.text not in categories_map:
        if message.text == "🔙 Orqaga":
            await state.clear()
            await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
            return
        await message.answer("❌ Iltimos, ro'yxatdagi kategoriyalardan birini tanlang!")
        return
    
    category = categories_map[message.text]
    contents = db.get_contents_by_category(category)
    
    if not contents:
        await message.answer(f"❌ '{message.text}' kategoriyasida hech qanday kontent topilmadi.")
        await state.clear()
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        return
    
    # Kontentlarni INLINE KLAVIATURA bilan ko'rsatish
    text = f"🗑️ <b>'{message.text}' kategoriyasidagi kontentlar:</b>\n\n"
    
    for content in contents:
        content_id = content[0]
        content_type = "🖼️" if content[2] == 'photo' else "📹" if content[2] == 'video' else "📄"
        date = content[5].split()[0] if isinstance(content[5], str) else str(content[5])[:10]
        
        text += f"<b>🆔 {content_id}</b> | {content_type} | 📅 {date}\n"
        
        if content[4]:
            caption_preview = content[4][:30] + "..." if len(content[4]) > 30 else content[4]
            text += f"📝 {caption_preview}\n"
        
        text += "─" * 30 + "\n"
    
    # INLINE KLAVIATURA YARATISH
    keyboard = []
    
    # Har bir kontent uchun o'chirish tugmasi
    for content in contents:
        content_id = content[0]
        content_type = "🖼️" if content[2] == 'photo' else "📹" if content[2] == 'video' else "📄"
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ O'chirish #{content_id} ({content_type})",
                callback_data=f"delete_content:{content_id}"
            )
        ])
    
    # Barchasini bir vaqtda o'chirish tugmasi
    keyboard.append([
        InlineKeyboardButton(
            text="🗑️ BARCHASINI O'CHIRISH",
            callback_data=f"delete_all:{category}"
        )
    ])
    
    # Orqaga tugmasi
    keyboard.append([
        InlineKeyboardButton(
            text="🔙 Orqaga",
            callback_data="delete_back"
        )
    ])
    
    reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")
    await state.clear()

# ==================== ASOSIY MENYUGA QAYTISH ====================

# Asosiy menyuga qaytish
async def back_to_main_menu(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    from main import get_main_menu_keyboard
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_menu_keyboard('uz'))
    await state.clear()

# ==================== ASOSIY ADMIN HANDLER ====================

async def handle_admin_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    command = message.text
    current_state = await state.get_state()
    
    # ============ JOYLASHUVLAR BOSHQARUVI ============
    if command in [
        "📍 Joylashuvlarni Boshqarish",
        "📍 Eng so'nggi joylashuv",
        "📋 Barcha joylashuvlar", 
        "⏳ Kutilayotganlar",
        "✅ Tasdiqlanganlar",
        "❌ Rad etilganlar",
        "🗑️ Eski joylashuvlar",
        "🔄 Joylashuvlarni yangilash",
        "🔙 Admin Menyuga"
    ]:
        await handle_admin_locations(message, state)
        return
    
    # ============ YANGI ODAM QO'SHISH HOLATLARI ============
    if current_state == AdminStates.waiting_for_user_fullname:
        await process_user_fullname(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_user_phone:
        await process_user_phone(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_user_language:
        await process_user_language(message, state)
        return
    
    # ============ REKLAMA YUBORISH HOLATLARI ============
    elif current_state == AdminStates.sending_message.state:
        await process_broadcast_type(message, state)
        return
    
    elif current_state == AdminStates.waiting_broadcast_text.state:
        await process_broadcast_text(message, state)
        return
    
    elif current_state == AdminStates.waiting_broadcast_photo.state:
        await process_broadcast_photo(message, state)
        return
    
    elif current_state == AdminStates.waiting_broadcast_video.state:
        await process_broadcast_video(message, state)
        return
    
    elif current_state == AdminStates.waiting_broadcast_document.state:
        await process_broadcast_document(message, state)
        return
    
    # ============ KONTENT QO'SHISH HOLATLARI ============
    elif current_state == AdminStates.adding_content.state:
        await process_content_category(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_content.state:
        await process_content_type(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_caption.state:
        if message.content_type in ['photo', 'video', 'document']:
            await process_content_file(message, state)
        elif message.text and message.text == "🔙 Orqaga":
            await message.answer("📄 Kontent turini tanlang:", reply_markup=get_content_type_keyboard())
            await state.set_state(AdminStates.waiting_for_content)
        return
    
    # ============ BLOKLASH HOLATLARI ============
    elif current_state == AdminStates.blocking_user.state:
        await process_block_user(message, state)
        return
    
    elif current_state == AdminStates.unblocking_user.state:
        await process_unblock_user(message, state)
        return
    
    # ============ KONTENT O'CHIRISH HOLATLARI ============
    elif current_state == AdminStates.deleting_content.state:
        await process_delete_category(message, state)
        return
    
    # ============ ASOSIY BUYRUQLAR ============
    # 👥 ODAM QO'SHISH
    if command == "👥 Odam Qo'shish":
        await start_adding_user(message, state)
        return
    
    # 📨 XABAR YUBORISH va REKLAMA
    elif command == "📨 Xabar Yuborish":
        await start_broadcast(message, state)
        return
    
    elif command == "👥 Kimlarga yuborish?" or command in [
        "👥 Barcha foydalanuvchilar", 
        "✅ Faol foydalanuvchilar", 
        "🆕 Yangi foydalanuvchilar",
        "🔙 Reklama menyusi"
    ]:
        await process_broadcast_recipients(message, state)
        return
    
    # REKLAMA FORMATLARI
    elif command in ["📝 Matnli reklama", "🖼️ Rasmli reklama", 
                    "📹 Videoli reklama", "📄 Dokument reklama"]:
        
        # Agar sending_message holatida bo'lsa
        if current_state == AdminStates.sending_message.state:
            await process_broadcast_type(message, state)
        else:
            await message.answer("❌ Iltimos, avval '📨 Xabar Yuborish' tugmasini bosing!")
        return
    
    # 📊 FOYDALANUVCHILAR MA'LUMOTLARI
    elif command == "📊 Foydalanuvchilar Ma'lumotlari":
        await show_users_info(message)
    
    # ➕ KONTENT QO'SHISH
    elif command == "➕ Kontent Qo'shish":
        await start_adding_content(message, state)
    
    # 🗑️ KONTENT O'CHIRISH
    elif command == "🗑️ Kontent O'chirish":
        await start_deleting_content(message, state)
    
    # 🚫 BLOKLASH
    elif command == "🚫 Bloklash":
        await start_blocking_user(message, state)
    
    # ✅ BLOKDAN OCHISH
    elif command == "✅ Blokdan Ochish":
        await start_unblocking_user(message, state)
    
    # 📋 KONTENTLAR RO'YXATI
    elif command == "📋 Kontentlar Ro'yxati":
        await show_contents_list(message)
    
    # 📍 JOYLASHUVLARNI BOSHQARISH (ESKISI)
    elif command == "📍 Joylashuvni Ko'rish":
        await show_latest_locations(message)
    
    # 🔙 ASOSIY MENYUGA QAYTISH
    elif command == "🔙 Asosiy Menyuga Qaytish":
        await back_to_main_menu(message, state)
    
    # KATEGORIYA TUGMALARI
    elif command in ["🛠️ Klassik Tamirlash", "🎨 Lepka Yopishtirish", 
                    "🏠 Gipsi Carton Fason", "💻 HiTech Tamirlash",
                    "🔨 To'liq Tamirlash", "📹 Video Joylash"]:
        
        # Agar FSM holati bo'lsa
        if current_state == AdminStates.adding_content.state:
            await process_content_category(message, state)
        elif current_state == AdminStates.deleting_content.state:
            await process_delete_category(message, state)
        else:
            await message.answer("Iltimos, avval '➕ Kontent Qo'shish' yoki '🗑️ Kontent O'chirish' tugmasini bosing!")
    
    # BOSHQALAR
    elif command in ["🖼️ Rasm", "📹 Video", "📄 Dokument", "🔙 Orqaga"]:
        
        if current_state == AdminStates.waiting_for_content.state:
            await process_content_type(message, state)
        elif command == "🔙 Orqaga":
            await state.clear()
            await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    
    # Agar hech qaysi shart bajarilmasa
    else:
        await message.answer("❌ Noma'lum buyruq!", reply_markup=get_admin_keyboard())

# ==================== JOYLASHUVLAR BOSHQARUVI HANDLER ====================

async def handle_admin_locations(message: Message, state: FSMContext):
    """Admin joylashuvlar boshqaruvi"""
    if message.from_user.id != ADMIN_ID:
        return
    
    command = message.text
    
    if command == "📍 Joylashuvlarni Boshqarish":
        await message.answer("📍 Joylashuvlar Boshqaruvi", reply_markup=get_locations_management_keyboard())
    
    elif command == "📍 Eng so'nggi joylashuv":
        await show_latest_locations(message)
    
    elif command == "📋 Barcha joylashuvlar":
        await show_all_locations_admin(message)
    
    elif command == "⏳ Kutilayotganlar":
        await show_pending_locations(message)
    
    elif command == "✅ Tasdiqlanganlar":
        await show_accepted_locations(message)
    
    elif command == "❌ Rad etilganlar":
        await show_rejected_locations(message)
    
    elif command == "🗑️ Eski joylashuvlar":
        await delete_old_locations(message)
    
    elif command == "🔄 Joylashuvlarni yangilash":
        await show_latest_locations(message)
        await message.answer("🔄 Joylashuvlar yangilandi!")
    
    elif command == "🔙 Admin Menyuga":
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# ==================== CALLBACK HANDLERS (admin.py uchun) ====================

async def handle_view_location_callback(callback: CallbackQuery):
    """Joylashuvni ko'rish callback"""
    try:
        location_id = int(callback.data.split(":")[1])
        location_data = db.get_location_by_id(location_id)
        
        if not location_data:
            await callback.answer("❌ Joylashuv topilmadi!")
            return
        
        # Joylashuv ma'lumotlari
        location_info = (
            f"📍 <b>JOYLASHUV #{location_id}</b>\n\n"
            f"👤 <b>Ism:</b> {location_data[2]}\n"
            f"📞 <b>Telefon:</b> {location_data[3]}\n"
            f"📍 <b>Koordinatalar:</b>\n"
            f"   • Kenglik: {location_data[4]}\n"
            f"   • Uzunlik: {location_data[5]}\n"
            f"📊 <b>Holat:</b> {location_data[6]}\n"
            f"⏰ <b>Yuborilgan:</b> {location_data[7]}"
        )
        
        # Joylashuvni yuborish
        await callback.message.answer_location(
            latitude=location_data[4],
            longitude=location_data[5],
            caption=f"📍 Joylashuv #{location_id}\n👤 {location_data[2]}\n📞 {location_data[3]}"
        )
        
        # Tasdiqlash/Rad etish tugmalari
        keyboard_buttons = []
        
        if location_data[6] == 'pending':
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text="✅ Tasdiqlash",
                    callback_data=f"accept_location:{location_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Rad etish",
                    callback_data=f"reject_location:{location_id}"
                )
            ])
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text="📞 Telefon qilish",
                url=f"tel:{location_data[3].replace('+', '').replace(' ', '')}"
            ),
            InlineKeyboardButton(
                text="📍 Barcha joylashuvlar",
                callback_data="view_all_locations_admin"
            )
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.answer(location_info, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"View location error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

async def handle_accept_location_callback(callback: CallbackQuery):
    """Joylashuvni tasdiqlash callback"""
    try:
        location_id = int(callback.data.split(":")[1])
        location_data = db.get_location_by_id(location_id)
        
        if not location_data:
            await callback.answer("❌ Joylashuv topilmadi!")
            return
        
        # Statusni yangilash
        db.update_location_status(location_id, "accepted")
        
        # Foydalanuvchiga xabar yuborish
        user_id = location_data[1]
        user_data = db.get_user(user_id)
        
        if user_data:
            lang = user_data[3]
            
            user_message = {
                "uz": "✅ <b>Joylashuvingiz tasdiqlandi!</b>\n\n"
                      "Usta Muhiddin tez orada siz bilan bog'lanadi.\n"
                      "📞 Telefon: +998 88 044-55-50\n\n"
                      "📍 <i>Joylashuvingiz:</i>\n"
                      f"• Kenglik: {location_data[4]}\n"
                      f"• Uzunlik: {location_data[5]}",
                "ru": "✅ <b>Ваше местоположение подтверждено!</b>\n\n"
                      "Мастер Мухиддин скоро свяжется с вами.\n"
                      "📞 Телефон: +998 88 044-55-50\n\n"
                      "📍 <i>Ваше местоположение:</i>\n"
                      f"• Широта: {location_data[4]}\n"
                      f"• Долгота: {location_data[5]}"
            }
            
            try:
                if bot_instance:
                    await bot_instance.send_message(user_id, user_message[lang], parse_mode="HTML")
                else:
                    from main import bot
                    await bot.send_message(user_id, user_message[lang], parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")
        
        # Admin uchun xabar
        await callback.answer(f"✅ Joylashuv #{location_id} tasdiqlandi!", show_alert=True)
        
        # Xabarni yangilash
        await callback.message.delete()
        await show_latest_locations(callback.message)
        
    except Exception as e:
        logger.error(f"Accept location error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

async def handle_reject_location_callback(callback: CallbackQuery):
    """Joylashuvni rad etish callback"""
    try:
        location_id = int(callback.data.split(":")[1])
        location_data = db.get_location_by_id(location_id)
        
        if not location_data:
            await callback.answer("❌ Joylashuv topilmadi!")
            return
        
        # Statusni yangilash
        db.update_location_status(location_id, "rejected")
        
        # Foydalanuvchiga xabar yuborish
        user_id = location_data[1]
        user_data = db.get_user(user_id)
        
        if user_data:
            lang = user_data[3]
            
            user_message = {
                "uz": "❌ <b>Joylashuvingiz rad etildi.</b>\n\n"
                      "Iltimos, boshqa joylashuv yuboring yoki telefon orqali bog'laning.\n"
                      "📞 +998 88 044-55-50",
                "ru": "❌ <b>Ваше местоположение отклонено.</b>\n\n"
                      "Пожалуйста, отправьте другое местоположение или свяжитесь по телефону.\n"
                      "📞 +998 88 044-55-50"
            }
            
            try:
                if bot_instance:
                    await bot_instance.send_message(user_id, user_message[lang], parse_mode="HTML")
                else:
                    from main import bot
                    await bot.send_message(user_id, user_message[lang], parse_mode="HTML")
            except Exception as e:
                logger.error(f"Failed to notify user: {e}")
        
        # Admin uchun xabar
        await callback.answer(f"❌ Joylashuv #{location_id} rad etildi!", show_alert=True)
        
        # Xabarni yangilash
        await callback.message.delete()
        await show_latest_locations(callback.message)
        
    except Exception as e:
        logger.error(f"Reject location error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

# ==================== CALLBACK HANDLERLAR (main.py ga o'tkazish uchun) ====================

# Bu funksiyalar main.py da ishlatiladi
async def handle_admin_callback(callback: CallbackQuery, state: FSMContext):
    """Admin callback'larini boshqarish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    data = callback.data
    
    try:
        if data.startswith("view_location:"):
            await handle_view_location_callback(callback)
        
        elif data.startswith("accept_location:"):
            await handle_accept_location_callback(callback)
        
        elif data.startswith("reject_location:"):
            await handle_reject_location_callback(callback)
        
        elif data == "refresh_locations_admin":
            from admin import show_latest_locations
            await callback.message.delete()
            await show_latest_locations(callback.message)
            await callback.answer("🔄 Yangilandi!")
        
        elif data == "view_all_locations_admin":
            from admin import show_all_locations_admin
            await callback.message.delete()
            await show_all_locations_admin(callback.message)
            await callback.answer()
        
        elif data == "view_latest_location":
            from admin import show_latest_locations
            await callback.message.delete()
            await show_latest_locations(callback.message)
            await callback.answer()
        
        elif data == "locations_management_back":
            from admin import get_locations_management_keyboard
            await callback.message.delete()
            await callback.message.answer("📍 Joylashuvlar Boshqaruvi", reply_markup=get_locations_management_keyboard())
            await callback.answer()
        
        elif data.startswith("copy_link:"):
            # Havolani nusxalash
            link = data.split(":")[1]
            await callback.answer(f"✅ Havola nusxalandi!\n{link[:50]}...", show_alert=True)
        
        else:
            await callback.answer("❌ Noma'lum buyruq!")
    
    except Exception as e:
        logger.error(f"Callback error: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)