import os
from final_bot import app as flask_app
import logging
import threading
import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    flask_app.run(host='0.0.0.0', port=port, debug=False)

async def run_telethon_services():
    """Запускаем только Telethon сервисы"""
    logger.info("🔍 Запуск Telethon мониторинга...")
    try:
        import advanced_monitor
        await advanced_monitor.main()
    except Exception as e:
        logger.error(f"❌ Ошибка мониторинга: {e}")

def start_telethon():
    asyncio.run(run_telethon_services())

if __name__ == '__main__':
    logger.info("🎯 Запуск Telethon + Flask (без polling)...")
    
    # Запускаем Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем Telethon
    start_telethon()
