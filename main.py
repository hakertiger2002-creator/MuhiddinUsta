# main.py faylida:

import asyncio
import logging
from datetime import datetime
from aiogram import F

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart, Command
from aiogram.types import (
    Message, ReplyKeyboardMarkup, KeyboardButton, 
    ReplyKeyboardRemove, CallbackQuery, Location,
    ContentType, InlineKeyboardMarkup, InlineKeyboardButton,
    FSInputFile, PhotoSize, Video, Document, InputFile
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

from database import db
from dotenv import load_dotenv
import os
import keep_alive

# ✅ TO'G'RI: admin modulini import qilish
import admin

# Log konfiguratsiyasi
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from aiogram import Bot

# .env faylini yuklash
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# ✅ TO'G'RI: admin modulini sozlash (bot yaratilgandan keyin)
admin.set_bot_and_admin(bot, ADMIN_ID)

async def get_bot_username():
    """Bot username'ini olish"""
    try:
        bot_info = await bot.get_me()
        return bot_info.username
    except Exception as e:
        logger.error(f"Failed to get bot username: {e}")
        return "MuhiddinUsta_bot"  # Default username

# ✅ YANGI: Bot username'ini global qilish
BOT_USERNAME = None

async def initialize_bot():
    """Botni ishga tushirish va username'ni olish"""
    global BOT_USERNAME
    BOT_USERNAME = await get_bot_username()
    logger.info(f"Bot username: {BOT_USERNAME}")

# Emojilar
EMOJIS = {
    "hello": "👋",
    "house": "🏠",
    "tools": "🛠️",
    "paint": "🎨",
    "tech": "💻",
    "video": "📹",
    "location": "📍",
    "phone": "📱",
    "language": "🌐",
    "contact": "📞",
    "check": "✅",
    "info": "ℹ️",
    "warning": "⚠️",
    "clock": "⏳",
    "admin": "👨‍💻",
    "user": "👤",
    "photo": "🖼️",
    "document": "📄",
    "next": "➡️",
    "prev": "⬅️",
    "home": "🏠",
    "lock": "🔒",
    "no_download": "⛔"
}

# Til matnlari
TEXTS = {
    "uz": {
        "welcome": f"{EMOJIS['hello']} Assalomu alaykum! Usta Elbek Botiga xush kelibsiz!",
        "full_welcome": "Hurmatli foydalanuvchi! Siz bu bot orqali o'zingizning uyingiz uchun eng so'nggi texnologiyalar va eng so'nggi tamirlash mahsulotlaridan xabardor bo'lishingiz mumkin. Uz/Ru tillarda tarjima bilan.",
        "register_prompt": "Hurmatli foydalanuvchi! Botdan to'liq foydalanish huquqiga ega bo'lish uchun ma'lumotlaringizni to'liq kiriting.",
        "choose_language": f"{EMOJIS['language']} Iltimos, kerakli tilni tanlang:",
        "share_phone": f"{EMOJIS['phone']} Telefon raqamingizni yuboring:",
        "checking_data": f"{EMOJIS['clock']} Ma'lumotlaringiz tekshirilmoqda",
        "reg_success": f"{EMOJIS['check']} Ro'yxatdan o'tish ma'lumotlaringiz muvaffaqiyatli tugadi.",
        "welcome_back": "Xush kelibsiz",
        "main_menu": "Asosiy menyu",
        "send_location": f"{EMOJIS['location']} Hurmatli foydalanuvchi! Tamirlash ishlarimiz ma'qul kelgan bo'lsa, joylashuvingizni yuboring. Joylashuv yuborish uchun 'Joylashuv' bo'limidan foydalaning.",
        "no_content": "⚠️ Hozircha bu bo'limda mediamavjud emas. Tez orada qo'shiladi.",
        "location_sent": "✅ Joylashuvingiz qabul qilindi! Tez orada siz bilan bog'lanamiz.",
        "language_changed": "✅ Til muvaffaqiyatli o'zgartirildi!",
        "blocked": "❌ Siz bloklangansiz! Botdan foydalana olmaysiz.",
        "admin_only": "❌ Bu buyruq faqat administratorlar uchun!",
        "content_available": "📂 Mavjud kontentlar:",
        "page_info": "Sahifa",
        "of": "/",
        "back_to_main": "Asosiy menyuga qaytish",
        "no_download": f"{EMOJIS['lock']} Ushbu kontent faqat ko'rish uchun. Saqlab olish imkoni yo'q.",
        "copyright": f"© Usta Elbek. Barcha huquqlar himoyalangan.",
        
        # ✅ YANGI: Kontakt uchun kalitlar
        "contact": "Usta Bilan Bog'lanish",
        "contact_phone": "Telefon raqam",
        "call_now": "Hozir qo'ng'iroq qiling",
        "working_hours": "Ish vaqtlari",
        "services": "Xizmat turlari",
        "payment_methods": "To'lov usullari",
        "address": "Manzil",
        "telegram": "Telegram"
    },
    "ru": {
        "welcome": f"{EMOJIS['hello']} Здравствуйте! Добро пожаловать в бот Usta Elbek!",
        "full_welcome": "Уважаемый пользователь! С помощью этого бота вы можете быть в курсе последних технологий и последних ремонтных продуктов для вашего дома. С переводом на уз/рус языках.",
        "register_prompt": "Уважаемый пользователь! Для получения права на полное использование бота введите свои данные полностью.",
        "choose_language": f"{EMOJIS['language']} Пожалуйста, выберите нужный язык:",
        "share_phone": f"{EMOJIS['phone']} Отправьте свой номер телефона:",
        "checking_data": f"{EMOJIS['clock']} Ваши данные проверяются",
        "reg_success": f"{EMOJIS['check']} Ваши регистрационные данные успешно завершены.",
        "welcome_back": "Добро пожаловать",
        "main_menu": "Главное меню",
        "send_location": f"{EMOJIS['location']} Уважаемый пользователь! Если наши ремонтные работы вам понравились, отправьте свое местоположение. Для отправки местоположения используйте раздел 'Местоположение'.",
        "no_content": "⚠️ В этом разделе пока нет медиа. Скоро будет добавлено.",
        "location_sent": "✅ Ваше местоположение принято! Скоро свяжемся с вами.",
        "language_changed": "✅ Язык успешно изменен!",
        "blocked": "❌ Вы заблокированы! Вы не можете использовать бота.",
        "admin_only": "❌ Эта команда только для администраторов!",
        "content_available": "📂 Доступные контенты:",
        "page_info": "Страница",
        "of": "из",
        "back_to_main": "Вернуться в главное меню",
        "no_download": f"{EMOJIS['lock']} Этот контент только для просмотра. Сохранение невозможно.",
        "copyright": f"© Usta Elbek. Все права защищены.",
        
        # ✅ YANGI: Kontakt uchun kalitlar
        "contact": "Связаться с Мастером",
        "contact_phone": "Номер телефона", 
        "call_now": "Позвонить сейчас",
        "working_hours": "Время работы",
        "services": "Виды услуг",
        "payment_methods": "Способы оплаты",
        "address": "Адрес",
        "telegram": "Телеграм"
    }
}

# Kategoriya mapping
CATEGORY_MAPPING = {
    "uz": {
        "classic": "Klassik Tamirlash",
        "glue": "Lepka Yopishtirish", 
        "gypsum": "Gipsi Carton Fason",
        "hitech": "HiTech Tamirlash",
        "full": "To'liq Tamirlash",
        "video": "Video Joylash"
    },
    "ru": {
        "classic": "Классический Ремонт",
        "glue": "Поклейка Обоев", 
        "gypsum": "Гипсокартон Фасон",
        "hitech": "HiTech Ремонт",
        "full": "Полный Ремонт",
        "video": "Видео Работы"
    }
}

# Kategoriya code mapping
CATEGORY_CODES = {
    "Klassik Tamirlash": "classic",
    "Lepka Yopishtirish": "glue",
    "Gipsi Carton Fason": "gypsum",
    "HiTech Tamirlash": "hitech",
    "To'liq Tamirlash": "full",
    "Video Joylash": "video",
    "Классический Ремонт": "classic",
    "Поклейка Обоев": "glue",
    "Гипсокартон Фасон": "gypsum",
    "HiTech Ремонт": "hitech",
    "Полный Ремонт": "full",
    "Видео Работы": "video"
}

# FSM holatlari
class RegistrationStates(StatesGroup):
    choosing_language = State()
    sharing_phone = State()

class AdminStates(StatesGroup):
    adding_content = State()
    waiting_for_content = State()
    waiting_for_caption = State()
    sending_message = State()
    blocking_user = State()
    unblocking_user = State()
    deleting_content = State()
    waiting_content_id = State()

class ChangeLanguageState(StatesGroup):
    choosing_language = State()

# Kontent ko'rish holatlari uchun ma'lumotlar
user_content_data = {}

# Klaviaturalar
def get_language_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🇺🇿 O'zbek"), KeyboardButton(text="🇷🇺 Русский")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_phone_keyboard(lang: str = 'uz'):
    text = "📱 Telefon raqamni yuborish" if lang == 'uz' else "📱 Отправить номер телефона"
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=text, request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def get_main_menu_keyboard(lang: str = 'uz'):
    texts = {
        "uz": {
            "classic": f"{EMOJIS['tools']} Klassik Tamirlash",
            "glue": f"{EMOJIS['paint']} Lepka Yopishtirish",
            "gypsum": f"{EMOJIS['house']} Gipsi Carton Fason",
            "hitech": f"{EMOJIS['tech']} HiTech Tamirlash",
            "full": f"{EMOJIS['tools']} To'liq Tamirlash",
            "contact": f"{EMOJIS['contact']} Usta Bilan Bog'lanish",
            "location": f"{EMOJIS['location']} Joylashuv",
            "video": f"{EMOJIS['video']} Video Ishlar",
            "language": f"{EMOJIS['language']} Tilni O'zgartirish"
        },
        "ru": {
            "classic": f"{EMOJIS['tools']} Классический Ремонт",
            "glue": f"{EMOJIS['paint']} Поклейка Обоев",
            "gypsum": f"{EMOJIS['house']} Гипсокартон Фасон",
            "hitech": f"{EMOJIS['tech']} HiTech Ремонт",
            "full": f"{EMOJIS['tools']} Полный Ремонт",
            "contact": f"{EMOJIS['contact']} Связаться с Мастером",
            "location": f"{EMOJIS['location']} Местоположение",
            "video": f"{EMOJIS['video']} Видео Работы",
            "language": f"{EMOJIS['language']} Изменить Язык"
        }
    }
    
    current_lang_texts = texts[lang]
    
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=current_lang_texts["classic"]), KeyboardButton(text=current_lang_texts["glue"])],
            [KeyboardButton(text=current_lang_texts["gypsum"]), KeyboardButton(text=current_lang_texts["hitech"])],
            [KeyboardButton(text=current_lang_texts["full"]), KeyboardButton(text=current_lang_texts["contact"])],
            [KeyboardButton(text=current_lang_texts["location"]), KeyboardButton(text=current_lang_texts["video"])],
            [KeyboardButton(text=current_lang_texts["language"])]
        ],
        resize_keyboard=True,
        persistent=True
    )

