#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import asyncio
import socket
import re
import os
import sys
import requests
from datetime import datetime
from telethon import TelegramClient, events

# ======================================================
#  КОНФИГУРАЦИЯ С ПРОВЕРКОЙ
# ======================================================

try:
    API_ID = int(os.getenv('API_ID', 0))
    if API_ID == 0:
        print("❌ ОШИБКА: API_ID не задан или равен 0!")
        sys.exit(1)
    
    API_HASH = os.getenv('API_HASH', '')
    if not API_HASH or len(API_HASH) < 32:
        print(f"❌ ОШИБКА: API_HASH не задан или слишком короткий! Длина: {len(API_HASH)}")
        sys.exit(1)
    
    BOT_TOKEN = os.getenv('BOT_TOKEN', '')
    if not BOT_TOKEN or ':' not in BOT_TOKEN:
        print("❌ ОШИБКА: BOT_TOKEN не задан или неправильного формата!")
        sys.exit(1)
    
    PROXY_PORT = int(os.getenv('PORT', 7777))
    
    print("✅ Все переменные окружения загружены:")
    print(f"   API_ID: {API_ID}")
    print(f"   API_HASH: {API_HASH[:5]}... (скрыто)")
    print(f"   BOT_TOKEN: {BOT_TOKEN[:5]}... (скрыто)")
    print(f"   PORT: {PROXY_PORT}")
    
except Exception as e:
    print(f"❌ ОШИБКА загрузки переменных: {e}")
    sys.exit(1)

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

print("🔄 Подключение к Telegram...")

try:
    bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    print("✅ Подключение к Telegram успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения к Telegram: {e}")
    sys.exit(1)

# ... остальной код (команды /start, /log и т.д. - без изменений)
