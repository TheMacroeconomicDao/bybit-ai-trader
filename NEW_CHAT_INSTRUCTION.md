# 🎯 ИНСТРУКЦИЯ ДЛЯ НОВОГО ЧАТА - КРИТИЧЕСКИЕ ИСПРАВЛЕНИЯ

## Дата: 2025-11-21
## Проект: TRADER-AGENT - AI Trading System


изучи документы :
/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/SYSTEM_COMPLETE_AUDIT_EXTENDED.md

/Users/Gyber/GYBERNATY-ECOSYSTEM/TRADER-AGENT/SYSTEM_COMPLETE_AUDIT_AND_FIX_INSTRUCTION.md
---

## 📋 КРАТКОЕ РЕЗЮМЕ ПРОБЛЕМ

### 🔴 КРИТИЧЕСКАЯ ПРОБЛЕМА
**MCP сервер показывает "0 prompts" несмотря на наличие промптов в папке `prompts/`**

**Причина:** Отсутствуют функции `@app.list_resources()` и `@app.read_resource()` в MCP серверах

**Последствия:**
- Autonomous agent не использует промпты через MCP
- База знаний не интегрирована в систему
- Качество анализа низкое (нет best practices валидации)
- Не соблюдается CRITICAL_REQUIREMENTS.md

---

## ✅ ЧТО НУЖНО СДЕЛАТЬ (ПРИОРИТЕТЫ)

### 🔴 КРИТИЧЕСКИЙ ПРИОРИТЕТ #1: Интеграция Промптов в MCP

**Файл:** `mcp_server/full_server.py`

**Добавить в конец файла (перед `async def main()`):**

```python
from mcp.types import Resource, TextResourceContents

@app.list_resources()
async def list_resources() -> List[Resource]:
    """Список всех промптов и базы знаний"""
    
    base_path = Path(__file__).parent.parent
    resources = []
    
    # Промпты
    prompts_dir = base_path / "prompts"
    if prompts_dir.exists():
        for prompt_file in prompts_dir.glob("*.md"):
            resources.append(Resource(
                uri=f"prompt:///{prompt_file.stem}",
                name=prompt_file.stem,
                description=f"Trading prompt: {prompt_file.stem}",
                mimeType="text/markdown"
            ))
    
    # База знаний
    kb_dir = base_path / "knowledge_base"
    if kb_dir.exists():
        for kb_file in kb_dir.glob("*.md"):
            resources.append(Resource(
                uri=f"knowledge:///{kb_file.stem}",
                name=kb_file.stem,
                description=f"Trading knowledge: {kb_file.stem}",
                mimeType="text/markdown"
            ))
    
    logger.info(f"Listed {len(resources)} resources")
    return resources


@app.read_resource()
async def read_resource(uri: str) -> TextResourceContents:
    """Чтение промпта или базы знаний"""
    
    base_path = Path(__file__).parent.parent
    
    if uri.startswith("prompt:///"):
        prompt_name = uri.replace("prompt:///", "")
        prompt_file = base_path / "prompts" / f"{prompt_name}.md"
        
        if not prompt_file.exists():
            raise ValueError(f"Prompt not found: {prompt_name}")
        
        content = prompt_file.read_text(encoding="utf-8")
        logger.info(f"Read prompt: {prompt_name} ({len(content)} chars)")
        
        return TextResourceContents(
            uri=uri,
            mimeType="text/markdown",
            text=content
        )
    
    elif uri.startswith("knowledge:///"):
        kb_name = uri.replace("knowledge:///", "")
        kb_file = base_path / "knowledge_base" / f"{kb_name}.md"
        
        if not kb_file.exists():
            raise ValueError(f"Knowledge base not found: {kb_name}")
        
        content = kb_file.read_text(encoding="utf-8")
        logger.info(f"Read knowledge: {kb_name} ({len(content)} chars)")
        
        return TextResourceContents(
            uri=uri,
            mimeType="text/markdown",
            text=content
        )
    
    else:
        raise ValueError(f"Unknown resource URI: {uri}")
```

**Также добавить в `mcp_server/autonomous_agent_server.py`** - аналогично

---

### 🔴 КРИТИЧЕСКИЙ ПРИОРИТЕТ #2: Улучшить Autonomous Agent

**Проблемы:**
- Confluence score не основан на Entry Decision Framework
- Не всегда показывает ОБА направления (LONG и SHORT)
- Нет валидации по чеклисту из `7_zero_risk_methodology.md`

**Решение - Читай детали в:**
- `SYSTEM_COMPLETE_AUDIT_AND_FIX_INSTRUCTION.md` - основной план
- `SYSTEM_COMPLETE_AUDIT_EXTENDED.md` - advanced фичи

**Ключевые изменения в `autonomous_agent/autonomous_analyzer.py`:**

