#!/usr/bin/env python3
import os
import sys

print("=" * 50)
print("🚀 ТЕСТОВЫЙ ЗАПУСК")
print("=" * 50)

# Проверяем переменные
print("1. Проверка переменных окружения:")
api_id = os.getenv('API_ID', 'НЕ ЗАДАН')
api_hash = os.getenv('API_HASH', 'НЕ ЗАДАН')
bot_token = os.getenv('BOT_TOKEN', 'НЕ ЗАДАН')
port = os.getenv('PORT', 'НЕ ЗАДАН')

print(f"   API_ID: {api_id}")
print(f"   API_HASH: {api_hash[:5] if api_hash != 'НЕ ЗАДАН' else 'НЕ ЗАДАН'}...")
print(f"   BOT_TOKEN: {bot_token[:5] if bot_token != 'НЕ ЗАДАН' else 'НЕ ЗАДАН'}...")
print(f"   PORT: {port}")
print("=" * 50)

# Пытаемся импортировать библиотеки
print("2. Проверка импорта библиотек:")
try:
    import telethon
    print("   ✅ telethon установлен")
except Exception as e:
    print(f"   ❌ telethon НЕ установлен: {e}")

try:
    import requests
    print("   ✅ requests установлен")
except Exception as e:
    print(f"   ❌ requests НЕ установлен: {e}")

try:
    import aiohttp
    print("   ✅ aiohttp установлен")
except Exception as e:
    print(f"   ❌ aiohttp НЕ установлен: {e}")

print("=" * 50)
print("✅ ТЕСТ ПРОЙДЕН! Если ты это видишь, код работает.")
print("=" * 50)
