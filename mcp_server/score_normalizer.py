"""
Score Normalizer
Единая система нормализации scoring для всего проекта
"""

from typing import Dict, Any, Optional


def normalize_score(score: float, system: str = "20-point") -> float:
    """
    Нормализация score в диапазон 0-10
    
    Args:
        score: Исходный score
        system: Система scoring ("20-point", "15-point", "12-point", "10-point")
        
    Returns:
        Нормализованный score в диапазоне 0-10
    """
    if score is None or score < 0:
        return 0.0
    
    # Определяем максимум для системы
    max_scores = {
        "20-point": 20.0,
        "15-point": 15.0,
        "12-point": 12.0,
        "10-point": 10.0
    }
    
    max_score = max_scores.get(system, 10.0)
    
    # Нормализуем в 0-10
    normalized = (score / max_score) * 10.0
    
    return round(min(10.0, max(0.0, normalized)), 2)


def normalize_opportunity_score(opportunity: Dict[str, Any]) -> Dict[str, Any]:
    """
    Нормализация всех score полей в opportunity
    
    Args:
        opportunity: Объект возможности
        
    Returns:
        Opportunity с нормализованными score
    """
    # Определяем какая система использовалась
    raw_score = opportunity.get("score", 0.0)
    
    # Автоопределение системы по значению
    if raw_score > 15.0:
        system = "20-point"
    elif raw_score > 12.0:
        system = "15-point"
    elif raw_score > 10.0:
        system = "12-point"
    else:
        system = "10-point"
    
    # Нормализуем все варианты score
    normalized = normalize_score(raw_score, system)
    
    opportunity["score"] = normalized
    opportunity["confluence_score"] = normalized
    opportunity["final_score"] = normalized
    
    # Если есть score_breakdown, нормализуем total
    if "score_breakdown" in opportunity:
        breakdown = opportunity["score_breakdown"]
        if isinstance(breakdown, dict) and "total" in breakdown:
            breakdown["total"] = normalized
    
    return opportunity


def validate_score_fields(opportunity: Dict[str, Any]) -> bool:
    """
    Валидация наличия и корректности score полей
    
    Args:
        opportunity: Объект возможности
        
    Returns:
        True если все score поля валидны
    """
    required_fields = ["score", "confluence_score", "final_score"]
    
    for field in required_fields:
        value = opportunity.get(field)
        if value is None:
            return False
        if not isinstance(value, (int, float)):
            return False
        if value < 0 or value > 10:
            return False
    
    return True