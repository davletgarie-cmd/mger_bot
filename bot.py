from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

TOKEN = "8440568995:AAHc6d37OwVDv8WHPzQQVoZxl07ctrWCr9g"  # Замени на свой
ADMIN_ID = 1625411174  # ТВОЙ Telegram ID от @userinfobot

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
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Регистрация", "👮 Руководитель")
    await message.reply("👋 Добро пожаловать в МГЕР Оренбург!", reply_markup=markup)

@dp.message_handler(text="👮 Руководитель")
async def admin_menu(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("📊 Активисты ОАТК", "📊 Активисты ОАК")
        markup.add("📊 Активисты МГЮА", "🔙 Главное меню")
        await message.reply("👮 Меню руководителя:", reply_markup=markup)
    else:
        await message.reply("❌ Доступ только для руководителя!")

@dp.message_handler(text="📝 Регистрация")
async def reg_start(message: types.Message, state: FSMContext):
    await Registration.fio.set()
    await message.reply("1️⃣ Введите ФИО:")

@dp.message_handler(state=Registration.fio)
async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    await Registration.next()
    await message.reply("2️⃣ Дата рождения (ДД.ММ.ГГГГ):")

@dp.message_handler(state=Registration.birthday)
async def process_birthday(message: types.Message, state: FSMContext):
    await state.update_data(birthday=message.text)
    await Registration.next()
    await message.reply("3️⃣ Номер телефона (+7XXXXXXXXXX):")

@dp.message_handler(state=Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await Registration.next()
    await message.reply("4️⃣ Отправьте фото профиля")

@dp.message_handler(content_types=['photo'], state=Registration.photo)
async def process_photo(message: types.Message, state: FSMContext):
    await state.update_data(photo=message.photo[-1].file_id)
    await Registration.next()
    
    # Кнопки первичек
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🏭 ОАТК", "🏭 ОАК")
    markup.add("👨‍🎓 МГЮА", "🏭 ГТТ")
    markup.add("🏭 Гидропресс", "🏛️ ОГПУ")
    markup.add("❌ Внепервичные", "✍️ Другое")
    
    await message.reply("5️⃣ Выберите первичное отделение:", reply_markup=markup)

@dp.message_handler(state=Registration.branch, lambda message: message.text in [
    "🏭 ОАТК", "🏭 ОАК", "👨‍🎓 МГЮА", "🏭 ГТТ", 
    "🏭 Гидропресс", "🏛️ ОГПУ", "❌ Внепервичные"
])
async def process_branch_preset(message: types.Message, state: FSMContext):
    branch_map = {
        "🏭 ОАТК": "ОАТК",
        "🏭 ОАК": "ОАК", 
        "👨‍🎓 МГЮА": "МГЮА",
        "🏭 ГТТ": "ГТТ",
        "🏭 Гидропресс": "Гидропресс",
        "🏛️ ОГПУ": "ОГПУ",
        "❌ Внепервичные": "Внепервичные"
    }
    
    await state.update_data(branch=branch_map[message.text])
    await finish_registration(message, state)

@dp.message_handler(state=Registration.branch, text="✍️ Другое")
async def process_branch_custom(message: types.Message, state: FSMContext):
    await message.reply("✍️ Введите название вашей первички:")

@dp.message_handler(state=Registration.branch)
async def process_branch_text(message: types.Message, state: FSMContext):
    await state.update_data(branch=message.text)
    await finish_registration(message, state)

async def finish_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    
    summary = f"✅ НОВАЯ РЕГИСТРАЦИЯ\n\n"
    summary += f"👤 ФИО: {data['fio']}\n"
    summary += f"📅 Дата рождения: {data['birthday']}\n"
    summary += f"📱 Телефон: {data['phone']}\n"
    summary += f"🏢 Первичка: {data['branch']}"
    
    # Отправляем руководителю с фото
    await bot.send_photo(ADMIN_ID, data['photo'], caption=summary)
    
    # Возвращаем главное меню
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Регистрация", "👮 Руководитель")
    
    await state.finish()
    await message.reply("✅ Регистрация завершена!\nДанные отправлены руководителю.", reply_markup=markup)

@dp.message_handler(text="🔙 Главное меню")
async def back_to_main(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Регистрация", "👮 Руководитель")
    await message.reply("🏠 Главное меню:", reply_markup=markup)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
