import json
import os
import logging
import hashlib
import time
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# Flask app для веб-сервера
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Бот мониторинга акций работает!"

@app.route('/health')
def health():
    return "✅ OK"

@app.route('/ping')
def ping():
    return "🏓 PONG"

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
BOT_TOKEN = '8453487204:AAGpoHs90KFEyRkO2WPFIVkmWVYKO3Kfnm8'
TARGET_CHAT_ID = -1002591061391
API_ID = 38978588
API_HASH = 'fbeec321d7fc8576d585195d3e2b6eba'
STOCK_BOT = '@gargenstockbot'
MY_USER_ID = 7368702836

# Файлы данных
USERS_FILE = 'users.json'
LAST_MESSAGE_FILE = 'last_message_data.txt'

def load_users():
    """Загрузка пользователей из файла"""
    if os.path.exists(USERS_FILE):
        try:
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_users(users):
    """Сохранение пользователей в файл"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def get_user_settings(user_id):
    """Получение настроек пользователя"""
    users = load_users()
    if str(user_id) not in users:
        users[str(user_id)] = {'auto_notifications': True}
        save_users(users)
    return users[str(user_id)]

def set_auto_notifications(user_id, enabled):
    """Включение/выключение уведомлений"""
    users = load_users()
    users[str(user_id)] = {'auto_notifications': enabled}
    save_users(users)

def get_all_users_with_notifications():
    """Получение всех пользователей с включенными уведомлениями"""
    users = load_users()
    return [int(user_id) for user_id, settings in users.items()
            if settings.get('auto_notifications', True)]

def get_message_hash(text):
    """Создание хеша сообщения для проверки дублирования"""
    return hashlib.md5(text.encode()).hexdigest()

def save_last_message_data(message_hash, timestamp):
    """Сохранение данных последнего сообщения"""
    data = {'hash': message_hash, 'timestamp': timestamp}
    with open(LAST_MESSAGE_FILE, 'w') as f:
        json.dump(data, f)

def get_last_message_data():
    """Получение данных последнего сообщения"""
    if os.path.exists(LAST_MESSAGE_FILE):
        try:
            with open(LAST_MESSAGE_FILE, 'r') as f:
                return json.load(f)
        except:
            return None
    return None

def should_skip_message(current_hash):
    """Проверка нужно ли пропускать сообщение (дублирование)"""
    last_data = get_last_message_data()
    if not last_data:
        return False

    last_hash = last_data.get('hash')
    last_timestamp = last_data.get('timestamp')

    # Пропускаем если тот же хеш и прошло меньше 90 секунд
    if last_hash == current_hash and (time.time() - last_timestamp) < 90:
        logger.info(f"🔄 Пропускаем дублирующее сообщение")
        return True

    return False

def get_main_keyboard():
    """Клавиатура бота"""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📊 СТОК", callback_data='stock')],
        [InlineKeyboardButton("🔔 ВКЛ Уведомления", callback_data='autoon')],
        [InlineKeyboardButton("🔕 ВЫКЛ Уведомления", callback_data='autooff')],
        [InlineKeyboardButton("📊 Статус", callback_data='status')],
        [InlineKeyboardButton("🆘 Поддержка", callback_data='support')]
    ])

async def send_stock_command(user_id):
    """Отправка команды Сток боту"""
    try:
        from telethon import TelegramClient
        client = TelegramClient('command_session', API_ID, API_HASH)
        await client.start()
        
        if await client.is_user_authorized():
            await client.send_message(STOCK_BOT, 'Сток')
            await client.disconnect()
            
            # Логируем кто отправил запрос
            if user_id == MY_USER_ID:
                logger.info("✅ Мой запрос 'СТОК' отправлен")
            else:
                logger.info(f"✅ Запрос 'СТОК' от пользователя {user_id}")
                
            return True
        await client.disconnect()
        return False
    except Exception as e:
        logger.error(f"❌ Ошибка отправки команды Сток: {e}")
        return False

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user_id = update.effective_user.id
    settings = get_user_settings(user_id)
    status = "✅ ВКЛ" if settings['auto_notifications'] else "❌ ВЫКЛ"
    text = f"🤖 **БОТ МОНИТОРИНГА АКЦИЙ**\n\n🔔 Авто-уведомления: {status}\n\n🎯 Используйте кнопки:"
    await update.message.reply_text(text, reply_markup=get_main_keyboard())

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатий кнопок"""
    query = update.callback_query
    user_id = query.from_user.id
    await query.answer()

    try:
        if query.data == 'stock':
            await query.edit_message_text("🔄 Получаю сток...", reply_markup=get_main_keyboard())
            success = await send_stock_command(user_id)
            if success:
                await query.edit_message_text("✅ Запрос отправлен! Ожидайте обновления акций...", reply_markup=get_main_keyboard())
            else:
                await query.edit_message_text("❌ Ошибка отправки запроса. Попробуйте позже.", reply_markup=get_main_keyboard())

        elif query.data == 'autoon':
            set_auto_notifications(user_id, True)
            new_text = "✅ Авто-уведомления ВКЛЮЧЕНЫ!"
            await query.edit_message_text(new_text, reply_markup=get_main_keyboard())

        elif query.data == 'autooff':
            set_auto_notifications(user_id, False)
            new_text = "❌ Авто-уведомления ВЫКЛЮЧЕНЫ!"
            await query.edit_message_text(new_text, reply_markup=get_main_keyboard())

        elif query.data == 'status':
            settings = get_user_settings(user_id)
            status = "✅ ВКЛ" if settings['auto_notifications'] else "❌ ВЫКЛ"
            new_text = f"📊 **СТАТУС**\n\n🔔 Уведомления: {status}"
            await query.edit_message_text(new_text, reply_markup=get_main_keyboard())

        elif query.data == 'support':
            new_text = "🆘 **ПОДДЕРЖКА**\n\n💻 Разработчик: @Sad_unique\n🤖 Бот обратной связи: @SadFeedback_bot"
            await query.edit_message_text(new_text, reply_markup=get_main_keyboard())

    except Exception as e:
        logger.error(f"❌ Ошибка в button_handler: {e}")

