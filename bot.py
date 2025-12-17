from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import os

TOKEN = "8440568995:AAHc6d37OwVDv8WHPzQQVoZxl07ctrWCr9g"  # ваш токен
ADMIN_ID = 1625411174  # ваш Telegram ID

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# Состояния регистрации (без фото)
class Registration(StatesGroup):
    name = State()
    birthdate = State()
    phone = State()
    branch = State()

# Загрузка/сохранение данных
DATA_FILE = 'activists.json'
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

activists = load_data()

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = activists.get(str(user_id), {})
    
    # Админ-проверка (авто-админ меню)
    if user_id == ADMIN_ID:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👥 Просмотр активистов", "📊 Статистика", "🔄 Обновить")
        await message.reply("👋 Данил Русланович! Админ-панель:", reply_markup=markup)
        return
    
    # Проверка заполненного профиля
    if user_data.get('name'):  # профиль заполнен
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add("👤 Мой профиль", "📝 Обновить данные", "ℹ️ Помощь")
        await message.reply("✅ Добро пожаловать обратно!\nВыберите действие:", reply_markup=markup)
    else:  # незаполнен → регистрация
        await Registration.name.set()
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        markup.add("❌ Отмена")
        await message.reply("📝 Начнем регистрацию активиста МГЕР Оренбург.\n\nВведите ФИО:", reply_markup=markup)

@dp.message_handler(state=Registration.name)
async def process_name(message: types.Message, state: FSMContext):
    if message.text == "❌ Отмена":
        await state.finish()
        await message.reply("❌ Регистрация отменена.")
        return
    await state.update_data(name=message.text)
    await Registration.birthdate.set()
    await message.reply("📅 Введите дату рождения (ДД.ММ.ГГГГ):")

@dp.message_handler(state=Registration.birthdate)
async def process_birthdate(message: types.Message, state: FSMContext):
    await state.update_data(birthdate=message.text)
    await Registration.phone.set()
    await message.reply("📱 Введите номер телефона:")

@dp.message_handler(state=Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await Registration.branch.set()
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    branches = ["1. Центральное", "2. Акташское", "3. ГТТ", "4. Гидропресс", "5. ГТТ", "6. Внепервичного отделения", "Другое"]
    for branch in branches:
        markup.add(branch)
    await message.reply("🏢 Выберите первичное отделение:", reply_markup=markup)

@dp.message_handler(state=Registration.branch)
async def finish_registration(message: types.Message, state: FSMContext):
    data = await state.get_data()
    user_id = message.from_user.id
    activists[str(user_id)] = data
    activists[str(user_id)]['branch'] = message.text
    save_data(activists)
    
    # Уведомление админу (текст вместо фото)
    summary = f"🆕 Новый активист:\n👤 {data['name']}\n📅 {data['birthdate']}\n📱 {data['phone']}\n🏢 {message.text}"
    await bot.send_message(ADMIN_ID, summary)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 Мой профиль", "ℹ️ Помощь")
    await state.finish()
    await message.reply("✅ Регистрация завершена! Данные сохранены.", reply_markup=markup)

# Админ-команды (работают только для ADMIN_ID)
@dp.message_handler(lambda message: message.from_user.id == ADMIN_ID and message.text == "👥 Просмотр активистов")
async def admin_view(message: types.Message):
    if not activists:
        await message.reply("📭 Активистов пока нет.")
        return
    summary = "📋 Список активистов:\n\n"
    for uid, data in activists.items():
        summary += f"👤 {data['name']} - {data['branch']}\n"
    await message.reply(summary[:4096])  # лимит Telegram

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