# Sahifalash uchun inline klaviatura (saqlash bloklangan)
def get_pagination_keyboard(category: str, current_page: int, total_pages: int, lang: str = 'uz'):
    keyboard = []
    
    # Sahifa tugmalari
    page_buttons = []
    if current_page > 0:
        page_buttons.append(InlineKeyboardButton(
            text=f"{EMOJIS['prev']}",
            callback_data=f"content_page:{category}:{current_page-1}"
        ))
    
    # ✅ O'ZGARISH: Page raqami ko'rsatilmaydi
    # page_buttons.append(InlineKeyboardButton(
    #     text=f"{current_page+1}/{total_pages}",
    #     callback_data="no_action"
    # ))
    
    if current_page < total_pages - 1:
        page_buttons.append(InlineKeyboardButton(
            text=f"{EMOJIS['next']}",
            callback_data=f"content_page:{category}:{current_page+1}"
        ))
    
    if page_buttons:  # Faqat tugmalar bo'lsa qo'sh
        keyboard.append(page_buttons)
    
    # Asosiy menyuga qaytish tugmasi
    keyboard.append([InlineKeyboardButton(
        text=f"{EMOJIS['home']} {TEXTS[lang]['back_to_main']}",
        callback_data="back_to_main"
    )])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# Animatsiya funksiyasi
async def show_simple_animation(message: Message, text: str):
    """Oddiy animatsiya"""
    msg = await message.answer(f"{text}.")
    await asyncio.sleep(0.7)
    await msg.edit_text(f"{text}..")
    await asyncio.sleep(0.7)
    await msg.edit_text(f"{text}...")
    await asyncio.sleep(0.7)
    await msg.edit_text(f"{text}.....")
    await asyncio.sleep(0.5)
    return msg


async def show_content(message: Message, category_code: str, page: int = 0, lang: str = 'uz'):
    """Kategoriya bo'yicha kontentlarni sahifalab ko'rsatish (saqlash bloklangan)"""
    user_id = message.from_user.id
    
    # Kontentlarni olish
    contents = db.get_contents_by_category(category_code, limit=1, offset=page)
    
    if not contents:
        await message.answer(TEXTS[lang]["no_content"])
        return
    
    total_contents = db.count_contents_by_category(category_code)
    total_pages = max(1, total_contents)
    
    if page >= total_contents:
        page = total_contents - 1
    
    content = contents[0]
    file_id = content[3]
    
    common_params = {
        "protect_content": True,
        "has_spoiler": True,
        "reply_markup": get_pagination_keyboard(category_code, page, total_pages, lang)
    }
    
    try:
        if content[2] == 'photo':
            await message.answer_photo(
                photo=file_id,
                caption=" ",
                **common_params
            )
        
        elif content[2] == 'video':
            await message.answer_video(
                video=file_id,
                caption=" ",
                supports_streaming=False,
                **common_params
            )
        
        elif content[2] == 'document':
            await message.answer_document(
                document=file_id,
                caption=" ",
                disable_content_type_detection=True,
                **common_params
            )
        
        # ✅ YANGI: Tilga qarab ogohlantirish xabarlari
        warning_messages = {
            "uz": """⚠️ DIQQAT: Bu kontent himoyalangan!
📵 Saqlash, yuklab olish, nusxa olish TAQIQLANGAN!
⚖️ Huquqbuzarlik qonuniy javobgarlikni keltirib chiqaradi.

⛔ <b>Ta'qiqlangan amallar:</b>
• Skrinshot olish
• Ekran yozib olish
• Forward qilish
• Nusxa ko'chirish
• Yuklab olish

🛡️ <b>Himoya:</b>
• Telegram himoyasi faollashtirilgan
• Spoiler himoyasi
• Maxsus kodlash

📞 <b>Qonuniy foydalanish uchun:</b>
+998 88 044-55-50""",
            
            "ru": """⚠️ ВНИМАНИЕ: Этот контент защищен!
📵 Сохранение, загрузка, копирование ЗАПРЕЩЕНО!
⚖️ Нарушение прав влечет юридическую ответственность.

⛔ <b>Запрещенные действия:</b>
• Делать скриншоты
• Записывать экран
• Пересылать
• Копировать
• Загружать

🛡️ <b>Защита:</b>
• Защита Telegram активирована
• Защита спойлерами
• Специальное кодирование

📞 <b>Для законного использования:</b>
+998 88 044-55-50"""
        }
        
        # Ogohlantirish xabarini yuborish
        warning = await message.answer(
            warning_messages[lang],
            parse_mode="HTML"
        )
        
        # 10 soniyadan keyin ogohlantirishni o'chirish
        await asyncio.sleep(10)
        await warning.delete()
        
    except Exception as e:
        logger.error(f"Content display error: {e}")
        await message.answer(f"❌ Kontentni ko'rsatishda xatolik: {str(e)}")