async def send_stock_notification(stock_text, message_id, from_user_id=None):
    """Отправка уведомлений о новых акциях"""
    try:
        message_hash = get_message_hash(stock_text)
        current_time = time.time()

        # Проверяем дублирование
        if should_skip_message(message_hash):
            return False

        bot = Bot(BOT_TOKEN)
        notification_text = f"🔄 **Появился новый предмет в стоке** 🔄\n\n{stock_text}"

        # Сохраняем данные сообщения
        save_last_message_data(message_hash, current_time)

        # ОТПРАВЛЯЕМ В КАНАЛ ТОЛЬКО ЕСЛИ ЗАПРОС БЫЛ ОТ МЕНЯ
        if from_user_id == MY_USER_ID:
            try:
                await bot.send_message(TARGET_CHAT_ID, notification_text)
                logger.info("✅ Акции отправлены в канал (мой запрос)")
            except Exception as e:
                logger.error(f"❌ Ошибка отправки в канал: {e}")
        else:
            logger.info(f"🔄 Пропускаем отправку в канал (запрос от пользователя {from_user_id})")

        # ВСЕГДА отправляем уведомления пользователям бота
        users_with_notifications = get_all_users_with_notifications()
        if users_with_notifications:
            logger.info(f"📢 Отправка {len(users_with_notifications)} пользователям...")
            for user_id in users_with_notifications:
                try:
                    await bot.send_message(user_id, notification_text)
                except Exception as e:
                    logger.error(f"❌ Ошибка пользователю {user_id}: {e}")

        return True

    except Exception as e:
        logger.error(f"❌ Ошибка в send_stock_notification: {e}")
        return False

def run_bot():
    """Запуск Telegram бота"""
    try:
        app_bot = Application.builder().token(BOT_TOKEN).build()
        app_bot.add_handler(CommandHandler("start", start_command))
        app_bot.add_handler(CallbackQueryHandler(button_handler))
        
        logger.info("🤖 Telegram бот запускается...")
        app_bot.run_polling(drop_pending_updates=True)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")
