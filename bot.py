from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = "8440568995:AAHc6d37OwVDv8WHPzQQVoZxl07ctrWCr9g"

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


class Registration(StatesGroup):
    fio = State()
    birthday = State()
    phone = State()
    photo = State()
    branch = State()


@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    await Registration.fio.set()
    await message.answer("Привет! Давай зарегистрируемся.\nНапиши, пожалуйста, своё ФИО полностью.")


@dp.message_handler(state=Registration.fio)
async def reg_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await Registration.next()
    await message.answer("Укажи дату рождения в формате 01.01.2000")


@dp.message_handler(state=Registration.birthday)
async def reg_birthday(message: types.Message, state: FSMContext):
    await state.update_data(birthday=message.text)
    await Registration.next()
    await message.answer("Напиши номер телефона (с +7).")


@dp.message_handler(state=Registration.phone)
async def reg_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await Registration.next()
    await message.answer("Пришли, пожалуйста, своё фото профиля (как фото, не файлом).")


@dp.message_handler(content_types=['photo'], state=Registration.photo)
async def reg_photo(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)

    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add("ОАТК", "ОАК")
    kb.add("МГЮА", "ГТТ")
    kb.add("Гидропресс", "Внепервичного отделения")

    await Registration.next()
    await message.answer("Выбери своё первичное отделение:", reply_markup=kb)


PRIMARY = ["ОАТК", "ОАК", "МГЮА", "ГТТ", "Гидропресс", "Внепервичного отделения"]


@dp.message_handler(lambda m: m.text in PRIMARY, state=Registration.branch)
async def reg_branch(message: types.Message, state: FSMContext):
    await state.update_data(branch=message.text)
    data = await state.get_data()
    await state.finish()

    await message.answer(
        "Регистрация завершена!\n"
        f"ФИО: {data['fio']}\n"
        f"Дата рождения: {data['birthday']}\n"
        f"Телефон: {data['phone']}\n"
        f"Отделение: {data['branch']}",
        reply_markup=types.ReplyKeyboardRemove()
    )


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
