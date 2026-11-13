import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiohttp import web

# Loggingni yoqish
logging.basicConfig(level=logging.INFO)

# Token va admin ID raqamlari
BOT_TOKEN = "9068409172:AAEufPpEtqh39lER4ritx2dNNrp7fzdfuyg"
ADMIN_IDS = [728027531, 8489027633]

# Mas'ul shaxslarning Telegram ID raqamlari
DIRECTOR_ID = 8489027633
PSYCHOLOGIST_ID = 8489027633
OIBDO_ID = 8489027633
MMIBDO_ID = 8489027633
ADVISOR_ID = 8489027633

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar
CURRENT_RATING = (
    "🏆 <b>Maktab reytingi:</b>\n\n"
    "1. 11-A sinf - 150 ball\n"
    "2. 9-B sinf - 120 ball\n"
    "3. 10-A sinf - 95 ball"
)
ACTIVE_CONTESTS = "Hozircha faol tanlovlar mavjud emas."

# --- 19 TA SINF GURUHLARINING ID'LARI ---
SCHOOL_CLASSES = {
    "class_5d": ("5-D sinf", -5464235621),
    "class_5e": ("5-E sinf", -5223524246),
    "class_6d": ("6-D sinf", -5542354727),
    "class_6e": ("6-E sinf", -5365485659),
    "class_7d": ("7-D sinf", -5251764629),
    "class_7e": ("7-E sinf", -5234651636),
    "class_7g": ("7-G sinf", -5183862151),
    "class_7v": ("7-V sinf", -5492840488),
    "class_8d": ("8-D sinf", -5224077025),
    "class_8e": ("8-E sinf", -5598684484),
    "class_9d": ("9-D sinf", -5288612821),
    "class_9e": ("9-E sinf", -5340753966),
    "class_9g": ("9-G sinf", -5219547822),
    "class_10d": ("10-D sinf", -5150476450),
    "class_10e": ("10-E sinf", -5182347375),
    "class_10g": ("10-G sinf", -5377555918),
    "class_11d": ("11-D sinf", -5495400023),
    "class_11e": ("11-E sinf", -5248398629),
    "class_11g": ("11-G sinf", -5370728668),
}


# State (Holatlar)
class AdminStates(StatesGroup):
    waiting_for_contest_name = State()
    choosing_classes_for_announcement = State()
    waiting_for_announcement = State()
    waiting_for_rating = State()


class StudentStates(StatesGroup):
    choosing_recipient = State()
    waiting_for_message = State()


# Admin tugmalari
def get_admin_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏆 Faol tanlovlar"),
                KeyboardButton(text="📊 Reyting"),
            ],
            [
                KeyboardButton(text="➕ Yangi tanlov qo'shish"),
                KeyboardButton(text="📢 E'lon yuborish"),
            ],
            [KeyboardButton(text="📊 Reyting qo'shish")],
            [KeyboardButton(text="✍️ Taklif / Shikoyat yuborish")],
        ],
        resize_keyboard=True,
    )


def get_user_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="🏆 Faol tanlovlar"),
                KeyboardButton(text="📊 Reyting"),
            ],
            [KeyboardButton(text="✍️ Taklif / Shikoyat yuborish")],
        ],
        resize_keyboard=True,
    )


# Start buyrug'i
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if ADMIN_IDS and message.from_user.id in ADMIN_IDS:
        await message.answer(
            "Assalomu alaykum, Hurmatli Admin! Kerakli bo'limni tanlang:",
            reply_markup=get_admin_keyboard(),
        )
    else:
        await message.answer(
            "Assalomu alaykum! Maktab boshqaruv botiga xush kelibsiz. Kerakli bo'limni tanlang:",
            reply_markup=get_user_keyboard(),
        )


# Faol tanlovlar va Reyting
@dp.message(F.text == "🏆 Faol tanlovlar")
async def show_active_contests(message: types.Message):
    await message.answer(
        f"🎯 <b>Faol tanlovlar:</b>\n\n{ACTIVE_CONTESTS}", parse_mode="HTML"
    )


@dp.message(F.text == "📊 Reyting")
@dp.message(Command("reyting"))
async def show_rating(message: types.Message):
    await message.answer(CURRENT_RATING, parse_mode="HTML")


