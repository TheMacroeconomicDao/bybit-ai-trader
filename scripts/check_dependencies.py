#!/usr/bin/env python3
"""Проверка всех зависимостей перед запуском агента"""

import sys
import importlib
from typing import List, Tuple

# Цвета для вывода
RED = '\033[0;31m'
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
BLUE = '\033[0;34m'
NC = '\033[0m'

REQUIRED_PACKAGES = [
    ('mcp', '>=0.9.0'),
    ('pybit', '>=5.6.0'),
    ('pandas', '>=2.1.0'),
    ('numpy', '>=1.24.0'),
    ('aiohttp', '>=3.9.0'),
    ('loguru', '>=0.7.0'),
    ('ta', '>=0.11.0'),
    ('dotenv', None),  # python-dotenv
    ('pydantic', '>=2.5.0'),
    ('ccxt', '>=4.2.0'),
    ('websockets', '>=12.0'),
    ('python_dateutil', None),  # python-dateutil
    ('pytz', '>=2023.3'),
]

# Маппинг имен модулей к именам пакетов
MODULE_TO_PACKAGE = {
    'dotenv': 'python-dotenv',
    'python_dateutil': 'python-dateutil',
}

def check_package(package_name: str, min_version: str = None) -> Tuple[bool, str, str]:
    """Проверка наличия пакета"""
    try:
        # Специальная обработка для некоторых модулей
        import_name = package_name
        if package_name == 'dotenv':
            import_name = 'dotenv'
        elif package_name == 'python_dateutil':
            import_name = 'dateutil'
        else:
            import_name = package_name
        
        module = importlib.import_module(import_name)
        
        if min_version and hasattr(module, '__version__'):
            version = module.__version__
            return True, f"✅ {package_name}: {version}", ""
        else:
            return True, f"✅ {package_name}: installed", ""
    except ImportError:
        package_display = MODULE_TO_PACKAGE.get(package_name, package_name)
        return False, f"❌ {package_name}: NOT INSTALLED", package_display

def main():
    print(f"\n{BLUE}🔍 Проверка зависимостей Autonomous Agent...{NC}\n")
    
    missing = []
    installed = []
    
    for package_info in REQUIRED_PACKAGES:
        if isinstance(package_info, tuple):
            package, min_ver = package_info
        else:
            package, min_ver = package_info, None
        
        success, message, package_name = check_package(package, min_ver)
        
        if success:
            installed.append(message)
            print(f"{GREEN}{message}{NC}")
        else:
            missing.append(package_name)
            print(f"{RED}{message}{NC}")
    
    print(f"\n{'='*50}")
    print(f"{'Результаты проверки':^50}")
    print(f"{'='*50}\n")
    
    print(f"{GREEN}✅ Установлено: {len(installed)}/{len(REQUIRED_PACKAGES)}{NC}")
    
    if missing:
        print(f"{RED}❌ Отсутствует: {len(missing)}{NC}")
        print(f"\n{YELLOW}Установите недостающие пакеты:{NC}")
        print(f"{GREEN}pip install {' '.join(missing)}{NC}")
        print(f"\n{YELLOW}Или установите все из requirements.txt:{NC}")
        print(f"{GREEN}pip install -r requirements.txt{NC}\n")
        sys.exit(1)
    else:
        print(f"\n{GREEN}🎉 Все зависимости установлены!{NC}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()