# Callback query handler (sahifalash uchun)
@dp.callback_query(F.data.startswith("content_page:"))
async def handle_content_pagination(callback: CallbackQuery):
    try:
        # Ma'lumotlarni ajratib olish
        _, category, page_str = callback.data.split(":")
        page = int(page_str)
        
        # Foydalanuvchi ma'lumotlarini olish
        user_id = callback.from_user.id
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        
        # Callback query'ni darhol javob berish
        await callback.answer()
        
        # Oldingi xabarni o'chirish
        try:
            await callback.message.delete()
        except:
            pass
        
        # Yangi kontentni ko'rsatish
        await show_content(callback.message, category, page, lang)
        
    except Exception as e:
        logger.error(f"Pagination error: {e}")
        # Xatolikda faqat answer berish, delete emas
        try:
            await callback.answer("Xatolik yuz berdi!", show_alert=True)
        except:
            pass

# No action callback
@dp.callback_query(F.data == "no_action")
async def handle_no_action(callback: CallbackQuery):
    await callback.answer()

# Asosiy menyuga qaytish
@dp.callback_query(F.data == "back_to_main")
async def handle_back_to_main(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        user_data = db.get_user(user_id)
        
        if not user_data:
            await callback.answer("Iltimos, avval ro'yxatdan o'ting!")
            return
        
        lang = user_data[3]
        name = user_data[1]
        welcome_text = f"{TEXTS[lang]['welcome_back']} {name}!"
        
        # Oldingi xabarni o'chirish
        await callback.message.delete()
        
        # Asosiy menyuni yuborish
        await callback.message.answer(welcome_text, reply_markup=get_main_menu_keyboard(lang))
        await callback.message.answer(TEXTS[lang]["main_menu"])
        await callback.message.answer(TEXTS[lang]["send_location"])
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Back to main error: {e}")
        await callback.answer("Xatolik yuz berdi!")
        
@dp.callback_query(F.data.startswith("copy_link:"))
async def handle_copy_link(callback: CallbackQuery):
    """Havolani nusxalash"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    try:
        link = callback.data.split(":")[1]
        # Havolani clipboard ga nusxalash (foydalanuvchi uchun)
        await callback.answer(f"✅ Havola nusxalandi!\n{link[:50]}...", show_alert=True)
    except Exception as e:
        await callback.answer("❌ Xatolik!", show_alert=True)        

# main.py faylida cmd_start funksiyasini shunday qiling:

@dp.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganligini tekshirish
    user_data = db.get_user(user_id)
    
    # Agar foydalanuvchi bazada bo'lsa va bloklangan bo'lsa
    if user_data and user_data[5] == 1:  # is_blocked = 1 (True)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return  # ❗ BU YERDA return QILING! Keyingi kod ishlamasin
    
    # ✅ ADMIN uchun: Doimo admin panelda qolish
    if user_id == ADMIN_ID:
        from admin import get_admin_keyboard
        await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        await message.answer("Admin panelga xush kelibsiz! Quyidagi tugmalardan birini tanlang:")
        await state.clear()
        return
    
    # Foydalanuvchilar uchun eski logika
    if db.is_user_registered(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3]
        name = user_data[1]
        welcome_text = f"{TEXTS[lang]['welcome_back']} {name}!"
        
        await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(lang))
        await message.answer(TEXTS[lang]["main_menu"])
        await message.answer(TEXTS[lang]["send_location"])
    else:
        await message.answer(TEXTS['uz']["welcome"])
        await message.answer(TEXTS['uz']["full_welcome"])
        await message.answer(TEXTS['uz']["register_prompt"])
        await message.answer(TEXTS['uz']["choose_language"], reply_markup=get_language_keyboard())
        await state.set_state(RegistrationStates.choosing_language)

# Tilni tanlash (ro'yxatdan o'tishda)
@dp.message(RegistrationStates.choosing_language)
async def process_language(message: Message, state: FSMContext):
    if message.text == "🇺🇿 O'zbek":
        lang = 'uz'
    elif message.text == "🇷🇺 Русский":
        lang = 'ru'
    else:
        await message.answer("Iltimos, tugmalardan birini tanlang!")
        return
    
    await state.update_data(language=lang)
    await message.answer(TEXTS[lang]["share_phone"], reply_markup=get_phone_keyboard(lang))
    await state.set_state(RegistrationStates.sharing_phone)

# Telefon raqamni qabul qilish
@dp.message(RegistrationStates.sharing_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    phone_number = message.contact.phone_number
    full_name = message.from_user.full_name
    user_id = message.from_user.id
    
    # Animatsiya boshlash
    anim_message = await show_simple_animation(message, TEXTS[lang]["checking_data"])
    
    # Ma'lumotlarni bazaga saqlash
    db.add_user(user_id, full_name, phone_number, lang)
    
    # Adminlarga xabar yuborish
    await notify_admin_about_new_user(user_id, full_name, phone_number, lang)
    
    # Animatsiyani to'xtatish
    try:
        await anim_message.delete()
    except:
        pass
    
    # Muvaffaqiyatli xabar
    await message.answer(TEXTS[lang]["reg_success"])
    
    # Asosiy menyu
    welcome_text = f"{TEXTS[lang]['welcome_back']} {full_name}!"
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(lang))
    await message.answer(TEXTS[lang]["main_menu"])
    await message.answer(TEXTS[lang]["send_location"])
    
    await state.clear()

# Adminlarga yangi foydalanuvchi haqida xabar yuborish
async def notify_admin_about_new_user(user_id: int, full_name: str, phone_number: str, language: str):
    """Yangi ro'yxatdan o'tgan foydalanuvchi haqida adminlarga xabar yuborish"""
    try:
        language_text = "🇺🇿 O'zbek" if language == 'uz' else "🇷🇺 Русский"
        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        total_users = len(db.get_all_users())
        
        admin_message = (
            f"🆕 YANGI FOYDALANUVCHI RO'YXATDAN O'TTI!\n\n"
            f"👤 Ism: {full_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📞 Telefon: {phone_number}\n"
            f"🌐 Til: {language_text}\n"
            f"⏰ Vaqt: {current_time}\n\n"
            f"✅ Jami foydalanuvchilar: {total_users}"
        )
        
        await bot.send_message(ADMIN_ID, admin_message)
        
        # Log qilish
        logger.info(f"New user registered: {full_name} (ID: {user_id})")
        
    except Exception as e:
        logger.error(f"Failed to notify admin about new user: {e}")
        
async def check_if_user_blocked(user_id: int) -> bool:
    """Foydalanuvchi bloklanganligini tekshirish"""
    user_data = db.get_user(user_id)
    if user_data and user_data[5] == 1:  # is_blocked = 1
        lang = user_data[3] if user_data else 'uz'
        return True, lang
    return False, None    

# main.py faylida yangi funksiya qo'shing:

async def check_user_block_status(user_id: int) -> bool:
    """Foydalanuvchi bloklanganligini tekshirish"""
    user_data = db.get_user(user_id)
    if user_data:
        is_blocked = user_data[5]  # 5-indeksda is_blocked maydoni
        return is_blocked == 1
    return False    

# main.py faylida

@dp.message(F.text.contains("Klassik Tamirlash") | F.text.contains("Классический Ремонт"))
async def classic_repair(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    if await check_user_block_status(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # ✅ Agar admin bo'lsa, admin panelda bo'lishini tekshirish
    if user_id == ADMIN_ID:
        from admin import AdminStates
        
        current_state = await state.get_state()
        
        # Agar admin panel holatida bo'lsa
        if current_state in [AdminStates.adding_content, 
                            AdminStates.deleting_content,
                            AdminStates.waiting_for_content,
                            AdminStates.waiting_for_caption]:
            from admin import handle_admin_command
            await handle_admin_command(message, state)
            return
        # Agar admin asosiy menyudan kategoriyani bosgan bo'lsa
        else:
            # Admin ham kategoriyadagi kontentlarni ko'rishni istayotgan bo'lishi mumkin
            user_data = db.get_user(message.from_user.id)
            lang = user_data[3] if user_data else 'uz'
            await show_content(message, "classic", 0, lang)
            return
    
    # ✅ Oddiy foydalanuvchilar uchun
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    await show_content(message, "classic", 0, lang)


@dp.message(F.text.contains("Lepka Yopishtirish") | F.text.contains("Поклейка Обоев"))
async def glue_repair(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    if await check_user_block_status(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # ✅ Agar admin bo'lsa
    if user_id == ADMIN_ID:
        from admin import AdminStates
        
        current_state = await state.get_state()
        
        # Agar admin panel holatida bo'lsa (kontent qo'shish jarayonida)
        if current_state in [AdminStates.adding_content, AdminStates.deleting_content]:
            from admin import handle_admin_command
            await handle_admin_command(message, state)
            return
    
    # ✅ Oddiy foydalanuvchilar uchun
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    await show_content(message, "glue", 0, lang)

@dp.message(F.text.contains("Gipsi Carton Fason") | F.text.contains("Гипсокартон Фасон"))
async def gypsum_repair(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    if await check_user_block_status(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # ✅ Agar admin bo'lsa
    if user_id == ADMIN_ID:
        from admin import AdminStates
        
        current_state = await state.get_state()
        
        if current_state in [AdminStates.adding_content, AdminStates.deleting_content]:
            from admin import handle_admin_command
            await handle_admin_command(message, state)
            return
    
    # ✅ Oddiy foydalanuvchilar uchun
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    await show_content(message, "gypsum", 0, lang)

@dp.message(F.text.contains("HiTech Tamirlash") | F.text.contains("HiTech Ремонт"))
async def hitech_repair(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    if await check_user_block_status(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # ✅ Agar admin bo'lsa
    if user_id == ADMIN_ID:
        from admin import AdminStates
        
        current_state = await state.get_state()
        
        if current_state in [AdminStates.adding_content, AdminStates.deleting_content]:
            from admin import handle_admin_command
            await handle_admin_command(message, state)
            return
    
    # ✅ Oddiy foydalanuvchilar uchun
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    await show_content(message, "hitech", 0, lang)

@dp.message(F.text.contains("To'liq Tamirlash") | F.text.contains("Полный Ремонт"))
async def full_repair(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    if await check_user_block_status(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # ✅ Agar admin bo'lsa
    if user_id == ADMIN_ID:
        from admin import AdminStates
        
        current_state = await state.get_state()
        
        # Agar admin panel holatida bo'lsa (kontent qo'shish jarayonida)
        if current_state in [AdminStates.adding_content, 
                           AdminStates.deleting_content]:
            from admin import handle_admin_command
            await handle_admin_command(message, state)
            return
    
    # ✅ Oddiy foydalanuvchilar uchun
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    await show_content(message, "full", 0, lang)

@dp.message(F.text.contains("Video Ishlar") | F.text.contains("Видео Работы"))
async def video_works(message: Message, state: FSMContext):  # ✅ state parametrini qo'shing
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    if await check_user_block_status(user_id):
        user_data = db.get_user(user_id)
        lang = user_data[3] if user_data else 'uz'
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # ✅ Agar admin bo'lsa
    if user_id == ADMIN_ID:
        from admin import AdminStates
        
        current_state = await state.get_state()
        
        if current_state in [AdminStates.adding_content, AdminStates.deleting_content]:
            from admin import handle_admin_command
            await handle_admin_command(message, state)
            return
    
    # ✅ Oddiy foydalanuvchilar uchun
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    await show_content(message, "video", 0, lang)

@dp.message(F.text.contains("Usta Bilan Bog'lanish") | F.text.contains("Связаться с Мастером"))
async def contact_master(message: Message):
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    # 1. Inline keyboard (Telegram havolasi uchun)
    inline_keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="👨‍💼 Telegramda yozish",
                    url="https://t.me/UstaMuhiddin_bot"
                )
            ]
        ]
    )
    
    # 2. Reply keyboard (telefon raqami uchun)
    reply_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📞 Telefon raqamni olish",
                    request_contact=True
                )
            ],
            [
                KeyboardButton(text=f"🏠 {TEXTS[lang]['back_to_main']}")
            ]
        ],
        resize_keyboard=True
    )
    
    phone_number = "+998 88 044-55-50"
    
    if lang == 'uz':
        text = f"""<b>📞 Usta Elbek bilan bog'lanish:</b>

<code>{phone_number}</code>

<b>✅ Telefon qo'ng'iroqi uchun:</b>
1. "Telefon raqamni olish" tugmasini bosing
2. Telefon ilovasiga o'ting
3. Qo'ng'iroq qiling

<b>👨‍💼 Telegram:</b> @MuhhiddinUsta_bot
<b>📍 Manzil:</b> Toshkent

<b>⏰ Ish vaqtlari:</b>
• Dushanba-Yakshanba: 9:00 - 18:00
• Juma Kuni: Dam olish"""
    else:
        text = f"""<b>📞 Для связи с мастером Элбеком:</b>

<code>{phone_number}</code>

<b>✅ Для телефонного звонка:</b>
1. Нажмите "Telefon raqamni olish"
2. Перейдите в приложение телефона
3. Позвоните

<b>👨‍💼 Telegram:</b> @MuhiddinUsta_bot
<b>📍 Адрес:</b> Ташкент

<b>⏰ Время работы:</b>
• Понедельник-Воскресенье: 9:00 - 18:00
• Пятница: Выходной"""
    
    # Inline keyboard bilan xabar (Telegram havolasi)
    await message.answer(
        text,
        reply_markup=inline_keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True
    )
    
    # Reply keyboard bilan xabar (telefon raqami)
    await message.answer(
        "📱 Telefon raqamni olish uchun quyidagi tugmani bosing:",
        reply_markup=reply_keyboard
    )
    
@dp.message(F.contact)
async def handle_contact(message: Message):
    """Foydalanuvchi telefon raqamini qabul qilish"""
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    user_data = db.get_user(user_id)
    
    if not user_data:
        await message.answer("Iltimos, avval ro'yxatdan o'ting!")
        return
    
    # Agar foydalanuvchi bloklangan bo'lsa
    if user_data[5] == 1:  # is_blocked = 1 (True)
        lang = user_data[3]
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # Agar bu usta bilan bog'lanish uchun yuborilgan bo'lsa
    if message.contact:
        phone_number = message.contact.phone_number
        
        # Adminlarga xabar yuborish
        user_name = user_data[1]
        
        admin_message = (
            f"📞 YANGI TELEFON CHAQIRUVI SO'ROVI!\n\n"
            f"👤 Foydalanuvchi: {user_name}\n"
            f"🆔 ID: {user_id}\n"
            f"📞 Telefon: {phone_number}\n"
            f"⏰ Vaqt: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        try:
            await bot.send_message(ADMIN_ID, admin_message)
        except:
            pass
        
        # Foydalanuvchiga javob
        lang = user_data[3]
        
        response = {
            "uz": f"✅ Telefon raqamingiz qabul qilindi! Usta Elbek tez orada siz bilan bog'lanadi.\n📞 Ustaning telefoni: +998 (95) 902-32-32",
            "ru": f"✅ Ваш номер телефона принят! Мастер Элбек скоро свяжется с вами.\n📞 Телефон мастера: +998 (95) 902-32-32"
        }
        
        await message.answer(response[lang])
        
        # Asosiy menyuga qaytish
        await message.answer(
            TEXTS[lang]["main_menu"],
            reply_markup=get_main_menu_keyboard(lang)
        )   

# main.py faylida:

# ============ ADMIN BROADCAST CALLBACK HANDLERS ============

@dp.callback_query(F.data.startswith("confirm_broadcast:"))
async def handle_confirm_broadcast(callback: CallbackQuery, state: FSMContext):
    """Reklamani tasdiqlash va yuborish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    try:
        broadcast_type = callback.data.split(":")[1]
        data = await state.get_data()
        
        # Qabul qiluvchilarni aniqlash
        recipients_type = data.get('broadcast_recipients', '👥 Barcha foydalanuvchilar')
        
        if recipients_type == "👥 Barcha foydalanuvchilar":
            users = db.get_all_users()
        elif recipients_type == "✅ Faol foydalanuvchilar":
            users = db.get_active_users()
        elif recipients_type == "🆕 Yangi foydalanuvchilar":
            all_users = db.get_all_users()
            users = all_users[-50:] if len(all_users) > 50 else all_users
        else:
            users = db.get_active_users()
        
        total_users = len(users)
        success = 0
        failed = 0
        
        # Progress xabari
        progress_msg = await callback.message.answer(
            f"📤 <b>Reklama yuborilmoqda...</b>\n\n"
            f"👥 Nisbat: {recipients_type}\n"
            f"📊 Jami: {total_users} ta\n"
            f"✅ Yuborildi: {success}\n"
            f"❌ Xato: {failed}\n\n"
            f"⏳ Iltimos, kuting...",
            parse_mode="HTML"
        )
        
        # Har bir foydalanuvchiga yuborish
        for index, user in enumerate(users, 1):
            user_id = user[0]
            
            try:
                if broadcast_type == "text":
                    await bot.send_message(
                        user_id, 
                        data['broadcast_text'], 
                        parse_mode="HTML"
                    )
                
                elif broadcast_type == "photo":
                    await bot.send_photo(
                        user_id,
                        photo=data['broadcast_file_id'],
                        caption=data.get('broadcast_caption', ''),
                        parse_mode="HTML"
                    )
                
                elif broadcast_type == "video":
                    await bot.send_video(
                        user_id,
                        video=data['broadcast_file_id'],
                        caption=data.get('broadcast_caption', ''),
                        parse_mode="HTML",
                        supports_streaming=True
                    )
                
                elif broadcast_type == "document":
                    await bot.send_document(
                        user_id,
                        document=data['broadcast_file_id'],
                        caption=data.get('broadcast_caption', ''),
                        parse_mode="HTML"
                    )
                
                success += 1
                
                # Har 10 ta yuborilganda progress yangilash
                if success % 10 == 0 or index == total_users:
                    await progress_msg.edit_text(
                        f"📤 <b>Reklama yuborilmoqda...</b>\n\n"
                        f"👥 Nisbat: {recipients_type}\n"
                        f"📊 Jami: {total_users} ta\n"
                        f"✅ Yuborildi: {success}\n"
                        f"❌ Xato: {failed}\n\n"
                        f"⏳ {index}/{total_users} ({int((index/total_users)*100)}%)",
                        parse_mode="HTML"
                    )
                
                # Telegram limitlarini buzmaslik uchun kutish
                await asyncio.sleep(0.05)
                
            except Exception as e:
                failed += 1
                logger.error(f"Failed to send to user {user_id}: {e}")
        
        # Yakuniy natija
        result_message = (
            f"✅ <b>REKLAMA YUBORISH YAKUNLANDI!</b>\n\n"
            f"📊 <b>NATIJALAR:</b>\n"
            f"👥 Nisbat: {recipients_type}\n"
            f"📊 Jami foydalanuvchilar: {total_users}\n"
            f"✅ Muvaffaqiyatli: {success}\n"
            f"❌ Muvaffaqiyatsiz: {failed}\n"
            f"📈 Muvaffaqiyat darajasi: {int((success/total_users)*100) if total_users > 0 else 0}%\n\n"
            f"⏰ Vaqt: {datetime.now().strftime('%H:%M:%S')}"
        )
        
        await progress_msg.edit_text(result_message, parse_mode="HTML")
        await callback.answer(f"✅ {success} ta foydalanuvchiga yuborildi!", show_alert=True)
        
        # Holatni tozalash
        await state.clear()
        
        # Admin panelga qaytish
        from admin import get_admin_keyboard
        await callback.message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        await callback.answer(f"❌ Xatolik: {str(e)[:100]}", show_alert=True)

@dp.callback_query(F.data == "cancel_broadcast")
async def handle_cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    """Reklamani bekor qilish"""
    await callback.answer("❌ Reklama bekor qilindi!")
    await state.clear()
    from admin import get_admin_keyboard
    await callback.message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# Admin panelga o'tish (faqat admin uchun)
@dp.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer(TEXTS['uz']["admin_only"])
        return
    
    # Admin panel import qilish
    from admin import get_admin_keyboard
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await message.answer("Admin panelga xush kelibsiz! Quyidagi tugmalardan birini tanlang:")

# Admin buyruqlarini boshqarish
@dp.message(F.text.contains("Admin Panel") | F.text.contains("Админ Панель"))
async def admin_panel_handler(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    
    from admin import get_admin_keyboard
    await message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())

# Tilni o'zgartirishni boshlash
@dp.message(F.text.contains("Tilni O'zgartirish") | F.text.contains("Изменить Язык"))
async def start_change_language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    user_data = db.get_user(user_id)
    if not user_data:
        await message.answer("Iltimos, avval ro'yxatdan o'ting!", reply_markup=get_language_keyboard())
        return
    
    # Agar foydalanuvchi bloklangan bo'lsa
    if user_data[5] == 1:  # is_blocked = 1
        lang = user_data[3]
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # Agar bloklanmagan bo'lsa, asosiy kod ishlaydi
    current_lang = user_data[3]
    
    # Hozirgi tilni saqlash
    await state.update_data(current_lang=current_lang)
    
    # Tilni tanlash klaviaturasini yuborish
    await message.answer(TEXTS['uz']["choose_language"], reply_markup=get_language_keyboard())
    await state.set_state(ChangeLanguageState.choosing_language)

# main.py faylida process_change_language funksiyasini shunday tuzating:

# Tilni tanlash (o'zgartirishda)
@dp.message(ChangeLanguageState.choosing_language)
async def process_change_language(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    user_data = db.get_user(user_id)
    if user_data and user_data[5] == 1:  # is_blocked = 1
        lang = user_data[3]
        await message.answer(TEXTS[lang]["blocked"])
        await state.clear()
        return
    
    # Yangi tilni aniqlash
    if message.text == "🇺🇿 O'zbek":
        new_lang = 'uz'
    elif message.text == "🇷🇺 Русский":
        new_lang = 'ru'
    else:
        await message.answer("Iltimos, tugmalardan birini tanlang!", reply_markup=get_language_keyboard())
        return
    
    # Eski tilni olish
    data = await state.get_data()
    old_lang = data.get('current_lang', 'uz')
    
    # Agar til bir xil bo'lsa
    if old_lang == new_lang:
        if new_lang == 'uz':
            await message.answer("Siz allaqachon O'zbek tilini tanlagansiz!", reply_markup=get_main_menu_keyboard(new_lang))
        else:
            await message.answer("Вы уже выбрали русский язык!", reply_markup=get_main_menu_keyboard(new_lang))
        await state.clear()
        return
    
    # Tilni yangilash
    db.update_user_language(user_id, new_lang)
    
    # Foydalanuvchi ma'lumotlarini yangilangan holda olish
    user_data = db.get_user(user_id)
    full_name = user_data[1] if user_data else message.from_user.full_name
    
    # Muvaffaqiyatli xabar
    await message.answer(TEXTS[new_lang]["language_changed"])
    
    # Asosiy menyuga qaytish
    welcome_text = f"{TEXTS[new_lang]['welcome_back']} {full_name}!"
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(new_lang))
    await message.answer(TEXTS[new_lang]["main_menu"])
    await message.answer(TEXTS[new_lang]["send_location"])
    
    await state.clear()

# Joylashuv yuborish
@dp.message(F.text.contains("Joylashuv") | F.text.contains("Местоположение"))
async def request_location(message: Message):
    user_data = db.get_user(message.from_user.id)
    lang = user_data[3] if user_data else 'uz'
    
    location_keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{EMOJIS['location']} Joylashuv yuborish", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    ) if lang == 'uz' else ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"{EMOJIS['location']} Отправить местоположение", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    
    await message.answer(TEXTS[lang]["send_location"], reply_markup=location_keyboard)

# main.py faylida handle_location funksiyasini shunday tuzating:

@dp.message(F.location)
async def handle_location(message: Message):
    user_id = message.from_user.id
    
    # ✅ AVVAL: Bloklanganlikni tekshirish
    user_data = db.get_user(user_id)
    
    if not user_data:
        await message.answer("Iltimos, avval ro'yxatdan o'ting!")
        return
    
    # Agar foydalanuvchi bloklangan bo'lsa
    if user_data[5] == 1:  # is_blocked = 1 (True)
        lang = user_data[3]
        await message.answer(TEXTS[lang]["blocked"])
        return
    
    # Agar foydalanuvchi bloklanmagan bo'lsa, asosiy kod ishlaydi
    full_name = user_data[1]
    phone_number = user_data[2]
    lang = user_data[3]
    
    # Animatsiya
    anim_msg = await message.answer("📍 Joylashuv qabul qilinmoqda...")
    
    # Database'ga saqlash
    location_id = db.add_location(
        user_id=user_id,
        full_name=full_name,
        phone_number=phone_number,
        latitude=message.location.latitude,
        longitude=message.location.longitude
    )
    
    # Adminlarga xabar yuborish
    await notify_admin_about_location(location_id, user_data, message.location)
    
    await anim_msg.delete()
    
    # Foydalanuvchiga xabar
    location_response = {
        "uz": "✅ Joylashuvingiz qabul qilindi! Admin tez orada ko'rib chiqadi.",
        "ru": "✅ Ваше местоположение принято! Админ скоро рассмотрит."
    }
    
    await message.answer(location_response[lang])
    
    # Asosiy menyuga qaytish
    await message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang))
    