# Tanlov va Reyting qo'shish (Admin)
@dp.message(F.text == "➕ Yangi tanlov qo'shish")
@dp.message(Command("yangi_tanlov"))
async def start_add_contest(message: types.Message, state: FSMContext):
    if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
        return
    await message.answer("Yangi tanlov nomini va shartlarini kiriting:")
    await state.set_state(AdminStates.waiting_for_contest_name)


@dp.message(AdminStates.waiting_for_contest_name)
async def process_contest(message: types.Message, state: FSMContext):
    global ACTIVE_CONTESTS
    ACTIVE_CONTESTS = message.text
    await message.answer(
        f"✅ Tanlangan tanlov muvaffaqiyatli saqlandi:\n\n<b>{message.text}</b>",
        parse_mode="HTML",
    )
    await state.clear()


@dp.message(F.text == "📊 Reyting qo'shish")
async def start_add_rating(message: types.Message, state: FSMContext):
    if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
        return
    await message.answer(
        "Yangi reyting ma'lumotlarini yuboring:\n(Masalan:\n11-A sinf - 180 ball)"
    )
    await state.set_state(AdminStates.waiting_for_rating)


@dp.message(AdminStates.waiting_for_rating)
async def process_new_rating(message: types.Message, state: FSMContext):
    global CURRENT_RATING
    CURRENT_RATING = f"🏆 <b>Maktab reytingi:</b>\n\n{message.text}"
    await message.answer(
        "✅ Reyting muvaffaqiyatli yangilandi!", parse_mode="HTML"
    )
    await state.clear()


# --- BIR NECHTA SINFLARNI TANLAB E'LON YUBORISH ---


def generate_classes_keyboard(selected_classes=None):
    if selected_classes is None:
        selected_classes = []

    keyboard_buttons = []
    row = []

    # Har bir qatorga 2 tadan sinf tugmachasini joylaymiz
    for key, (class_name, _) in SCHOOL_CLASSES.items():
        is_selected = key in selected_classes
        icon = "✅ " if is_selected else ""
        text = f"{icon}{class_name}"

        row.append(InlineKeyboardButton(text=text, callback_data=f"sel_{key}"))
        if len(row) == 2:
            keyboard_buttons.append(row)
            row = []

    if row:
        keyboard_buttons.append(row)

    # Maxsus boshqaruv tugmalari
    keyboard_buttons.append(
        [
            InlineKeyboardButton(text="☑️ Hammasini tanlash", callback_data="sel_all"),
            InlineKeyboardButton(text="❌ Tozalash", callback_data="sel_clear"),
        ]
    )
    keyboard_buttons.append(
        [InlineKeyboardButton(text="🚀 E'lon matnini kiritish", callback_data="sel_done")]
    )

    return InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)


