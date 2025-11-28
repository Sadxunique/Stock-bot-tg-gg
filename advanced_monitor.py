import asyncio
import logging
from telethon import TelegramClient, events
import sys
import os
import requests

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфиг
API_ID = 38978588
API_HASH = 'fbeec321d7fc8576d585195d3e2b6eba'
STOCK_BOT = '@gargenstockbot'

# Ваш user_id
MY_USER_ID = 7368702836

# Словарь для отслеживания последних запросов
last_requests = {}

async def self_ping_monitor():
    """Самопинг для мониторинга"""
    while True:
        try:
            # Пингуем основной бот если есть URL
            render_url = os.environ.get('RENDER_EXTERNAL_URL')
            if render_url:
                response = requests.get(f"{render_url}/health", timeout=10)
                logger.info(f"🔄 Мониторинг самопинг: {response.status_code}")
            else:
                logger.info("🔄 Мониторинг самопинг: активен")
        except Exception as e:
            logger.error(f"❌ Ошибка самопинга мониторинга: {e}")
        
        await asyncio.sleep(5)

async def handle_stock_update(event):
    try:
        text = event.message.text
        message_id = event.message.id

        logger.info(f"📈 Получены акции от @gargenstockbot! ID: {message_id}")

        # Определяем, кто отправил запрос
        from_user_id = None
        
        # Проверяем, был ли недавно запрос от какого-либо пользователя
        current_time = asyncio.get_event_loop().time()
        for user_id, request_time in last_requests.items():
            if current_time - request_time < 30:  # 30 секунд - окно для определения отправителя
                from_user_id = user_id
                logger.info(f"🔍 Определен отправитель запроса: {user_id} (мой: {user_id == MY_USER_ID})")
                break

        # Если не определили отправителя, считаем что это авто-уведомление
        if from_user_id is None:
            from_user_id = MY_USER_ID  # Авто-уведомления считаем как "мои"
            logger.info("🔍 Авто-уведомление или неопределенный отправитель")

        # Импортируем и запускаем отправку уведомлений
        try:
            sys.path.append(os.getcwd())
            from final_bot import send_stock_notification

            # Запускаем отправку уведомлений с информацией об отправителе
            success = await send_stock_notification(text, message_id, from_user_id)

            if success:
                logger.info("✅ Уведомления отправлены пользователям")
            else:
                logger.info("🔄 Дублирующее сообщение пропущено")

        except Exception as e:
            logger.error(f"❌ Ошибка при отправке уведомлений: {e}")

    except Exception as e:
        logger.error(f"❌ Ошибка в handle_stock_update: {e}")

async def monitor_user_requests():
    """Мониторинг запросов пользователей к @gargenstockbot"""
    try:
        client = TelegramClient('monitor_session', API_ID, API_HASH)
        await client.start()

        @client.on(events.NewMessage(pattern='Сток|сток', chats=STOCK_BOT))
        async def handler(event):
            # Ловим запросы "Сток" от пользователей
            if event.is_private and event.message.out:
                user_id = event.message.sender_id
                last_requests[user_id] = asyncio.get_event_loop().time()
                logger.info(f"📝 Зафиксирован запрос 'СТОК' от пользователя {user_id}")

        await client.run_until_disconnected()
    except Exception as e:
        logger.error(f"❌ Ошибка мониторинга запросов: {e}")

async def main():
    logger.info("🔍 Запуск мониторинга авто-уведомлений...")

    # Запускаем самопинг
    asyncio.create_task(self_ping_monitor())

    # Запускаем мониторинг запросов пользователей в отдельной задаче
    asyncio.create_task(monitor_user_requests())

    # Используем отдельную сессию для мониторинга
    client = TelegramClient('monitor_session', API_ID, API_HASH)

    try:
        await client.start()

        if not await client.is_user_authorized():
            logger.error("❌ Сессия не авторизована! Запустите авторизацию.")
            return

        @client.on(events.NewMessage(chats=STOCK_BOT))
        async def handler(event):
            await handle_stock_update(event)

        logger.info("✅ Мониторинг запущен! Ожидаем авто-уведомления от @gargenstockbot...")
        print("🎯 Мониторинг активен. Ждем авто-уведомления о новых акциях...")

        # Бесконечный цикл
        while True:
            await asyncio.sleep(10)

    except Exception as e:
        logger.error(f"❌ Ошибка мониторинга: {e}")
    finally:
        try:
            await client.disconnect()
        except:
            pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Мониторинг остановлен")
