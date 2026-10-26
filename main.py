import asyncio
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

# Token to'g'ridan-to'g'ri kiritildi
BOT_TOKEN = "8895093853:AAEUDuEahHHbDGABEKFKQ3q_f2NPZ_3YLag"
ADMIN_IDS = [728027531, 8489027633]

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Saqlanuvchi ma'lumotlar uchun o'zgaruvchilar
CURRENT_RATING = (
    "🏆 <b>Maktab reytingi:</b>\n\n"
    "1. 11-A sinf - 150 ball\n"
    "2. 9-B sinf - 120 ball\n"
    "3. 10-A sinf - 95 ball"
)
ACTIVE_CONTESTS = "Hozircha faol tanlovlar mavjud emas."


# State (Holatlar)
class AdminStates(StatesGroup):
  waiting_for_contest_name = State()
  waiting_for_announcement = State()
  waiting_for_rating = State()


class StudentStates(StatesGroup):
  choosing_recipient = State()
  waiting_for_message = State()


# Admin uchun pastki tugmalar (Reply keyboard)
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
        "Assalomu alaykum! Maktab boshqaruv botiga xush kelibsiz. Kerakli"
        " bo'limni tanlang:",
        reply_markup=get_user_keyboard(),
    )


# Faol tanlovlar
@dp.message(F.text == "🏆 Faol tanlovlar")
async def show_active_contests(message: types.Message):
  await message.answer(
      f"🎯 <b>Faol tanlovlar:</b>\n\n{ACTIVE_CONTESTS}", parse_mode="HTML"
  )


# Reytingni ko'rsatish
@dp.message(F.text == "📊 Reyting")
@dp.message(Command("reyting"))
async def show_rating(message: types.Message):
  await message.answer(CURRENT_RATING, parse_mode="HTML")


# 1. ADMIN: Tanlov qo'shish
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
      f"✅ Tanlov muvaffaqiyatli saqlandi va yangilandi:\n\n<b>{message.text}</b>",
      parse_mode="HTML",
  )
  await state.clear()


# 2. ADMIN: Reyting qo'shish
@dp.message(F.text == "📊 Reyting qo'shish")
async def start_add_rating(message: types.Message, state: FSMContext):
  if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
    return
  await message.answer(
      "Yangi reyting ma'lumotlarini yuboring:\n(Masalan:\n1. 11-A sinf -"
      " 180 ball\n2. 10-B sinf - 150 ball)"
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


# 3. ADMIN: Sinflarga e'lon yuborish
@dp.message(F.text == "📢 E'lon yuborish")
@dp.message(Command("elon"))
async def start_announcement(message: types.Message, state: FSMContext):
  if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
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
              InlineKeyboardButton(text="9-sinflar", callback_data="send_9"),
              InlineKeyboardButton(text="10-sinflar", callback_data="send_10"),
          ],
          [
              InlineKeyboardButton(text="11-sinflar", callback_data="send_11"),
              InlineKeyboardButton(text="Barcha sinflar", callback_data="send_all"),
          ],
      ]
  )
  await message.answer(
      "E'lonni qaysi sinflarga yuborasiz?", reply_markup=keyboard
  )
  await state.clear()


# 4. Murojaat yoki Taklif yuborish
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
          [InlineKeyboardButton(text="Sinf rahbari", callback_data="to_teacher")],
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
      f"<b>{target}</b>ga yubormoqchi bo'lgan murojaatingiz matnini yozib"
      " qoldiring:"
  )
  await state.set_state(StudentStates.waiting_for_message)


@dp.message(StudentStates.waiting_for_message)
async def send_feedback_to_admin(message: types.Message, state: FSMContext):
  data = await state.get_data()
  target = data.get("target", "Admin")

  for admin_id in ADMIN_IDS:
    try:
      await bot.send_message(
          admin_id,
          f"📩 <b>Yangi murojaat!</b>\n"
          f"<b>Kimga:</b> {target}\n"
          f"<b>Kimdan:</b> {message.from_user.full_name} (@{message.from_user.username})\n\n"
          f"<b>Matn:</b> {message.text}",
          parse_mode="HTML",
      )
    except Exception as e:
      logging.error(f"Xabar yuborishda xatolik: {e}")

  await message.answer(
      "Murojaatingiz muvaffaqiyatli yuborildi! Rahmat.", parse_mode="HTML"
  )
  await state.clear()


# Render uchun veb-server
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
  await dp.start_polling(bot)


if __name__ == "__main__":
  asyncio.run(main())