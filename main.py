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

# Yangi token va admin ID raqamlari
BOT_TOKEN = "8895093853:AAEUDuEahHHbDGABEKFKQ3q_f2NPZ_3YLag"
ADMIN_IDS = [728027531, 8489027633]

# Mas'ul shaxslarning Telegram ID raqamlari
DIRECTOR_ID = 8489027633   # Maktab direktori ID raqami
PSYCHOLOGIST_ID = 8489027633  # Psixolog ID raqamini shu yerga qo'ying
OIBDO_ID = 8489027633  # O'IBDO' ID raqamini shu yerga qo'ying
MMIBDO_ID = 8489027633  # MMIBDO' ID raqamini shu yerga qo'ying
ADVISOR_ID = 8489027633  # Maslahatchi ID raqamini shu yerga qo'ying

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
GROUP_IDS = set()


# State (Holatlar)
class AdminStates(StatesGroup):
  waiting_for_contest_name = State()
  waiting_for_announcement = State()
  waiting_for_rating = State()


class StudentStates(StatesGroup):
  choosing_recipient = State()
  waiting_for_message = State()


# Bot guruhga qo'shilganda ID'sini saqlash
@dp.my_chat_member()
async def on_bot_chat_member(event: types.ChatMemberUpdated):
  chat = event.chat
  if chat.type in ["group", "supergroup"]:
    if event.new_chat_member.status in ["member", "administrator"]:
      GROUP_IDS.add(chat.id)
    elif event.new_chat_member.status in ["left", "kicked"]:
      if chat.id in GROUP_IDS:
        GROUP_IDS.remove(chat.id)


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


# Reyting
@dp.message(F.text == "📊 Reyting")
@dp.message(Command("reyting"))
async def show_rating(message: types.Message):
  await message.answer(CURRENT_RATING, parse_mode="HTML")


# Tanlov qo'shish
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
      f"✅ Tanlov muvaffaqiyatli saqlandi:\n\n<b>{message.text}</b>",
      parse_mode="HTML",
  )
  await state.clear()


# Reyting qo'shish
@dp.message(F.text == "📊 Reyting qo'shish")
async def start_add_rating(message: types.Message, state: FSMContext):
  if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
    return
  await message.answer(
      "Yangi reyting ma'lumotlarini yuboring:\n(Masalan:\n1. 11-A sinf -"
      " 180 ball)"
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


# E'lon yuborish (Barcha guruhlarga)
@dp.message(F.text == "📢 E'lon yuborish")
@dp.message(Command("elon"))
async def start_announcement(message: types.Message, state: FSMContext):
  if ADMIN_IDS and message.from_user.id not in ADMIN_IDS:
    return
  await message.answer(
      "Barcha guruhlarga yubormoqchi bo'lgan e'loningiz matnini kiriting:"
  )
  await state.set_state(AdminStates.waiting_for_announcement)


@dp.message(AdminStates.waiting_for_announcement)
async def send_announcement_to_groups(message: types.Message, state: FSMContext):
  announcement_text = message.text

  if not GROUP_IDS:
    await message.answer(
        "⚠️ Hozircha bot hech qanday guruhga qo'shilmagan. Avval botni"
        " guruhga qo'shing va admin qiling!"
    )
  else:
    success_count = 0
    for chat_id in GROUP_IDS:
      try:
        await bot.send_message(
            chat_id,
            f"📢 <b>Maktab e'loni:</b>\n\n{announcement_text}",
            parse_mode="HTML",
        )
        success_count += 1
      except Exception as e:
        logging.error(f"Xatolik: {e}")

    await message.answer(
        f"✅ E'lon {success_count} ta guruhga muvaffaqiyatli yuborildi!",
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


@dp.callback_query(F.data.startswith("to_"))
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
      f"<b>{target_name}</b>ga yubormoqchi bo'lgan murojaatingiz matnini yozib"
      " qoldiring:"
  )
  await state.set_state(StudentStates.waiting_for_message)


@dp.message(StudentStates.waiting_for_message)
async def send_feedback_to_recipient(message: types.Message, state: FSMContext):
  data = await state.get_data()
  target_name = data.get("target", "Admin")
  target_id = data.get("target_id")

  if target_id and target_id != 000000000:
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
        "⚠️ Bu lavozim uchun hali Telegram ID kiritilmagan. Iltimos,"
        " adminlar bilan bog'laning."
    )
    await state.clear()
    return

  await message.answer(
      "Murojaatingiz muvaffaqiyatli yuborildi! Rahmat.", parse_mode="HTML"
  )
  await state.clear()


# Veb-server
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