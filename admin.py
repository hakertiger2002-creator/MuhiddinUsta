# admin.py - TO'LIQ YANGILASH

from aiogram import Bot, F
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton, 
    Message, CallbackQuery,
    PhotoSize, Video, Document,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.enums import ParseMode

from database import db
import asyncio
import logging
from datetime import datetime

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
    
    # Xabar yuborish (mavjud)
    sending_message = State()
    waiting_broadcast_text = State()
    waiting_broadcast_photo = State()
    waiting_broadcast_video = State()
    waiting_broadcast_document = State()

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

# Admin panel klaviaturasini yangilang:
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📊 Foydalanuvchilar Ma'lumotlari"), KeyboardButton(text="📨 Xabar Yuborish")],
            [KeyboardButton(text="➕ Kontent Qo'shish"), KeyboardButton(text="🗑️ Kontent O'chirish")],
            [KeyboardButton(text="👥 Odam Qo'shish"), KeyboardButton(text="📋 Kontentlar Ro'yxati")],
            [KeyboardButton(text="🚫 Bloklash"), KeyboardButton(text="✅ Blokdan Ochish")],
            [KeyboardButton(text="📍 Joylashuvni Ko'rish"), KeyboardButton(text="🔙 Asosiy Menyuga Qaytish")]
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
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🖼️ Rasm"), KeyboardButton(text="📹 Video")],
            [KeyboardButton(text="📄 Dokument"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def get_back_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

def get_protection_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔒 Yuqori Himoya"), KeyboardButton(text="🛡️ O'rta Himoya")],
            [KeyboardButton(text="⚠️ Past Himoya"), KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )
    
def get_users_management_keyboard():
    """Foydalanuvchilarni boshqarish klaviaturasi"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Odam Qo'shish"), KeyboardButton(text="📊 Foydalanuvchilar Ma'lumotlari")],
            [KeyboardButton(text="📨 Xabar Yuborish"), KeyboardButton(text="🚫 Bloklash")],
            [KeyboardButton(text="✅ Blokdan Ochish"), KeyboardButton(text="🔙 Admin Menyuga")]
        ],
        resize_keyboard=True,
        persistent=True
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

async def set_protection_level(message: Message, state: FSMContext):
    """Himoya darajasini sozlash"""
    if message.from_user.id != ADMIN_ID:
        return
    
    protection_map = {
        "🔒 Yuqori Himoya": 3,
        "🛡️ O'rta Himoya": 2,
        "⚠️ Past Himoya": 1
    }
    
    if message.text in protection_map:
        level = protection_map[message.text]
        await state.update_data(protection_level=level)
        await message.answer(f"✅ Himoya darajasi {level} ga o'rnatildi")    

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

# ============ ODAM QO'SHISH FUNKSIYALARI ============

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
        # Telefon raqamini tozalash
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
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        # Telefon raqamidan Telegram profiliga havola
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
        
        # ✅ INLINE TUGMA UCHUN CALLBACK HANDLER (main.py ga qo'shing)
        # @dp.callback_query(F.data.startswith("copy_link:"))
        # async def handle_copy_link(callback: CallbackQuery):
        #     link = callback.data.split(":")[1]
        #     await callback.answer(f"Havola nusxalandi: {link[:30]}...")
        
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    # Admin panelga qaytish
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await state.clear()

# ✅ YANGI: User ID ni qabul qilish funksiyasi
async def process_user_id_input(message: Message, state: FSMContext):
    """Foydalanuvchi ID sini qabul qilish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    if message.text == "🔙 Orqaga":
        await message.answer(
            "🌐 <b>Tilni tanlang:</b>",
            parse_mode="HTML",
            reply_markup=get_user_language_keyboard()
        )
        await state.set_state(AdminStates.waiting_for_user_language)
        return
    
    # ID ni tekshirish
    try:
        if message.text == "0":
            # Avtomatik ID yaratish
            import random
            user_id = random.randint(1000000000, 9999999999)
            await message.answer(
                f"🆔 <b>Avtomatik ID yaratildi:</b> {user_id}",
                parse_mode="HTML"
            )
        else:
            user_id = int(message.text)
            if user_id <= 0:
                await message.answer(
                    "❌ <b>Noto'g'ri ID!</b> Iltimos, musbat son kiriting.",
                    parse_mode="HTML",
                    reply_markup=get_back_keyboard()
                )
                return
        
        # Oldin saqlangan ma'lumotlarni olish
        data = await state.get_data()
        full_name = data.get('temp_full_name')
        phone_number = data.get('temp_phone')
        language = data.get('temp_language')
        lang_text = data.get('temp_lang_text')
        
        # Bazaga qo'shish
        try:
            db.add_user(user_id, full_name, phone_number, language)
            
            # Bot username'ini olish
            try:
                from main import BOT_USERNAME
                bot_username = BOT_USERNAME if BOT_USERNAME else "UstaElbekBot"
            except:
                bot_username = "UstaElbekBot"
            
            # Deep link yaratish
            deep_link = f"https://t.me/{bot_username}?start={user_id}"
            
            # Admin uchun asosiy xabar
            success_message = (
                f"✅ <b>YANGI FOYDALANUVCHI QO'SHILDI!</b>\n\n"
                f"👤 <b>Ism:</b> {full_name}\n"
                f"🆔 <b>ID:</b> {user_id}\n"
                f"📞 <b>Telefon:</b> {phone_number}\n"
                f"🌐 <b>Til:</b> {lang_text}\n\n"
                f"📊 <b>Jami foydalanuvchilar:</b> {len(db.get_all_users())}\n\n"
                f"🔗 <b>Bot havolasi:</b>\n"
                f"<code>{deep_link}</code>\n\n"
                f"📝 <b>Ko'rsatma:</b>\n"
                f"Foydalanuvchi havolani bosib botga kirgandan so'ng xush kelish xabarini oladi."
            )
            
            await message.answer(success_message, parse_mode="HTML")
            
            # ✅ Foydalanuvchiga xabar yuborishga urinish
            try:
                welcome_messages = {
                    "uz": f"""🎉 <b>Assalomu alaykum, {full_name}!</b>

✅ <b>Siz Usta Elbek botiga muvaffaqiyatli qo'shildingiz!</b>

🏠 <b>Bizning xizmatlarimiz:</b>
• Klassik tamirlash
• Lepka yopishtirish  
• Gipsi carton fason
• HiTech tamirlash
• To'liq tamirlash
• Video ishlar

📱 <b>Bot imkoniyatlari:</b>
• Barcha tamirlash usullarini ko'rish
• Usta Elbek bilan bog'lanish
• Joylashuv yuborish
• Videolarni tomosha qilish

📞 <b>Usta Elbek bilan bog'lanish:</b>
+998 95 902-32-32

📍 <b>Manzil:</b> Toshkent

⏰ <b>Ish vaqtlari:</b>
Dushanba-Yakshanba: 9:00 - 18:00

💖 <b>Biz sizning uyingizni chiroyli qilish uchun mavjudmiz!</b>

<code>© Usta Elbek. Barcha huquqlar himoyalangan.</code>""",
                    
                    "ru": f"""🎉 <b>Здравствуйте, {full_name}!</b>

✅ <b>Вы успешно добавлены в бот Usta Elbek!</b>

🏠 <b>Наши услуги:</b>
• Классический ремонт
• Поклейка обоев
• Гипсокартон фасон
• HiTech ремонт
• Полный ремонт
• Видео работы

📱 <b>Возможности бота:</b>
• Просмотр всех методов ремонта
• Связь с мастером Элбеком
• Отправка местоположения
• Просмотр видео

📞 <b>Связаться с мастером Элбеком:</b>
+998 95 902-32-32

📍 <b>Адрес:</b> Ташкент

⏰ <b>Время работы:</b>
Понедельник-Воскресенье: 9:00 - 18:00

💖 <b>Мы здесь, чтобы сделать ваш дом красивым!</b>

<code>© Usta Elbek. Все права защищены.</code>"""
                }
                
                # Global bot_instance dan foydalanish
                if 'bot_instance' in globals() and bot_instance:
                    await bot_instance.send_message(
                        user_id, 
                        welcome_messages[language], 
                        parse_mode="HTML"
                    )
                    
                    logger.info(f"✅ Welcome message sent to new user {user_id} ({full_name})")
                else:
                    logger.error("Bot instance is not set in admin.py")
                    await message.answer(
                        "⚠️ <b>Bot instansiyasi sozlanmagan.</b>",
                        parse_mode="HTML"
                    )
                
            except Exception as chat_error:
                logger.warning(f"⚠️ User {user_id} has not started chat with bot yet: {chat_error}")
                await message.answer(
                    f"⚠️ <b>Foydalanuvchi bot bilan suhbat boshlagan emas.</b>\n\n"
                    f"Ushbu havolani yuboring: {deep_link}",
                    parse_mode="HTML"
                )
            
        except Exception as e:
            await message.answer(f"❌ Bazaga saqlashda xatolik: {str(e)}")
        
    except ValueError:
        await message.answer(
            "❌ <b>Noto'g'ri format!</b> Iltimos, faqat raqam kiriting.",
            parse_mode="HTML",
            reply_markup=get_back_keyboard()
        )
        return
    
    # Admin panelga qaytish
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await state.clear()

# ============ XABAR YUBORISH FUNKSIYALARI ============

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
            "📞 +998 95 902-32-32</code>",
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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

# Bloklashni boshlash
async def start_blocking_user(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await state.set_state(AdminStates.blocking_user)
    
    await message.answer(
        "🚫 Bloklash uchun foydalanuvchi ID sini yuboring:",
        reply_markup=get_back_keyboard()
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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

# admin.py faylida process_block_user funksiyasini shunday tuzating:

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
+998 95 902-32-32

⚠️ <b>Eslatma:</b>
Agar sizda savollar bo'lsa yoki xatolik deb o'ylasangiz, yuqoridagi raqamga qo'ng'iroq qiling.

⏰ <b>Bloklash muddati:</b>
Cheklanmagan (admin tomonidan olib tashlanmaguncha)

📝 <b>Qayta ochilish uchun:</b>
• Admin bilan bog'laning
• Sababni tushuntiring
• Kafolat bering

<code>© Usta Elbek. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🚫 <b>ПРЕДУПРЕЖДЕНИЕ!</b>

❌ <b>Ваш аккаунт заблокирован!</b>

Вы не можете использовать бота.

⚖️ <b>Причины блокировки:</b>
• За нарушение правил бота
• За скачивание или копирование контента
• За неподобающее поведение

📞 <b>Для жалоб или комментариев:</b>
+998 95 902-32-32

⚠️ <b>Примечание:</b>
Если у вас есть вопросы или вы считаете это ошибкой, позвоните по указанному номеру.

⏰ <b>Срок блокировки:</b>
Неограниченный (пока не снят администратором)

📝 <b>Для разблокировки:</b>
• Свяжитесь с администратором
• Объясните причину
• Дайте гарантии

<code>© Usta Elbek. Все права защищены.</code>"""
            }
            
            # Foydalanuvchiga xabar yuborish
            await bot.send_message(
                user_id, 
                block_messages[lang], 
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to send block message: {e}")
        
        # ✅ TO'G'RI: Admin uchun muvaffaqiyatli xabar (format usuli)
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
            "🇺🇿 O'zbek" if user_data[3] == 'uz' else "🇷🇺 Русский"  # ✅ Format ichida apostrof muammosiz
        )
        
        await message.answer(success_message, parse_mode="HTML")
        
    except ValueError:
        await message.answer("❌ Iltimos, to'g'ri ID kiriting (faqat raqam)!")
        return
    except Exception as e:
        await message.answer(f"❌ Xatolik yuz berdi: {str(e)}")
    
    await state.clear()
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

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

Siz endi Usta Elbek botidan to'liq foydalana olasiz.

⚠️ <b>OGOHLANTIRISH:</b>
• Bot qoidalariga qat'iy rioya qiling
• Kontentlarni yuklab olish yoki ko'chirish taqiqlanadi
• Qonuniy huquqlarni buzish javobgarlikni keltirib chiqaradi

📞 <b>Yordam uchun:</b>
+998 95 902-32-32

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

<code>© Usta Elbek. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🎉 <b>Поздравляем!</b>

✅ <b>Ваш аккаунт разблокирован!</b>

Теперь вы можете полноценно пользоваться ботом Мастера Элбека.

⚠️ <b>ПРЕДУПРЕЖДЕНИЕ:</b>
• Строго соблюдайте правила бота
• Запрещено скачивать или копировать контент
• Нарушение законных прав влечет ответственность

📞 <b>Для помощи:</b>
+998 95 902-32-32

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

<code>© Usta Elbek. Все права защищены.</code>"""
            }
            
            # Foydalanuvchiga xabar yuborish
            await bot.send_message(
                user_id, 
                unblock_messages[lang], 
                parse_mode="HTML"
            )
            
        except Exception as e:
            logger.error(f"Failed to send unblock message: {e}")
        
        # Admin uchun muvaffaqiyatli xabar (format() usuli)
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
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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

# Joylashuvlarni ko'rsatish
async def show_latest_locations(message: Message):
    """Eng so'nggi joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations()
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
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
    location_id = latest_location[0]
    user_name = latest_location[2]
    phone = latest_location[3]
    status = latest_location[6]
    sent_time = latest_location[7].split()[1][:5] if isinstance(latest_location[7], str) else str(latest_location[7])[11:16]
    
    # Status ranglari
    status_emoji = "🟡" if status == 'pending' else "🟢" if status == 'accepted' else "🔴"
    
    text = f"""📍 <b>ENG SO'NGI JOYLASHUV:</b>

{status_emoji} <b>Holat:</b> {status}
🆔 <b>ID:</b> {location_id}
👤 <b>Foydalanuvchi:</b> {user_name}
📞 <b>Telefon:</b> {phone}
⏰ <b>Vaqt:</b> {sent_time}

✅ <i>Joylashuvni ko'rib, tasdiqlang yoki rad eting</i>"""
    
    # Inline klaviatura
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📍 Joylashuvni ko'rish",
                callback_data=f"view_location:{location_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="✅ Tasdiqlash",
                callback_data=f"accept_location:{location_id}"
            ),
            InlineKeyboardButton(
                text="❌ Rad etish",
                callback_data=f"reject_location:{location_id}"
            )
        ],
        [
            InlineKeyboardButton(
                text="📋 Barcha joylashuvlar",
                callback_data="view_all_locations_admin"
            ),
            InlineKeyboardButton(
                text="🔄 Yangilash",
                callback_data="refresh_locations_admin"
            )
        ]
    ])
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Barcha joylashuvlarni ko'rsatish
async def show_all_locations_admin(message: Message):
    """Barcha joylashuvlarni ko'rsatish"""
    if message.from_user.id != ADMIN_ID:
        return
    
    locations = db.get_latest_locations(limit=20)
    
    if not locations:
        await message.answer("📭 Hech qanday joylashuv yo'q.")
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    text = "📍 <b>BARCHA JOYLASHUVLAR:</b>\n\n"
    
    for i, loc in enumerate(locations, 1):
        location_id = loc[0]
        user_name = loc[2]
        phone = loc[3]
        status = loc[6]
        sent_time = loc[7].split()[1][:5] if isinstance(loc[7], str) else str(loc[7])[11:16]
        
        # Status ranglari
        status_icon = "🟡" if status == 'pending' else "🟢" if status == 'accepted' else "🔴"
        
        text += f"{i}. {status_icon} <b>#{location_id}</b> - {user_name}\n"
        text += f"   📞 {phone} | ⏰ {sent_time}\n"
        text += "   ─" * 15 + "\n"
    
    # Inline klaviatura
    keyboard_buttons = []
    
    for loc in locations[:5]:
        location_id = loc[0]
        user_name = loc[2]
        
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"📍 #{location_id} ({user_name})",
                callback_data=f"view_location:{location_id}"
            )
        ])
    
    keyboard_buttons.append([
        InlineKeyboardButton(
            text="🔄 Yangilash",
            callback_data="refresh_locations_admin"
        ),
        InlineKeyboardButton(
            text="📤 Eng so'nggisi",
            callback_data="view_latest_location"
        )
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await message.answer(text, reply_markup=keyboard, parse_mode="HTML")

# Joylashuv qabul qilish rejimi
async def location_receive_mode(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    await message.answer(
        "📍 Joylashuv qabul qilish rejimi yoqildi.\n\n"
        "Endi foydalanuvchilar joylashuv yuborganida, ularning ma'lumotlari bu yerda ko'rinadi."
    )

# Asosiy menyuga qaytish
async def back_to_main_menu(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    from main import get_main_menu_keyboard
    await message.answer("🏠 Asosiy menyu", reply_markup=get_main_menu_keyboard('uz'))
    await state.clear()

async def handle_admin_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    command = message.text
    current_state = await state.get_state()
    
    # 1. YANGI ODAM QO'SHISH HOLATLARI
    if current_state == AdminStates.waiting_for_user_fullname:
        await process_user_fullname(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_user_phone:
        await process_user_phone(message, state)
        return
    
    elif current_state == AdminStates.waiting_for_user_language:
        await process_user_language(message, state)
        return
    
    elif current_state == AdminStates.waiting_content_id:
        await process_user_id_input(message, state)
        return
    
    # 2. REKLAMA YUBORISH HOLATLARI
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
    
    # 3. KONTENT QO'SHISH HOLATLARI
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
    
    # 4. KONTENT O'CHIRISH HOLATLARI
    elif current_state == AdminStates.deleting_content.state:
        await process_delete_category(message, state)
        return
    
    # 5. ASOSIY BUYRUQLAR
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
    
    # 📍 JOYLASHUVNI KO'RISH
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