# main.py fayliga:

async def notify_admin_about_location(location_id: int, user_data: tuple, location):
    """Adminlarga yangi joylashuv haqida xabar yuborish"""
    try:
        user_id = user_data[0]
        full_name = user_data[1]
        phone_number = user_data[2]
        language = user_data[3]
        
        # Til matnini tayyorlash (backslash'siz)
        language_text = "🇺🇿 O'zbek" if language == 'uz' else "🇷🇺 Русский"
        
        # Admin uchun xabar (backslash'siz)
        admin_message = (
            f"📍 <b>YANGI JOYLASHUV!</b>\n\n"
            f"🆔 <b>ID:</b> {location_id}\n"
            f"👤 <b>Foydalanuvchi:</b> {full_name}\n"
            f"🆔 <b>User ID:</b> {user_id}\n"
            f"📞 <b>Telefon:</b> {phone_number}\n"
            f"🌐 <b>Til:</b> {language_text}\n"
            f"📍 <b>Koordinatalar:</b>\n"
            f"   • Kenglik: {location.latitude}\n"
            f"   • Uzunlik: {location.longitude}\n"
            f"⏰ <b>Vaqt:</b> {datetime.now().strftime('%H:%M %d.%m.%Y')}\n\n"
            f"✅ <i>Admin panelda '📍 Joylashuv Qabul Qilish' bo'limiga kiring</i>"
        )
        
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
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
            ]
        ])
        
        await bot.send_message(
            ADMIN_ID,
            admin_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Failed to notify admin about location: {e}") 
        
# main.py faylida notify_admin_about_new_user funksiyasidan keyin yangi funksiya qo'shing:

async def send_welcome_message_to_user(user_id: int, full_name: str, lang: str):
    """Yangi ro'yxatdan o'tgan foydalanuvchiga xush kelish xabarini yuborish"""
    try:
        welcome_messages = {
            "uz": f"""🎉 <b>Xush kelibsiz, {full_name}!</b>

✅ <b>Muhiddin Usta botiga muvaffaqiyatli ro'yxatdan o'tdingiz!</b>

📱 <b>Bot imkoniyatlari:</b>
• Turli tamirlash usullarini ko'rish
• Usta Elbek bilan bog'lanish
• Joylashuv yuborish
• Videolarni tomosha qilish

⚠️ <b>OGOHLANTIRISH:</b>
• Bot qoidalariga qat'iy rioya qiling
• Kontentlarni yuklab olish yoki ko'chirish TAQIQLANGAN
• Huquqbuzarlik qonuniy javobgarlikni keltirib chiqaradi

📞 <b>Muhiddin Usta bilan bog'lanish:</b>
+998 88 044-55-50

🏠 <b>Xizmat turlari:</b>
• Klassik tamirlash
• Lepka yopishtirish
• Gipsi carton fason
• HiTech tamirlash
• To'liq tamirlash

📍 <b>Manzil:</b> Toshkent

⏰ <b>Ish vaqtlari:</b>
Dushanba-Yakshanba: 9:00 - 18:00
Juma kuni: Dam olish

🌟 <b>Biz sizning uyingizni chiroyli qilish uchun mavjudmiz!</b>

<code>© Muhiddin Usta. Barcha huquqlar himoyalangan.</code>""",
            
            "ru": f"""🎉 <b>Добро пожаловать, {full_name}!</b>

✅ <b>Вы успешно зарегистрировались в боте Muhiddin Usta!</b>

📱 <b>Возможности бота:</b>
• Просмотр различных методов ремонта
• Связь с мастером Элбеком
• Отправка местоположения
• Просмотр видео

⚠️ <b>ПРЕДУПРЕЖДЕНИЕ:</b>
• Строго соблюдайте правила бота
• Скачивание или копирование контента ЗАПРЕЩЕНО
• Нарушение прав влечет юридическую ответственность

📞 <b>Связаться с мастером Элбеком:</b>
+998 88 044-55-50

🏠 <b>Виды услуг:</b>
• Классический ремонт
• Поклейка обоев
• Гипсокартон фасон
• HiTech ремонт
• Полный ремонт

📍 <b>Адрес:</b> Ташкент

⏰ <b>Время работы:</b>
Понедельник-Воскресенье: 9:00 - 18:00
Пятница: Выходной

🌟 <b>Мы здесь, чтобы сделать ваш дом красивым!</b>

<code>© Muhiddin Usta. Все права защищены.</code>"""
        }
        
        await bot.send_message(user_id, welcome_messages[lang], parse_mode="HTML")
        logger.info(f"Welcome message sent to user {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome message: {e}")

# process_phone funksiyasida (ro'yxatdan o'tishda) ushbu funksiyani chaqiring:
@dp.message(RegistrationStates.sharing_phone, F.contact)
async def process_phone(message: Message, state: FSMContext):
    data = await state.get_data()
    lang = data.get('language', 'uz')
    
    phone_number = message.contact.phone_number
    full_name = message.from_user.full_name
    user_id = message.from_user.id
    
    # Animatsiya boshlash
    anim_message = await show_simple_animation(message, TEXTS[lang]["checking_data"])
    
    # Ma'lumotlarni bazaga saqlash
    db.add_user(user_id, full_name, phone_number, lang)
    
    # ✅ YANGI: Foydalanuvchiga xush kelish xabarini yuborish
    await send_welcome_message_to_user(user_id, full_name, lang)
    
    # Adminlarga xabar yuborish
    await notify_admin_about_new_user(user_id, full_name, phone_number, lang)
    
    # Animatsiyani to'xtatish
    try:
        await anim_message.delete()
    except:
        pass
    
    # Muvaffaqiyatli xabar
    await message.answer(TEXTS[lang]["reg_success"])
    
    # Asosiy menyu
    welcome_text = f"{TEXTS[lang]['welcome_back']} {full_name}!"
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(lang))
    await message.answer(TEXTS[lang]["main_menu"])
    await message.answer(TEXTS[lang]["send_location"])
    
    await state.clear()        

