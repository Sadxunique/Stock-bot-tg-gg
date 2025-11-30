import os
import logging
import threading
import asyncio

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_flask():
    """Запуск Flask сервера для Render"""
    from final_bot import app
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    app.run(host='0.0.0.0', port=port, debug=False)

def run_telegram_bot():
    """Запуск основного Telegram бота"""
    from final_bot import run_bot
    run_bot()

async def run_telethon_monitor():
    """Запуск Telethon мониторинга"""
    try:
        import advanced_monitor
        await advanced_monitor.main()
    except Exception as e:
        logger.error(f"❌ Ошибка мониторинга: {e}")

def start_telethon():
    """Запуск Telethon в отдельном потоке"""
    asyncio.run(run_telethon_monitor())

if __name__ == '__main__':
    logger.info("🎯 Запуск всей системы: Bot + Monitor + Flask...")
    
    # Запускаем Flask (для Render health checks)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("✅ Flask запущен")
    
    # Запускаем основного Telegram бота
    bot_thread = threading.Thread(target=run_telegram_bot, daemon=True)
    bot_thread.start()
    logger.info("✅ Telegram бот запущен")
    
    # Запускаем Telethon мониторинг
    telethon_thread = threading.Thread(target=start_telethon, daemon=True)
    telethon_thread.start()
    logger.info("✅ Telethon мониторинг запущен")
    
    # Держим все потоки активными
    try:
        while True:
            pass
    except KeyboardInterrupt:
        logger.info("🛑 Остановка системы...")
