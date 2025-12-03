"""
Utility functions for interval conversion
Конвертация интервалов между различными форматами
"""

from typing import Union


def convert_interval_to_bybit_format(interval: str) -> str:
    """
    Конвертирует интервал из человекочитаемого формата в формат Bybit API
    
    Args:
        interval: Интервал в формате "1h", "4h", "1d" и т.д.
        
    Returns:
        Интервал в формате Bybit: "1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"
        
    Examples:
        >>> convert_interval_to_bybit_format("1h")
        '60'
        >>> convert_interval_to_bybit_format("4h")
        '240'
        >>> convert_interval_to_bybit_format("1d")
        'D'
        >>> convert_interval_to_bybit_format("15m")
        '15'
    """
    # Если уже в правильном формате, возвращаем как есть
    if interval in ["1", "3", "5", "15", "30", "60", "120", "240", "360", "720", "D", "W", "M"]:
        return interval
    
    # Убираем пробелы и приводим к нижнему регистру
    interval = interval.strip().lower()
    
    # Маппинг интервалов
    interval_map = {
        # Минуты
        "1m": "1",
        "3m": "3",
        "5m": "5",
        "15m": "15",
        "30m": "30",
        # Часы
        "1h": "60",
        "3h": "180",
        "4h": "240",
        "6h": "360",
        "12h": "720",
        # Дни
        "1d": "D",
        "1w": "W",
        "1week": "W",
        "1mth": "M",
        "1month": "M",
    }
    
    # Прямое совпадение
    if interval in interval_map:
        return interval_map[interval]
    
    # Парсинг числовых значений (например "240" уже правильный формат)
    if interval.isdigit():
        return interval
    
    # Если не найдено, пытаемся извлечь число и единицу
    import re
    match = re.match(r'(\d+)([mhdwM])', interval)
    if match:
        number = int(match.group(1))
        unit = match.group(2).lower()
        
        if unit == 'm':  # минуты
            if number in [1, 3, 5, 15, 30]:
                return str(number)
            elif number == 60:
                return "60"  # 60 минут = 1 час
        elif unit == 'h':  # часы
            if number == 1:
                return "60"
            elif number == 3:
                return "180"
            elif number == 4:
                return "240"
            elif number == 6:
                return "360"
            elif number == 12:
                return "720"
        elif unit == 'd':  # дни
            if number == 1:
                return "D"
        elif unit == 'w':  # недели
            if number == 1:
                return "W"
        elif unit == 'M':  # месяцы
            if number == 1:
                return "M"
    
    # Если не удалось конвертировать, возвращаем исходное значение
    # и логируем предупреждение
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Не удалось конвертировать интервал '{interval}', возвращаем исходное значение")
    return interval


def normalize_interval(interval: Union[str, int]) -> str:
    """
    Нормализует интервал к формату Bybit API
    
    Args:
        interval: Интервал в любом формате
        
    Returns:
        Нормализованный интервал в формате Bybit
    """
    if isinstance(interval, int):
        interval = str(interval)
    
    return convert_interval_to_bybit_format(interval)


# Обратная конвертация (для отображения)
def convert_interval_to_human_readable(interval: str) -> str:
    """
    Конвертирует интервал из формата Bybit в человекочитаемый формат
    
    Args:
        interval: Интервал в формате Bybit
        
    Returns:
        Интервал в формате "1h", "4h", "1d" и т.д.
    """
    reverse_map = {
        "1": "1m",
        "3": "3m",
        "5": "5m",
        "15": "15m",
        "30": "30m",
        "60": "1h",
        "120": "2h",
        "240": "4h",
        "360": "6h",
        "720": "12h",
        "D": "1d",
        "W": "1w",
        "M": "1M"
    }
    
    return reverse_map.get(interval, interval)








