
import os
from final_bot import app as flask_app
import logging
import asyncio
import threading

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    flask_app.run(host='0.0.0.0', port=port, debug=False)

async def run_bot_async():
    logger.info("🤖 Запуск Telegram бота...")
    try:
        from final_bot import run_bot
        await run_bot()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

def run_bot():
    asyncio.run(run_bot_async())

if __name__ == '__main__':
    logger.info("🎯 Старт сервисов...")
    
    # Запускаем Flask
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Запускаем бота
    run_bot()
