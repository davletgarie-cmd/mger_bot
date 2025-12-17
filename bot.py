from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
import json
import os

TOKEN = "ТВОЙ_ТОКЕН_ИЗ_BOTFATHER"
ADMIN_ID = 123456789  # ТВОЙ Telegram ID

bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# База данных активистов
DB_FILE = "activists.json"

def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

activists_db = load_db()

class Registration(StatesGroup):
    fio = State()
    birthday = State()
    phone = State()
    photo = State()
    branch = State()

class AdminView(StatesGroup):
    select_branch = State()
    select_number = State()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Регистрация", "👮 Руководитель")
    await message.reply("👋 Добро пожаловать в МГЕР Оренбург!", reply_markup=markup)

@dp.message_handler(text="👮 Руководитель")
async def admin_menu(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("❌ Доступ только для руководителя!")
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📊 Просмотр активистов", "📈 Статистика")
    markup.add("🔙 Главное меню")
    await message.reply("👮 Меню руководителя:", reply_markup=markup)

@dp.message_handler(text="📊 Просмотр активистов")
async def admin_view_start(message: types.Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return
    
    await AdminView.select_branch.set()
    branches = sorted(set([a['branch'] for a in activists_db]))
    if not branches:
        await message.reply("📭 Пока нет зарегистрированных активистов")
        await state.finish()
        return
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for branch in branches:
        markup.add(f"📋 {branch}")
    markup.add("🔙 Назад")
    
    await message.reply("Выберите первичку:", reply_markup=markup)

@dp.message_handler(state=AdminView.select_branch, lambda m: m.text.startswith("📋 "))
async def select_branch(message: types.Message, state: FSMContext):
    branch = message.text[3:]  # Убираем "📋 "
    branch_activists = [a for a in activists_db if a['branch'] == branch]
    
    if not branch_activists:
        await message.reply("В этой первичке пока нет активистов")
        await state.finish()
        return
    
    await state.update_data(branch=branch, activists=branch_activists)
    await AdminView.next()
    
    text = f"📋 Активисты {branch} ({len(branch_activists)}):\n\n"
    for i, activist in enumerate(branch_activists, 1):
        text += f"{i}. {activist['fio']}\n"
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("🔙 Назад")
    
    await message.reply(text, reply_markup=markup)
    await message.reply("Введите номер активиста для просмотра профиля:")

@dp.message_handler(state=AdminView.select_number)
async def show_activist_profile(message: types.Message, state: FSMContext):
    data = await state.get_data()
    activists = data['activists']
    
    try:
        num = int(message.text) - 1
        if 0 <= num < len(activists):
            activist = activists[num]
            profile = f"👤 {activist['fio']}\n"
            profile += f"📅 {activist['birthday']}\n"
            profile += f"📱 {activist['phone']}\n"
            profile += f"🏢 {activist['branch']}"
            
            await bot.send_photo(ADMIN_ID, activist['photo'], caption=profile)
            await message.reply("✅ Профиль отправлен в личку")
        else:
            await message.reply("❌ Неверный номер")
    except ValueError:
        await message.reply("❌ Введите число")
    
    await state.finish()

@dp.message_handler(text=["🔙 Главное меню", "🔙 Назад"])
async def back_to_main(message: types.Message, state: FSMContext):
    if state:
        await state.finish()
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Регистрация", "👮 Руководитель")
    await message.reply("🏠 Главное меню:", reply_markup=markup)

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
        "🏭 ОАТК": "ОАТК", "🏭 ОАК": "ОАК", "👨‍🎓 МГЮА": "МГЮА",
        "🏭 ГТТ": "ГТТ", "🏭 Гидропресс": "Гидропресс", "🏛️ ОГПУ": "ОГПУ",
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
    activist = {
        'fio': data['fio'],
        'birthday': data['birthday'],
        'phone': data['phone'],
        'photo': data['photo'],
        'branch': data['branch'],
        'user_id': message.from_user.id,
        'username': message.from_user.username or "Нет"
    }
    
    # Сохраняем в БД
    activists_db.append(activist)
    save_db(activists_db)
    
    # Отправляем уведомление
    summary = f"✅ НОВАЯ РЕГИСТРАЦИЯ\n\n👤 {data['fio']}\n📅 {data['birthday']}\n📱 {data['phone']}\n🏢 {data['branch']}"
    await bot.send_photo(ADMIN_ID, data['photo'], caption=summary)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("📝 Регистрация", "👮 Руководитель")
    
    await state.finish()
    await message.reply("✅ Регистрация завершена!\nДанные сохранены.", reply_markup=markup)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
