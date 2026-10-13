import asyncio
import logging
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

# Bot va Admin ID
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
ADMIN_IDS = [728027531,8489027633]  # Bu yerga o'zingizning Telegram ID ingizni yozing

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


# State (Holatlar)
class AdminStates(StatesGroup):
    waiting_for_contest_name = State()
    waiting_for_announcement = State()


class StudentStates(StatesGroup):
    choosing_recipient = State()
    waiting_for_message = State()


# 1. ADMIN: Tanlov qo'shish
@dp.message(Command("yangi_tanlov"))
async def start_add_contest(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Yangi tanlov nomini va shartlarini kiriting:")
    await state.set_state(AdminStates.waiting_for_contest_name)


@dp.message(AdminStates.waiting_for_contest_name)
async def process_contest(message: types.Message, state: FSMContext):
    # Bu yerda bazaga saqlash kodi bo'ladi
    await message.answer(
        f"Tanlov saqlandi: <b>{message.text}</b>", parse_mode="HTML"
    )
    await state.clear()


# 2. REYTING TIZIMI
@dp.message(Command("reyting"))
async def show_rating(message: types.Message):
    rating_text = (
        "🏆 <b>Maktab reytingi:</b>\n\n"
        "1. 11-A sinf - 150 ball\n"
        "2. 9-B sinf - 120 ball\n"
        "3. 10-A sinf - 95 ball"
    )
    await message.answer(rating_text, parse_mode="HTML")


# 3. ADMIN: Sinflarga e'lon yuborish
@dp.message(Command("elon"))
async def start_announcement(message: types.Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Yubormoqchi bo'lgan e'loningiz matnini kiriting:")
    await state.set_state(AdminStates.waiting_for_announcement)


@dp.message(AdminStates.waiting_for_announcement)
async def choose_class_for_announcement(
    message: types.Message, state: FSMContext
):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="9-sinflar", callback_data="send_9"
                ),
                InlineKeyboardButton(
                    text="10-sinflar", callback_data="send_10"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="11-sinflar", callback_data="send_11"
                ),
                InlineKeyboardButton(
                    text="Barcha sinflar", callback_data="send_all"
                ),
            ],
        ]
    )
    await message.answer(
        "E'lonni qaysi sinflarga yuborasiz?", reply_markup=keyboard
    )
    await state.clear()


# 4. O'QUVCHI: Murojaat yoki Taklif yuborish
@dp.message(Command("murojaat"))
async def start_feedback(message: types.Message, state: FSMContext):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Maktab direktori", callback_data="to_director"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Sinf rahbari", callback_data="to_teacher"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Psixolog", callback_data="to_psychologist"
                )
            ],
        ]
    )
    await message.answer(
        "Murojaatingizni kimga yubormoqchisiz?", reply_markup=keyboard
    )
    await state.set_state(StudentStates.choosing_recipient)


@dp.callback_query(F.data.startswith("to_"))
async def process_recipient(callback: types.CallbackQuery, state: FSMContext):
    recipient_map = {
        "to_director": "Maktab direktori",
        "to_teacher": "Sinf rahbari",
        "to_psychologist": "Psixolog",
    }
    target = recipient_map.get(callback.data, "Admin")
    await state.update_data(target=target)

    await callback.message.edit_text(
        f"<b>{target}</b>ga yubormoqchi bo'lgan murojaatingiz matnini yozib qoldiring:"
    )
    await state.set_state(StudentStates.waiting_for_message)


@dp.message(StudentStates.waiting_for_message)
async def send_feedback_to_admin(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target = data.get("target", "Admin")

    # Murojaatni adminga forwarding/yuborish
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"📩 <b>Yangi murojaat!</b>\n"
            f"<b>Kimga:</b> {target}\n"
            f"<b>Kimdan:</b> {message.from_user.full_name} (@{message.from_user.username})\n\n"
            f"<b>Matn:</b> {message.text}",
            parse_mode="HTML",
        )

    await message.answer(
        "Murojaatingiz muvaffaqiyatli yuborildi! Rahmat.", parse_mode="HTML"
    )
    await state.clear()