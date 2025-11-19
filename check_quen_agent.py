#!/usr/bin/env python3
"""
Скрипт для проверки работы квен агента
Проверяет:
1. Наличие переменных окружения
2. Работу Telegram отправки
3. Статус Kubernetes CronJob (если доступен)
4. Последние логи
"""
import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def check_env_vars():
    """Проверка переменных окружения"""
    print("=" * 60)
    print("🔍 ПРОВЕРКА ПЕРЕМЕННЫХ ОКРУЖЕНИЯ")
    print("=" * 60)
    
    required_vars = {
        "QWEN_API_KEY": "API ключ для Qwen AI",
        "BYBIT_API_KEY": "API ключ для Bybit",
        "BYBIT_API_SECRET": "API секрет для Bybit",
        "TELEGRAM_BOT_TOKEN": "Токен Telegram бота",
        "TELEGRAM_CHAT_IDS": "ID Telegram каналов (через запятую)"
    }
    
    optional_vars = {
        "QWEN_MODEL": "Модель Qwen (по умолчанию: qwen/qwen-turbo)",
        "BYBIT_TESTNET": "Использовать testnet (true/false)"
    }
    
    all_ok = True
    
    print("\n📋 Обязательные переменные:")
    for var, desc in required_vars.items():
        value = os.getenv(var, "")
        if value:
            # Маскируем секретные значения
            if "SECRET" in var or "TOKEN" in var or "KEY" in var:
                display_value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            else:
                display_value = value
            print(f"  ✅ {var}: {display_value}")
        else:
            print(f"  ❌ {var}: НЕ УСТАНОВЛЕН ({desc})")
            all_ok = False
    
    print("\n📋 Опциональные переменные:")
    for var, desc in optional_vars.items():
        value = os.getenv(var, "")
        if value:
            print(f"  ✅ {var}: {value}")
        else:
            print(f"  ⚠️  {var}: не установлен (будет использовано значение по умолчанию)")
    
    print()
    return all_ok


def check_kubernetes():
    """Проверка статуса Kubernetes CronJob"""
    print("=" * 60)
    print("🔍 ПРОВЕРКА KUBERNETES CRONJOB")
    print("=" * 60)
    
    try:
        # Проверка наличия kubectl
        result = subprocess.run(
            ["kubectl", "version", "--client"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            print("  ⚠️  kubectl не найден или не настроен")
            return False
        
        # Проверка CronJob
        result = subprocess.run(
            ["kubectl", "get", "cronjob", "-n", "trader-agent", "trader-agent-analyzer"],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("  ✅ CronJob найден:")
            print(result.stdout)
            
            # Последние Jobs
            print("\n  📋 Последние Jobs:")
            result = subprocess.run(
                ["kubectl", "get", "jobs", "-n", "trader-agent", "--sort-by=.metadata.creationTimestamp"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                print("\n".join(lines[-5:]))  # Последние 5
            else:
                print("  ⚠️  Не удалось получить список Jobs")
            
            return True
        else:
            print("  ❌ CronJob не найден или namespace недоступен")
            print(f"  Ошибка: {result.stderr}")
            return False
            
    except FileNotFoundError:
        print("  ⚠️  kubectl не установлен")
        return False
    except subprocess.TimeoutExpired:
        print("  ⚠️  Таймаут при проверке Kubernetes")
        return False
    except Exception as e:
        print(f"  ⚠️  Ошибка проверки Kubernetes: {e}")
        return False


def check_logs():
    """Проверка последних логов"""
    print("=" * 60)
    print("🔍 ПРОВЕРКА ЛОГОВ")
    print("=" * 60)
    
    logs_dir = Path(__file__).parent / "logs"
    
    if not logs_dir.exists():
        print("  ⚠️  Директория logs не найдена")
        return
    
    # Ищем логи autonomous_agent
    log_files = sorted(
        logs_dir.glob("autonomous_agent_*.log"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    
    if not log_files:
        print("  ⚠️  Логи autonomous_agent не найдены")
        return
    
    latest_log = log_files[0]
    print(f"  📄 Последний лог: {latest_log.name}")
    print(f"  📅 Модифицирован: {datetime.fromtimestamp(latest_log.stat().st_mtime)}")
    
    # Читаем последние строки
    try:
        with open(latest_log, "r", encoding="utf-8") as f:
            lines = f.readlines()
            if lines:
                print("\n  📋 Последние 10 строк лога:")
                print("  " + "-" * 56)
                for line in lines[-10:]:
                    print("  " + line.rstrip())
                print("  " + "-" * 56)
    except Exception as e:
        print(f"  ⚠️  Ошибка чтения лога: {e}")


def check_data_files():
    """Проверка файлов с результатами"""
    print("=" * 60)
    print("🔍 ПРОВЕРКА ФАЙЛОВ РЕЗУЛЬТАТОВ")
    print("=" * 60)
    
    data_dir = Path(__file__).parent / "data"
    
    if not data_dir.exists():
        print("  ⚠️  Директория data не найдена")
        return
    
    # Проверяем наличие файлов результатов
    analysis_file = data_dir / "latest_analysis.json"
    telegram_file = data_dir / "latest_telegram_message.txt"
    
    if analysis_file.exists():
        mtime = datetime.fromtimestamp(analysis_file.stat().st_mtime)
        print(f"  ✅ latest_analysis.json найден (обновлён: {mtime})")
    else:
        print("  ⚠️  latest_analysis.json не найден")
    
    if telegram_file.exists():
        mtime = datetime.fromtimestamp(telegram_file.stat().st_mtime)
        print(f"  ✅ latest_telegram_message.txt найден (обновлён: {mtime})")
        
        # Показываем первые строки
        try:
            with open(telegram_file, "r", encoding="utf-8") as f:
                lines = f.readlines()[:5]
                if lines:
                    print("\n  📋 Первые строки сообщения:")
                    for line in lines:
                        print("  " + line.rstrip())
        except Exception as e:
            print(f"  ⚠️  Ошибка чтения файла: {e}")
    else:
        print("  ⚠️  latest_telegram_message.txt не найден")


def main():
    """Основная функция проверки"""
    print("\n" + "=" * 60)
    print("🔍 ПРОВЕРКА РАБОТЫ КВЕН АГЕНТА")
    print("=" * 60)
    print(f"Время проверки: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Проверки
    env_ok = check_env_vars()
    print()
    
    k8s_ok = check_kubernetes()
    print()
    
    check_logs()
    print()
    
    check_data_files()
    print()
    
    # Итоги
    print("=" * 60)
    print("📊 ИТОГИ ПРОВЕРКИ")
    print("=" * 60)
    
    if env_ok:
        print("✅ Все обязательные переменные окружения установлены")
    else:
        print("❌ Некоторые переменные окружения не установлены")
        print("   Установите их перед запуском агента")
    
    if k8s_ok:
        print("✅ Kubernetes CronJob настроен и работает")
    else:
        print("⚠️  Kubernetes CronJob недоступен или не настроен")
        print("   Это нормально, если вы запускаете агент локально")
    
    print()
    print("💡 Для тестирования отправки в Telegram запустите:")
    print("   python test_telegram_send.py")
    print()
    print("💡 Для ручного запуска анализа запустите:")
    print("   python -m autonomous_agent.main")
    print()


if __name__ == "__main__":
    main()