1. **Улучшить `_calculate_final_score()`** - использовать матрицу из Entry Decision Framework
2. **Улучшить `_finalize_top_3_longs_and_shorts()`** - ВСЕГДА возвращать оба направления
3. **Добавить ValidationEngine** - проверка по чеклисту

---

### 🟡 ВЫСОКИЙ ПРИОРИТЕТ #3: Создать ValidationEngine

**Создать новый файл:** `mcp_server/validation_engine.py`

**Цель:** Валидация всех возможностей по чеклисту из `7_zero_risk_methodology.md`

**10 критериев безопасного входа:**
1. Trend alignment (3-4 TF)
2. Multiple indicators (5+)
3. Strong S/R Level
4. Volume confirmation
5. Pattern >70% reliability
6. R:R ≥ 1:2
7. Favorable market conditions
8. BTC supports direction
9. Positive sentiment
10. On-chain supports

**Минимум 8/10 критериев для валидного сигнала!**

---

### 🟡 ВЫСОКИЙ ПРИОРИТЕТ #4: Улучшить QwenClient

**Файл:** `autonomous_agent/qwen_client.py`

**Добавить:**
- `_validate_critical_requirements()` - проверка что есть 3 LONGS и 3 SHORTS
- `_fix_critical_requirements()` - исправление если Qwen не выдал оба направления
- Structured output validation

---

## 📚 ПОЛНАЯ ДОКУМЕНТАЦИЯ

### Основные Документы:

1. **SYSTEM_COMPLETE_AUDIT_AND_FIX_INSTRUCTION.md**
   - Подробный план исправлений
   - Примеры кода для всех изменений
   - План действий с приоритетами

2. **SYSTEM_COMPLETE_AUDIT_EXTENDED.md**
   - Advanced фичи (Order Flow, ML Integration)
   - Best Practices 2025
   - Production deployment guide

3. **MASTER_PROMPT.md**
   - Оригинальное видение проекта
   - Требования к системе
   - Expected результаты

### Промпты (в `prompts/`):

- `agent_core_instructions.md` - основные инструкции для AI
- `market_analysis_protocol_optimized.md` - оптимизированный протокол анализа
- `entry_decision_framework.md` - framework принятия решений
- `CRITICAL_REQUIREMENTS.md` - ОБЯЗАТЕЛЬНО показывать оба направления!

### База Знаний (в `knowledge_base/`):

- `7_zero_risk_methodology.md` - методология нулевого риска
- `6_market_analysis_framework.md` - framework анализа рынка
- `4_entry_strategies.md` - стратегии входа
- Всего 8 документов с best practices

---

## 🎯 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### После Исправлений:

```
2025-11-21 XX:XX:XX [info] Found 35 tools, 12 prompts, 8 resources
```

**Вместо текущего:**
```
2025-11-21 09:18:55.725 [info] Found 35 tools, 0 prompts, and 0 resources
```

### Качество Анализа:

- ✅ **ВСЕГДА** показывает ОБА направления (LONG и SHORT)
- ✅ Confluence score >= 8.0 для рекомендованных сигналов
- ✅ Вероятность >= 70% для всех сигналов
- ✅ R:R >= 1:2 минимум
- ✅ Детальное обоснование каждой возможности
- ✅ Предупреждения для слабых setup (score < 8.0)

### Процесс Анализа (OPTIMIZED):

1. **ШАГ 1:** Быстрый market overview + BTC analysis (2 мин)
2. **ШАГ 2:** Параллельное сканирование (scan_market + find_*) (1 мин)
3. **ШАГ 3:** Фильтрация по score >= 7.0 (30 сек)
4. **ШАГ 4:** Детальный анализ ТОП 3-5 кандидатов (5 мин)
5. **ШАГ 5:** Валидация через ValidationEngine (1 мин)
6. **ШАГ 6:** Финализация ТОП 3 LONGS + ТОП 3 SHORTS (1 мин)

**ИТОГО:** < 10 минут качественного анализа

---

## 🚀 QUICK START ДЛЯ НОВОГО ЧАТА

### Шаг 1: Понять Проблему
```bash
# Читай:
cat SYSTEM_COMPLETE_AUDIT_AND_FIX_INSTRUCTION.md
```

### Шаг 2: Начать с Критических Исправлений
```bash
# 1. Интеграция промптов в MCP
code mcp_server/full_server.py
# Добавь @app.list_resources() и @app.read_resource()

# 2. То же для autonomous_agent_server.py
code mcp_server/autonomous_agent_server.py
```

### Шаг 3: Создать ValidationEngine
```bash
# Создай новый файл
code mcp_server/validation_engine.py
# Используй код из SYSTEM_COMPLETE_AUDIT_AND_FIX_INSTRUCTION.md
```