# main.py faylida faqat YANGI callback handler'larni saqlaymiz:

@dp.callback_query(F.data.startswith("view_location:"))
async def handle_view_location(callback: CallbackQuery):
    """Joylashuvni ko'rish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
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
            caption=f"📍 Joylashuv #{location_id}\n👤 {location_data[2]}"
        )
        
        # Tasdiqlash/Rad etish tugmalari
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
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
                )
            ]
        ])
        
        await callback.message.answer(location_info, reply_markup=keyboard, parse_mode="HTML")
        await callback.answer()
        
    except Exception as e:
        logger.error(f"View location error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

@dp.callback_query(F.data.startswith("accept_location:"))
async def handle_accept_location(callback: CallbackQuery):
    """Joylashuvni tasdiqlash"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
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
                "uz": "✅ <b>Joylashuvingiz tasdiqlandi!</b>\n\nUsta Elbek tez orada siz bilan bog'lanadi.\n📞 Telefon: +998 95 902-32-32",
                "ru": "✅ <b>Ваше местоположение подтверждено!</b>\n\nМастер Элбек скоро свяжется с вами.\n📞 Телефон: +998 95 902-32-32"
            }
            
            try:
                await bot.send_message(user_id, user_message[lang], parse_mode="HTML")
            except:
                pass
        
        # Admin uchun xabar
        await callback.answer(f"✅ Joylashuv #{location_id} tasdiqlandi!", show_alert=True)
        
        # ✅ Admin panelga qaytish
        from admin import show_latest_locations
        await callback.message.delete()
        await show_latest_locations(callback.message)
        
    except Exception as e:
        logger.error(f"Accept location error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

@dp.callback_query(F.data.startswith("reject_location:"))
async def handle_reject_location(callback: CallbackQuery):
    """Joylashuvni rad etish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
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
                "uz": "❌ <b>Joylashuvingiz rad etildi.</b>\n\nIltimos, boshqa joylashuv yuboring yoki telefon orqali bog'laning.\n📞 +998 95 902-32-32",
                "ru": "❌ <b>Ваше местоположение отклонено.</b>\n\nПожалуйста, отправьте другое местоположение или свяжитесь по телефону.\n📞 +998 95 902-32-32"
            }
            
            try:
                await bot.send_message(user_id, user_message[lang], parse_mode="HTML")
            except:
                pass
        
        # Admin uchun xabar
        await callback.answer(f"❌ Joylashuv #{location_id} rad etildi!", show_alert=True)
        
        # ✅ Admin panelga qaytish
        from admin import show_latest_locations
        await callback.message.delete()
        await show_latest_locations(callback.message)
        
    except Exception as e:
        logger.error(f"Reject location error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

# ============ ADMIN LOCATION CALLBACK HANDLERS ============

@dp.callback_query(F.data == "refresh_locations_admin")
async def handle_refresh_locations_admin(callback: CallbackQuery):
    """Admin panelda joylashuvlarni yangilash"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    from admin import show_latest_locations
    await callback.message.delete()
    await show_latest_locations(callback.message)
    await callback.answer("🔄 Yangilandi!")

@dp.callback_query(F.data == "view_all_locations_admin")
async def handle_view_all_locations_admin(callback: CallbackQuery):
    """Barcha joylashuvlarni ko'rish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    from admin import show_all_locations_admin
    await callback.message.delete()
    await show_all_locations_admin(callback.message)
    await callback.answer()

@dp.callback_query(F.data == "view_latest_location")
async def handle_view_latest_location(callback: CallbackQuery):
    """Eng so'nggi joylashuvni ko'rish"""
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    from admin import show_latest_locations
    await callback.message.delete()
    await show_latest_locations(callback.message)
    await callback.answer()

# main.py faylida handle_all_messages funksiyasini yangilang:
@dp.message()
async def handle_all_messages(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # ✅ 1. AVVAL: Bloklanganlikni tekshirish (FAQAT ADMIN EMAS)
    if user_id != ADMIN_ID:  # Admin uchun tekshirmaymiz
        user_data = db.get_user(user_id)
        if user_data and user_data[5] == 1:  # is_blocked = 1 (True)
            lang = user_data[3] if user_data else 'uz'
            await message.answer(TEXTS[lang]["blocked"])
            return  # ❗ Keyingi kod ishlamasin
    
    # ✅ 2. Agar admin bo'lsa, admin buyruqlarini tekshirish
    if user_id == ADMIN_ID:
        from admin import handle_admin_command
        await handle_admin_command(message, state)
        return
    
    # ✅ 3. Agar foydalanuvchi til o'zgartirish holatida bo'lsa
    current_state = await state.get_state()
    if current_state == ChangeLanguageState.choosing_language:
        await process_change_language(message, state)
        return
    
    # ✅ 4. Agar ro'yxatdan o'tish holatida bo'lsa
    if current_state in [RegistrationStates.choosing_language, RegistrationStates.sharing_phone]:
        # Bu holatlar allaqachon boshqa handlerlar tomonidan qayta ishlanadi
        return
    
    # ✅ 5. Boshqa barcha xabarlar uchun asosiy menyuni ko'rsatish
    user_data = db.get_user(user_id)
    if user_data:
        lang = user_data[3]
        await message.answer(TEXTS[lang]["main_menu"], reply_markup=get_main_menu_keyboard(lang))

# main.py faylida yangi funksiya qo'shing

async def delete_forwarded_content(chat_id: int, message_id: int):
    """Forward qilingan kontentlarni o'chirish"""
    try:
        await bot.delete_message(chat_id, message_id)
        logger.info(f"Forwarded content deleted: {chat_id}/{message_id}")
    except Exception as e:
        logger.error(f"Cannot delete forwarded content: {e}")

# Forward va kopiya qilishni bloklash handler'i
@dp.message(F.forward_from_chat)
async def handle_forwarded_content(message: Message):
    """Forward qilingan kontentlarni o'chirish"""
    user_id = message.from_user.id
    
    # Agar admin bo'lmasa
    if user_id != ADMIN_ID:
        try:
            await message.delete()
            
            # Ogohlantirish xabarlari
            user_data = db.get_user(user_id)
            lang = user_data[3] if user_data else 'uz'
            
            warning_messages = {
                "uz": """🚫 <b>OGOHLANTIRISH!</b>

❌ <b>Kontentlarni forward qilish taqiqlanadi!</b>

Bu amal bot qoidalariga ziddir.

⚖️ <b>Ogohlantirishlar:</b>
• 1-chi ogohlantirish: Bu xabar
• 2-chi ogohlantirish: Bloklash
• 3-chi ogohlantirish: Doimiy bloklash

📞 <b>Savollar uchun:</b>
+998 88 044-55-50

<code>© Usta Elbek. Barcha huquqlar himoyalangan.</code>""",
                
                "ru": """🚫 <b>ПРЕДУПРЕЖДЕНИЕ!</b>

❌ <b>Пересылка контента запрещена!</b>

Это действие нарушает правила бота.

⚖️ <b>Предупреждения:</b>
• 1-е предупреждение: Это сообщение
• 2-е предупреждение: Блокировка
• 3-е предупреждение: Постоянная блокировка

📞 <b>По вопросам:</b>
+998 88 044-55-50

<code>© Muhiddin Usta. Все права защищены.</code>"""
            }
            
            warning_msg = await message.answer(
                warning_messages.get(lang, warning_messages['uz']),
                parse_mode="HTML"
            )
            await asyncio.sleep(5)
            await warning_msg.delete()
            
        except Exception as e:
            logger.error(f"Failed to delete forwarded message: {e}")

# Media guruhlarni bloklash
@dp.message(F.media_group_id)
async def handle_media_group(message: Message):
    """Media guruhlarini bloklash"""
    user_id = message.from_user.id
    
    # Agar admin bo'lmasa
    if user_id != ADMIN_ID:
        try:
            await message.delete()
        except:
            pass
            
@dp.message(F.content_type.in_({ContentType.PHOTO, ContentType.VIDEO, ContentType.DOCUMENT}))
async def handle_all_media(message: Message):
    """Barcha media'lar forward bo'lsa o'chirish"""
    if message.forward_from or message.forward_from_chat:
        try:
            await message.delete()
            
            # Foydalanuvchi ma'lumotlari
            user_data = db.get_user(message.from_user.id)
            lang = user_data[3] if user_data else 'uz'
            
            warning_messages = {
                "uz": "🚫 Bu kontent forward qilish mumkin emas!",
                "ru": "🚫 Этот контент нельзя пересылать!"
            }
            
            warning = await message.answer(warning_messages.get(lang, warning_messages['uz']))
            await asyncio.sleep(3)
            await warning.delete()
        except:
            pass

# 2. Media guruhlarini bloklash
@dp.message(F.media_group_id)
async def block_media_groups(message: Message):
    """Media guruhlarini to'liq bloklash"""
    try:
        await message.delete()
    except:
        pass

# 3. Copy/paste ni bloklash
@dp.message(F.text.contains("@UstaElbekBot"))
async def block_copy_paste(message: Message):
    """Bot nomi ko'chirilgan xabarlarni o'chirish"""
    try:
        await message.delete()
        
        # Foydalanuvchi ma'lumotlari
        user_data = db.get_user(message.from_user.id)
        lang = user_data[3] if user_data else 'uz'
        
        warning_messages = {
            "uz": "⚠️ Bot nomini ko'chirish taqiqlanadi!",
            "ru": "⚠️ Копирование имени бота запрещено!"
        }
        
        warning = await message.answer(warning_messages.get(lang, warning_messages['uz']))
        await asyncio.sleep(3)
        await warning.delete()
        
    except:
        pass

# main.py faylida, boshqa callback handler'lardan KEYIN qo'shing:

# ============ ADMIN CONTENT DELETE HANDLERS ============

@dp.callback_query(F.data.startswith("delete_content:"))
async def handle_delete_content_callback(callback: CallbackQuery, state: FSMContext):
    """Inline tugma orqali kontent o'chirish"""
    from admin import ADMIN_ID
    from database import db
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    try:
        # Callback data: delete_content:content_id
        content_id = int(callback.data.split(":")[1])
        
        # Kontentni o'chirish
        db.delete_content(content_id)
        
        # Javob berish
        await callback.answer(f"✅ Kontent #{content_id} o'chirildi!")
        
        # Xabarni yangilash yoki o'chirish
        await callback.message.delete()
        
        # Admin panelga qaytish
        from admin import get_admin_keyboard
        await callback.message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        
        await state.clear()
        
    except Exception as e:
        logger.error(f"Delete content error: {e}")
        await callback.answer("❌ Xatolik yuz berdi!", show_alert=True)

@dp.callback_query(F.data.startswith("delete_all:"))
async def handle_delete_all_callback(callback: CallbackQuery):
    """Barcha kontentlarni bir vaqtda o'chirish"""
    from admin import ADMIN_ID
    from database import db
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    try:
        category = callback.data.split(":")[1]
        contents = db.get_contents_by_category(category)
        
        if not contents:
            await callback.answer("❌ Bu kategoriyada kontent yo'q!")
            return
        
        # Tasdiqlash klaviaturasi
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ HA, O'chirish", callback_data=f"confirm_delete_all:{category}"),
                InlineKeyboardButton(text="❌ BEKOR QILISH", callback_data="cancel_delete")
            ]
        ])
        
        await callback.message.answer(
            f"⚠️ <b>DIQQAT!</b>\n\n"
            f"<b>{len(contents)} ta kontentni</b> o'chirmoqchimisiz?\n"
            f"Bu amalni <b>bekor qilib bo'lmaydi!</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Delete all error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

@dp.callback_query(F.data.startswith("confirm_delete_all:"))
async def handle_confirm_delete_all(callback: CallbackQuery):
    """Barcha kontentlarni o'chirishni tasdiqlash"""
    from admin import ADMIN_ID
    from database import db
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    try:
        category = callback.data.split(":")[1]
        contents = db.get_contents_by_category(category)
        
        # Barcha kontentlarni o'chirish
        deleted_count = 0
        for content in contents:
            db.delete_content(content[0])
            deleted_count += 1
        
        # Javob berish
        await callback.answer(f"✅ {deleted_count} ta kontent o'chirildi!", show_alert=True)
        
        # Xabarlarni o'chirish
        await callback.message.delete()
        
        # Admin panelga qaytish
        from admin import get_admin_keyboard
        await callback.message.answer(
            f"✅ <b>{deleted_count} ta kontent muvaffaqiyatli o'chirildi!</b>\n"
            f"📁 Kategoriya: {category}",
            parse_mode="HTML"
        )
        await callback.message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
        
    except Exception as e:
        logger.error(f"Confirm delete all error: {e}")
        await callback.answer("❌ Xatolik!", show_alert=True)

@dp.callback_query(F.data == "cancel_delete")
async def handle_cancel_delete(callback: CallbackQuery):
    """O'chirishni bekor qilish"""
    await callback.answer("❌ O'chirish bekor qilindi!")
    await callback.message.delete()

@dp.callback_query(F.data == "delete_back")
async def handle_delete_back(callback: CallbackQuery):
    """O'chirishdan orqaga qaytish"""
    from admin import ADMIN_ID, get_admin_keyboard
    
    if callback.from_user.id != ADMIN_ID:
        await callback.answer("❌ Faqat admin!")
        return
    
    await callback.message.delete()
    await callback.message.answer("👨‍💻 Admin Panel", reply_markup=get_admin_keyboard())
    await callback.answer()        

# Botni ishga tushirish
async def main():
    # Keep alive serverini ishga tushirish
    keep_alive.start_keep_alive()
    
    # Bot username'ini olish
    await initialize_bot()
    
    logger.info(f"Bot ishga tushdi... Username: {BOT_USERNAME}")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())