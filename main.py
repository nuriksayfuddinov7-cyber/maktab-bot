import asyncio
import sqlite3
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# 1. Bot tokeningiz:
BOT_TOKEN = "8895093853:AAEZqCDVCWDly9seBbKqBh-SWIR5sMMzw-E"

# 2. Adminlar ID raqamlari:
ADMIN_IDS = [728027531,8489027633]  # O'z ID raqamingizni yozing

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# --- SHIKOYAT UCHUN HOLAT (STATE) ---
class FeedbackState(StatesGroup):
    waiting_for_text = State()

# --- MA'LUMOTLAR BAZASI ---
def init_db():
    conn = sqlite3.connect("school_bot.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            chat_id INTEGER PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --- TUGMALAR ---
def get_main_keyboard():
    kb = [
        [KeyboardButton(text="📢 Faol tanlovlar"), KeyboardButton(text="🏆 Reyting")],
        [KeyboardButton(text="✍️ Taklif / Shikoyat yuborish")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- BUYRUQLAR VA XABARLAR ---

@dp.message(CommandStart())
async def start_handler(message: Message, state: FSMContext):
    await state.clear()
    if message.chat.type == "private":
        await message.answer(
            "Salom! Maktabimizning rasmiy botiga xush kelibsiz.\n\n"
            "Kerakli bo'limni tanlash uchun pastdagi tugmalardan foydalaning:",
            reply_markup=get_main_keyboard()
        )

@dp.my_chat_member()
async def bot_added_to_group(event: types.ChatMemberUpdated):
    if event.new_chat_member.status in ["member", "administrator"]:
        chat_id = event.chat.id
        conn = sqlite3.connect("school_bot.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO groups (chat_id) VALUES (?)", (chat_id,))
        conn.commit()
        conn.close()

@dp.message(F.text == "📢 Faol tanlovlar")
async def show_contests(message: Message):
    await message.answer("🎯 **Maktabdagi faol tanlovlar:**\n\n1. Yilning eng yaxshi sinfi\n2. Matematika fan olimpiadasi")

@dp.message(F.text == "🏆 Reyting")
async def show_rating(message: Message):
    await message.answer("📊 **O'quvchilar reytingi (Maktab valyutasi):**\n\n1. Aliyev Ali — 150 tanga\n2. Karimova Madina — 120 tanga")

# 1-QADAM: O'quvchi tugmani bosganda bot shikoyat yuborishni so'raydi
@dp.message(F.text == "✍️ Taklif / Shikoyat yuborish")
async def feedback_start(message: Message, state: FSMContext):
    await state.set_state(FeedbackState.waiting_for_text)
    await message.answer(
        "Marhamat, o'z taklif yoki shikoyatingizni shu yerga yozib yuboring.\n"
        "U to'g'ridan-to'g'ri maktab ma'muriyatiga (adminlarga) yuboriladi:"
    )

# 2-QADAM: O'quvchi yozgan xabarni tutib olib, adminlarga jo'natish
@dp.message(FeedbackState.waiting_for_text)
async def feedback_receive(message: Message, state: FSMContext):
    text = message.text
    user = message.from_user
    
    # O'quvchi haqida ma'lumot tayyorlash
    user_info = (
        f"📩 **YANGI TAKLIF / SHIKOYAT KELDI!**\n\n"
        f"👤 **Kimdan:** {user.full_name} "
        f"({f'@{user.username}' if user.username else 'username yo\'q'})\n"
        f"🆔 **ID:** {user.id}\n\n"
        f"📝 **Matn:**\n{text}"
    )

    # Barcha adminlarga xabarni yuborish
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text=user_info)
        except Exception:
            pass

    await state.clear()
    await message.answer(
        "Rahmat! Sizning murojaatingiz ma'muriyatga muvaffaqiyatli yuborildi.",
        reply_markup=get_main_keyboard()
    )

@dp.message(Command("elon"))
async def send_announcement(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("Sizda e'lon yuborish huquqi yo'q!")
        return

    text = message.text.replace("/elon", "").strip()
    if not text:
        await message.answer("E'lon matnini buyruqdan keyin yozing.\nMasalan:\n`/elon Ertaga maktabda tadbir bo'lib o'tadi!`")
        return

    conn = sqlite3.connect("school_bot.db")
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM groups")
    groups = cursor.fetchall()
    conn.close()

    count = 0
    for group in groups:
        try:
            await bot.send_message(chat_id=group[0], text=f"📢 **MAKTAB E'LONI:**\n\n{text}")
            count += 1
        except Exception:
            pass

    await message.answer(f"E'lon muvaffaqiyatli {count} ta sinf guruhiga yuborildi!")

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())