### Шаг 4: Обновить Autonomous Analyzer
```bash
code autonomous_agent/autonomous_analyzer.py
# Улучши _calculate_final_score()
# Улучши _finalize_top_3_longs_and_shorts()
```

### Шаг 5: Тестирование
```bash
# Запусти MCP server
uv run python mcp_server/full_server.py

# Проверь что видно resources
# Должно быть: "35 tools, 12 prompts, 8 resources"
```

---

## 🧪 ТЕСТИРОВАНИЕ

### Проверка Интеграции Промптов:

```python
# В новом Python shell
from pathlib import Path
import asyncio
from mcp_server.full_server import list_resources, read_resource

# Список всех resources
resources = asyncio.run(list_resources())
print(f"Total resources: {len(resources)}")

# Чтение промпта
content = asyncio.run(read_resource("prompt:///CRITICAL_REQUIREMENTS"))
print(f"Prompt length: {len(content.text)} chars")
```

### Проверка Autonomous Agent:

```python
# Запуск анализа
python scripts/test_autonomous_agent.py

# Проверь результат:
# 1. Есть ли 3 LONGS?
# 2. Есть ли 3 SHORTS?
# 3. Confluence score >= 8.0?
# 4. Есть ли детальное обоснование?
```

---

## ⚠️ КРИТИЧЕСКИЕ НАПОМИНАНИЯ

### ❌ НЕ ДЕЛАЙ:
1. ❌ НЕ игнорируй одно из направлений (LONG или SHORT)
2. ❌ НЕ предлагай сигналы с confluence < 8.0 без предупреждения
3. ❌ НЕ используй статический баланс ($30) - ВСЕГДА проверяй реальный через get_account_info()
4. ❌ НЕ пропускай валидацию по чеклисту из 7_zero_risk_methodology.md

### ✅ ОБЯЗАТЕЛЬНО ДЕЛАЙ:
1. ✅ ВСЕГДА показывай ОБА направления (LONG и SHORT)
2. ✅ Используй Entry Decision Framework для confluence scoring
3. ✅ Валидируй через ValidationEngine перед показом пользователю
4. ✅ Проверяй CRITICAL_REQUIREMENTS.md перед финализацией
5. ✅ Детально объясняй каждое решение

---

## 📊 МЕТРИКИ УСПЕХА

### Технические Метрики:
- ✅ MCP resources > 0 (должно быть 12 prompts + 8 knowledge)
- ✅ Время анализа < 10 минут
- ✅ Memory usage < 2GB
- ✅ No errors в логах

### Качественные Метрики:
- ✅ Win rate > 70% для сигналов с score >= 8.0
- ✅ Probability estimation accuracy > 80%
- ✅ R:R actual > R:R predicted (95% времени)
- ✅ User satisfaction (качество обоснования)

---

## 🔗 ПОЛЕЗНЫЕ ССЫЛКИ

- [Bybit API Docs](https://bybit-exchange.github.io/docs/v5/intro)
- [MCP Protocol Spec](https://spec.modelcontextprotocol.io/)
- [Entry Decision Framework](prompts/entry_decision_framework.md)
- [Zero Risk Methodology](knowledge_base/7_zero_risk_methodology.md)

---

## 📝 ФИНАЛЬНЫЙ ЧЕКЛИСТ

Перед тем как считать задачу выполненной:

- [ ] MCP показывает "35 tools, 12 prompts, 8 resources"
- [ ] Autonomous agent использует промпты через MCP
- [ ] ValidationEngine создан и интегрирован
- [ ] ВСЕГДА показывает оба направления (LONG + SHORT)
- [ ] Confluence score основан на Entry Decision Framework
- [ ] Проверка по чеклисту из 7_zero_risk_methodology.md
- [ ] Тесты пройдены (unit + integration)
- [ ] Документация обновлена
- [ ] Production-ready (error handling, logging, monitoring)

---

## 🎯 ИТОГ

**Эта инструкция содержит ВСЁ необходимое для исправления критических проблем системы.**

**НАЧНИ С:**
1. Интеграции промптов в MCP (Приоритет #1)
2. Создания ValidationEngine (Приоритет #2)
3. Улучшения Autonomous Agent (Приоритет #3)

**ИСПОЛЬЗУЙ:**
- `SYSTEM_COMPLETE_AUDIT_AND_FIX_INSTRUCTION.md` - для деталей реализации
- `SYSTEM_COMPLETE_AUDIT_EXTENDED.md` - для advanced фич
- Существующие промпты и базу знаний - для контекста

**ЦЕЛЬ:**
Превратить систему из прототипа в профессиональный торговый инструмент с качеством анализа на уровне best practices 2025.

---

**Удачи!** 🚀

**Версия:** 1.0  
**Дата:** 2025-11-21  
**Автор:** System Audit Team  
**Статус:** READY FOR NEW CHAT