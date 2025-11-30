import os
import logging
import asyncio
import threading
from flask import Flask

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем Flask app здесь
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

def run_flask():
    """Запуск Flask сервера"""
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram_bot():
    """Запуск Telegram бота"""
    try:
        # Импортируем здесь чтобы избежать circular imports
        from telegram.ext import Application, CommandHandler, CallbackQueryHandler
        
        # Импортируем из final_bot
        import final_bot
        
        app_bot = Application.builder().token(final_bot.BOT_TOKEN).build()
        app_bot.add_handler(CommandHandler("start", final_bot.start_command))
        app_bot.add_handler(CallbackQueryHandler(final_bot.button_handler))
        
        logger.info("🤖 Telegram бот запускается...")
        app_bot.run_polling(drop_pending_updates=True, close_loop=False)
        
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

async def run_telethon_monitor():
    """Запуск Telethon мониторинга"""
    try:
        import advanced_monitor
        await advanced_monitor.main()
    except Exception as e:
        logger.error(f"❌ Ошибка мониторинга: {e}")

def start_telethon():
    """Запуск Telethon"""
    asyncio.run(run_telethon_monitor())

if __name__ == '__main__':
    logger.info("🎯 Запуск всей системы...")
    
    # Запускаем Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask запущен")
    
    # Запускаем Telethon мониторинг
    telethon_thread = threading.Thread(target=start_telethon, daemon=True)
    telethon_thread.start()
    logger.info("✅ Telethon мониторинг запущен")
    
    # Запускаем Telegram бота в ОСНОВНОМ потоке
    logger.info("✅ Запуск Telegram бота...")
    run_telegram_bot()