@dp.message(F.text == "📢 E'lon yuborish")
@dp.message(Command("elon"))
async def start_announcement(message: types.Message, state: FSMContext):
    if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
        return

    # Tanlangan sinflar ro'yxatini boshlang'ich holatda bo'sh qilamiz
    await state.update_data(selected_classes=[])

    keyboard = generate_classes_keyboard([])
    await message.answer(
        "📢 E'lon yubormoqchi bo'lgan sinflarni tanlang (ustiga bosib belgilang):\n\n"
        "Tanlab bo'lgach, pastdagi <b>'🚀 E'lon matnini kiritish'</b> tugmasini bosing:",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    await state.set_state(AdminStates.choosing_classes_for_announcement)


@dp.callback_query(
    AdminStates.choosing_classes_for_announcement, F.data.startswith("sel_")
)
async def process_class_selection(
    callback: types.CallbackQuery, state: FSMContext
):
    action = callback.data.replace("sel_", "")
    data = await state.get_data()
    selected = data.get("selected_classes", [])

    if action == "all":
        selected = list(SCHOOL_CLASSES.keys())
    elif action == "clear":
        selected = []
    elif action == "done":
        if not selected:
            await callback.answer(
                "⚠️ Hech qanday sinf tanlanmadi!", show_alert=True
            )
            return
        await callback.message.edit_text(
            f"✅ Tanlangan sinflar soni: {len(selected)} ta.\n\n"
            "Endi yubormoqchi bo'lgan <b>e'lon matnini</b> yuboring:"
        )
        await state.set_state(AdminStates.waiting_for_announcement)
        return
    else:
        # Sinf tugmasi bosilganda (toggle)
        if action in selected:
            selected.remove(action)
        else:
            selected.append(action)

    await state.update_data(selected_classes=selected)

    # Tugmalarni yangilangan holatda qayta chizamiz
    keyboard = generate_classes_keyboard(selected)
    try:
        await callback.message.edit_reply_markup(reply_markup=keyboard)
    except Exception:
        pass
    await callback.answer()


@dp.message(AdminStates.waiting_for_announcement)
async def send_announcement_to_classes(message: types.Message, state: FSMContext):
    data = await state.get_data()
    selected_keys = data.get("selected_classes", [])
    announcement_text = message.text

    if not selected_keys:
        await message.answer("⚠️ Sinf tanlanmagan!")
        await state.clear()
        return

    success_count = 0
    for key in selected_keys:
        if key in SCHOOL_CLASSES:
            c_name, c_id = SCHOOL_CLASSES[key]
            try:
                await bot.send_message(
                    c_id,
                    f"📢 <b>Maktab e'loni ({c_name}):</b>\n\n{announcement_text}",
                    parse_mode="HTML",
                )
                success_count += 1
            except Exception as e:
                logging.error(f"Xatolik {c_name} ga yuborishda: {e}")

    await message.answer(
        f"✅ E'lon muvaffaqiyatli ravishda {success_count} ta sinf guruhiga yuborildi!",
        parse_mode="HTML",
    )
    await state.clear()


# Murojaat yoki Taklif yuborish
@dp.message(F.text == "✍️ Taklif / Shikoyat yuborish")
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
                    text="Psixolog", callback_data="to_psychologist"
                )
            ],
            [InlineKeyboardButton(text="O'IBDO'", callback_data="to_oibdo")],
            [InlineKeyboardButton(text="MMIBDO'", callback_data="to_mmibdo")],
            [
                InlineKeyboardButton(
                    text="Maslahatchi", callback_data="to_advisor"
                )
            ],
        ]
    )
    await message.answer(
        "Murojaatingizni kimga yubormoqchisiz?", reply_markup=keyboard
    )
    await state.set_state(StudentStates.choosing_recipient)


@dp.callback_query(StudentStates.choosing_recipient, F.data.startswith("to_"))
async def process_recipient(callback: types.CallbackQuery, state: FSMContext):
    recipient_map = {
        "to_director": ("Maktab direktori", DIRECTOR_ID),
        "to_psychologist": ("Psixolog", PSYCHOLOGIST_ID),
        "to_oibdo": ("O'IBDO'", OIBDO_ID),
        "to_mmibdo": ("MMIBDO'", MMIBDO_ID),
        "to_advisor": ("Maslahatchi", ADVISOR_ID),
    }

    target_name, target_id = recipient_map.get(
        callback.data, ("Admin", ADMIN_IDS[0])
    )
    await state.update_data(target=target_name, target_id=target_id)

    await callback.message.edit_text(
        f"<b>{target_name}</b>ga yubormoqchi bo'lgan murojaatingiz matnini yozib qoldiring:"
    )
    await state.set_state(StudentStates.waiting_for_message)


@dp.message(StudentStates.waiting_for_message)
async def send_feedback_to_recipient(message: types.Message, state: FSMContext):
    data = await state.get_data()
    target_name = data.get("target", "Admin")
    target_id = data.get("target_id")

    if target_id and target_id != 0:
        try:
            await bot.send_message(
                target_id,
                f"📩 <b>Yangi murojaat!</b>\n"
                f"<b>Kimga:</b> {target_name}\n"
                f"<b>Kimdan:</b> {message.from_user.full_name}\n\n"
                f"<b>Matn:</b> {message.text}",
                parse_mode="HTML",
            )
        except Exception as e:
            logging.error(f"Xatolik: {e}")
    else:
        await message.answer(
            "⚠️ Bu lavozim uchun hali Telegram ID kiritilmagan. Iltimos, adminlar bilan bog'laning."
        )
        await state.clear()
        return

    await message.answer(
        "Murojaatingiz muvaffaqiyatli yuborildi! Rahmat.", parse_mode="HTML"
    )
    await state.clear()


# Veb-server (Render talabi uchun)
async def handle(request):
    return web.Response(text="Bot ishlayapti!")


app = web.Application()
app.router.add_get("/", handle)


async def web_server():
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()


async def main():
    await web_server()
    await bot.delete_webhook(drop_pending_updates=True)
    print("Bot muvaffaqiyatli ishga tushdi!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())