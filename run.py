import threading
import subprocess
import sys
import os
from final_bot import app as flask_app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_flask():
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🚀 Запуск Flask на порту {port}")
    flask_app.run(host='0.0.0.0', port=port, debug=False)

def run_bot():
    logger.info("🤖 Запуск Telegram бота...")
    try:
        from final_bot import run_bot as start_bot
        start_bot()
    except Exception as e:
        logger.error(f"❌ Ошибка запуска бота: {e}")

def run_monitor():
    logger.info("🔍 Запуск мониторинга...")
    try:
        subprocess.run([sys.executable, "advanced_monitor.py"], check=True)
    except Exception as e:
        logger.error(f"❌ Ошибка запуска мониторинга: {e}")

if __name__ == '__main__':
    logger.info("🎯 Старт всех сервисов...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    run_monitor()
