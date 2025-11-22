# 🧹 SYSTEM CLEANUP PROMPT
## Удаление Всего Лишнего для Эффективной Работы

**Версия:** 1.0 CLEANUP  
**Дата:** 22.11.2025  
**Цель:** Оптимизация структуры проекта  
**Приоритет:** Безопасность > Агрессивность

---

## 🎯 ЗАДАЧА

Ты - **Senior DevOps Engineer** с экспертизой в оптимизации проектов.

**Твоя миссия:**
1. Проанализировать ВСЮ структуру проекта TRADER-AGENT
2. Идентифицировать УСТАРЕВШИЕ, ДУБЛИРУЮЩИЕ и НЕНУЖНЫЕ файлы
3. Создать БЕЗОПАСНЫЙ план удаления
4. Предоставить команды для cleanup
5. Организовать оставшиеся файлы

**КРИТИЧНО:** НЕ удалять:
- Рабочий код (mcp_server/, autonomous_agent/)
- Актуальную документацию (SYSTEM_MASTER_INSTRUCTIONS.md, knowledge_base/)
- Конфигурацию (.env, config/)
- Tests

---

## 📋 ШАГ 1: КАТЕГОРИЗАЦИЯ ФАЙЛОВ

### Анализируй каждый файл по категориям:

#### A. КРИТИЧЕСКИЕ (НЕ ТРОГАТЬ) ✅
```
Признаки:
- Используется в коде (imports)
- Referenced в актуальных промптах
- Production configuration
- Working tests
- Master documentation

Примеры:
- mcp_server/*.py (весь рабочий код)
- SYSTEM_MASTER_INSTRUCTIONS.md
- knowledge_base/*.md (все 9)
- .env, requirements.txt
- tests/*.py (рабочие тесты)
```

#### B. УСТАРЕВШИЕ (УДАЛИТЬ) ❌
```
Признаки:
- "OLD", "DEPRECATED", "LEGACY" в названии
- Дата > 6 месяцев назад без обновлений
- Упоминает старые версии
- Contradicts с актуальной документацией
- Никто не использует

Кандидаты для проверки:
- AGENT_FIX_PROMPT.md (устарел?)
- API_FIX_PROMPT.md (проблема уже решена?)
- BYBIT_API_FIXES_COMPLETE.md (история, архив?)
- Множественные TEST_REPORT.md (оставить только последний)
```

#### C. ДУБЛИКАТЫ (КОНСОЛИДИРОВАТЬ) ⚠️
```
Признаки:
- Похожие названия
- Одинаковое содержимое
- Multiple версии (v1, v2, FIXED, OPTIMIZED)
- Redundant information

Примеры найденные:
- market_analysis_protocol.md (3 версии!)
- test_*.py (множественные старые тесты)
- COMPLETE_*_TEST_REPORT.md (история тестов)
- DEPLOYMENT_*.md (несколько гайдов)
```

#### D. АРХИВНЫЕ (ПЕРЕМЕСТИТЬ) 📦
```
Признаки:
- Историческая ценность
- Справочная информация
- Audit reports (завершенные)
- Fix reports (исправления применены)

Действие:
- Создать archive/ директорию
- Переместить туда
- Не удалять (может понадобиться)

Кандидаты:
- Все *_AUDIT_*.md (завершенные аудиты)
- Все *_FIX_*.md (исправления уже применены)
- Все *_REPORT.md (старые отчеты)
- Все *_TESTING_*.md (история тестирования)
```

#### E. ВРЕМЕННЫЕ (УДАЛИТЬ) 🗑️
```
Признаки:
- test_*.py (экспериментальные)
- quick_*.py (временные скрипты)
- *_example.py (примеры после внедрения)
- *_ISSUE.md (проблемы уже решены)

Проверь сначала что не используются!
```

---

## 📊 ШАГ 2: INVENTORY ANALYSIS

### Создай таблицу для КАЖДОГО файла:

```markdown
| Файл | Категория | Размер | Последнее изменение | Used by | Действие |
|------|-----------|--------|---------------------|---------|----------|
| example.md | УСТАРЕВШИЙ | 50KB | 6 мес назад | None | DELETE |
| test_old.py | ВРЕМЕННЫЙ | 12KB | 3 мес назад | None | DELETE |
| analysis.md | ДУБЛИКАТ | 45KB | Дублирует X | None | DELETE, оставить X |
| audit_2023.md | АРХИВНЫЙ | 89KB | История | None | ARCHIVE |
| core_code.py | КРИТИЧЕСКИЙ | 156KB | Active | main.py | KEEP |
```

---

## 🔍 ШАГ 3: ДЕТАЛЬНЫЙ АНАЛИЗ

### Для корневой директории:

**Группы файлов для проверки:**

#### Группа 1: Множественные отчеты
```
Найдено:
- TESTING_REPORT.md
- TEST_REPORT.md  
- TESTING_CHECKLIST_23_FUNCTIONS.md
- COMPLETE_23_FUNCTIONS_TEST_REPORT.md
- COMPLETE_FUNCTIONS_TEST_REPORT.md
- MCP_29_TOOLS_TEST_REPORT.md
- MCP_29_TOOLS_VERIFICATION.md
- И еще 10+ TEST/REPORT файлов

ПРОБЛЕМА: Множественные старые отчеты
РЕШЕНИЕ: Оставить ТОЛЬКО последний актуальный, остальные → archive/
```

#### Группа 2: FIX промпты
```
Найдено:
- AGENT_FIX_PROMPT.md
- API_FIX_PROMPT.md
- PROMPT_FIX_BYBIT_ACCOUNT_TYPES.md
- PROMPT_FIX_KEYERROR_CATEGORY.md
- PROMPT_FIX_SYSTEM_WEAKNESSES.md
- BYBIT_API_FIXES_COMPLETE.md
- AUDIT_FIXES_APPLIED.md
- И др.

ПРОБЛЕМА: Исправления УЖЕ применены
РЕШЕНИЕ: Archive все FIX файлы (история)
```

#### Группа 3: SETUP гайды
```
Найдено:
- SETUP_GUIDE.md
- QUICK_SETUP_AUTONOMOUS_AGENT.md
- SETUP_QWEN_KEY.md
- SETUP_GITHUB_SECRETS.md
- DASHSCOPE_SETUP_GUIDE.md
- QWEN_UI_SETUP.md
- И др.

ПРОБЛЕМА: Множественные setup guides
РЕШЕНИЕ: Консолидировать в ОДИН comprehensive setup guide
```

#### Группа 4: DEPLOYMENT гайды
```
Найдено:
- DEPLOYMENT_GUIDE.md
- DEPLOYMENT_CHECKLIST.md
- DEPLOYMENT_COMPLETE.md
- DEPLOY_QUICK.md
- READY_TO_DEPLOY.md
- PRODUCTION_READY.md

ПРОБЛЕМА: 6 deployment guides
РЕШЕНИЕ: Оставить 1 актуальный, остальные удалить
```

#### Группа 5: README файлы
```
Найдено:
- README.md
- README_RU.md
- README_DASHSCOPE.md
- README_OPENROUTER.md

ПРОБЛЕМА: 4 README
РЕШЕНИЕ: Оставить README.md + README_RU.md (bilingual), остальные → docs/
```

#### Группа 6: Промпты (22 файла в prompts/)
```
ДУБЛИКАТЫ найдены:
- market_analysis_protocol.md
- market_analysis_protocol_FIXED.md
- market_analysis_protocol_optimized.md

РЕШЕНИЕ: Оставить comprehensive_market_analysis_2025.md, удалить старые 3
```

---

## 🗑️ ШАГ 4: CLEANUP PLAN

### Phase 1: Safe Archive (НЕ удалять, переместить)

```bash
#!/bin/bash
# archive_historical.sh

# Создать структуру архива
mkdir -p archive/{audits,fixes,tests,reports,old_docs}

# Archive завершенные аудиты
mv *AUDIT*.md archive/audits/ 2>/dev/null || true
mv *REVIEW*.md archive/audits/ 2>/dev/null || true

# Archive FIX промпты (исправления применены)
mv *FIX*.md archive/fixes/ 2>/dev/null || true
mv *FIXES*.md archive/fixes/ 2>/dev/null || true

# Archive старые test reports
mv *TEST_REPORT*.md archive/tests/ 2>/dev/null || true
mv *TESTING*.md archive/tests/ 2>/dev/null || true
mv COMPLETE_*_TEST*.md archive/tests/ 2>/dev/null || true

# Archive старые отчеты
mv *REPORT.md archive/reports/ 2>/dev/null || true
mv *STATUS*.md archive/reports/ 2>/dev/null || true

# Archive устаревшие docs
mv *ISSUE.md archive/old_docs/ 2>/dev/null || true
mv *PROBLEM*.md archive/old_docs/ 2>/dev/null || true

echo "✅ Archived historical files"
```

### Phase 2: Delete Temporary Files

```bash
#!/bin/bash
# delete_temporary.sh

# Удалить temporary test scripts
rm -f test_qwen_simple.py
rm -f test_qwen_connection.py
rm -f quick_test_functions.py
rm -f check_quen_agent.py

# Удалить example scripts (если уже интегрированы)
rm -f telegram_publisher_example.py
rm -f send_post_en.py
rm -f send_post.py

# Удалить backup scripts (если есть .backup файлы)
rm -f *.backup

# Удалить empty или generated files
rm -f .telegram_chat_id (если пустой)
rm -f available_symbols.txt (генерируется динамически)

echo "✅ Deleted temporary files"
```

### Phase 3: Consolidate Duplicates

```bash
#!/bin/bash
# consolidate_duplicates.sh

# Удалить дублирующие protocols (оставить comprehensive_2025)
cd prompts/
rm -f market_analysis_protocol.md
rm -f market_analysis_protocol_FIXED.md
rm -f market_analysis_protocol_optimized.md
echo "📝 Keep: comprehensive_market_analysis_2025.md"

# Удалить старые audit промпты (оставить актуальные)
rm -f system_deep_review_quick.md
rm -f system_efficiency_audit_quick.md
echo "📝 Keep: system_deep_review_prompt.md, system_efficiency_audit.md"

cd ..

# Удалить дублирующие deployment guides
rm -f DEPLOY_QUICK.md
rm -f DEPLOYMENT_COMPLETE.md
rm -f READY_TO_DEPLOY.md
rm -f PRODUCTION_READY.md
echo "📝 Keep: DEPLOYMENT_GUIDE.md"

# Удалить дублирующие setup guides (консолидировать)
rm -f DASHSCOPE_QUICK_START.md
rm -f QUICK_START_WEBUI.md
echo "📝 Keep: SETUP_GUIDE.md + специфичные (QWEN_UI_SETUP, GITHUB_SECRETS)"

echo "✅ Duplicates consolidated"
```

### Phase 4: Reorganize Structure

```bash
#!/bin/bash
# reorganize_structure.sh

# Создать organized structure
mkdir -p docs/{setup,deployment,api}
mkdir -p archive/{2024,2025}

# Move setup guides в docs/setup/
mv SETUP_*.md docs/setup/ 2>/dev/null || true
mv *SETUP*.md docs/setup/ 2>/dev/null || true

# Move deployment guides в docs/deployment/
mv DEPLOYMENT_*.md docs/deployment/ 2>/dev/null || true

# Move API guides в docs/api/
mv BYBIT_*.md docs/api/ 2>/dev/null || true

# Move README extras в docs/
mv README_DASHSCOPE.md docs/README_DASHSCOPE.md 2>/dev/null || true
mv README_OPENROUTER.md docs/README_OPENROUTER.md 2>/dev/null || true

echo "✅ Structure reorganized"
```

---

## 📝 ШАГ 5: СОЗДАТЬ CLEANUP MANIFEST

### Manifest файл для review:

```markdown
# CLEANUP_MANIFEST.md
## Файлы для удаления/перемещения

### АРХИВИРОВАТЬ (100+ файлов):

**Audits & Reviews:**
- SYSTEM_COMPLETE_AUDIT_*.md → archive/audits/
- DEEP_SYSTEM_AUDIT_PROMPT.md → archive/audits/
- AUTONOMOUS_AGENT_FULL_AUDIT_REPORT.md → archive/audits/
- SYSTEM_DEEP_REVIEW_REPORT.md → archive/audits/
- SYSTEM_WEAKNESS_ANALYSIS_REPORT.md → archive/audits/

**Fixes Applied:**
- AGENT_FIX_PROMPT.md → archive/fixes/
- API_FIX_PROMPT.md → archive/fixes/
- PROMPT_FIX_*.md (все 4) → archive/fixes/
- BYBIT_API_FIXES_COMPLETE.md → archive/fixes/
- AUDIT_FIXES_APPLIED.md → archive/fixes/
- MCP_FIXES_APPLIED.md → archive/fixes/

**Test Reports História:**
- COMPLETE_23_FUNCTIONS_TEST_REPORT.md → archive/tests/
- COMPLETE_FUNCTIONS_TEST_REPORT.md → archive/tests/
- FUNCTIONS_TEST_REPORT.md → archive/tests/
- MCP_29_TOOLS_TEST_REPORT.md → archive/tests/
- MCP_29_TOOLS_VERIFICATION.md → archive/tests/
- TESTING_CHECKLIST_23_FUNCTIONS.md → archive/tests/
- TESTING_REPORT*.md (все) → archive/tests/

**Status Reports (Completed):**
- IMPLEMENTATION_COMPLETE_REPORT.md → archive/reports/
- INTEGRATION_STATUS_REPORT.md → archive/reports/
- QUEN_AGENT_STATUS_REPORT.md → archive/reports/
- PROJECT_COMPLETE.md → archive/reports/
- FINAL_VERIFICATION_REPORT.md → archive/reports/

**Problem Reports (Solved):**
- ANALYSIS_FAILURE_REPORT.md → archive/old_issues/
- BYBIT_API_DELIVERY_PROBLEM.md → archive/old_issues/
- QWEN_API_ISSUE.md → archive/old_issues/

### УДАЛИТЬ ПОЛНОСТЬЮ:

**Temporary Scripts:**
```bash
rm test_qwen_simple.py
rm test_qwen_connection.py
rm quick_test_functions.py
rm check_quen_agent.py
rm telegram_publisher_example.py
rm send_post_en.py
rm send_post.py
```

**Duplicate Protocols:**
```bash
cd prompts/
rm market_analysis_protocol.md
rm market_analysis_protocol_FIXED.md
rm market_analysis_protocol_optimized.md
# KEEP: comprehensive_market_analysis_2025.md ✅
```

**Old Setup Guides (после консолидации):**
```bash
rm DASHSCOPE_QUICK_START.md
rm QUICK_START_WEBUI.md
rm START_WEBUI.md
rm START_WEBUI_FINAL.md
# KEEP: Только актуальные специфичные guides
```

**Duplicate Deployment Guides:**
```bash
rm DEPLOY_QUICK.md
rm DEPLOYMENT_COMPLETE.md
rm READY_TO_DEPLOY.md
rm PRODUCTION_READY.md
# KEEP: DEPLOYMENT_GUIDE.md ✅
```

**Duplicate Improvement Reports:**
```bash
rm IMPROVEMENTS_SUMMARY.md
rm SYSTEM_IMPROVEMENTS_COMPLETE.md
rm SYSTEM_IMPROVEMENT_REPORT.md
# История дублируется
```

**Generated/Dynamic Files:**
```bash
rm available_symbols.txt  # Генерируется динамически
rm available_symbols_detailed.txt  # Генерируется динамически
```

### КОНСОЛИДИРОВАТЬ:

**Action Items:**
1. Объединить все SETUP guides в один comprehensive:
   - Create: `docs/COMPLETE_SETUP_GUIDE.md`
   - Include: Bybit, Qwen, Telegram, GitHub секреты
   - Delete: отдельные мелкие guides

2. Объединить deployment guides:
   - Keep: `DEPLOYMENT_GUIDE.md` (обновить)
   - Delete: остальные

3. Один master README:
   - Keep: `README.md` (English)
   - Keep: `README_RU.md` (Russian)
   - Move специфичные в docs/

---

## 🚀 ШАГ 6: БЕЗОПАСНОЕ ВЫПОЛНЕНИЕ

### Порядок действий (СТРОГИЙ):

#### 1. DRY RUN (проверка без удаления)
```bash
#!/bin/bash
# cleanup_dryrun.sh

echo "🔍 DRY RUN - показываю что будет удалено/перемещено"
echo ""

echo "📦 TO ARCHIVE:"
ls *AUDIT*.md *FIX*.md *REPORT*.md 2>/dev/null | head -20
echo "... и еще $(ls *AUDIT*.md *FIX*.md *REPORT*.md 2>/dev/null | wc -l) файлов"

echo ""
echo "🗑️ TO DELETE:"
ls test_qwen*.py quick_*.py check_*.py 2>/dev/null
ls prompts/market_analysis_protocol*.md 2>/dev/null | grep -v comprehensive

echo ""
echo "⚠️ НЕ БУДЕТ УДАЛЕНО:"
echo "- mcp_server/*.py (весь код)"
echo "- knowledge_base/*.md (все 9)"
echo "- SYSTEM_MASTER_INSTRUCTIONS.md"
echo "- tests/*.py (рабочие тесты)"
echo "- .env, requirements.txt"

echo ""
read -p "Продолжить? (y/n) " -n 1 -r
```

#### 2. Create Archive Structure
```bash
mkdir -p archive/{audits,fixes,tests,reports,old_issues,old_docs,deployment,setup}
echo "✅ Archive structure created"
```

#### 3. Execute Archive (БЕЗОПАСНО)
```bash
#!/bin/bash
# execute_archive.sh

set -e

echo "📦 Archiving historical files..."

# Audits
mv SYSTEM_COMPLETE_AUDIT*.md archive/audits/ 2>/dev/null || true
mv DEEP_SYSTEM_AUDIT_PROMPT.md archive/audits/ 2>/dev/null || true
mv *AUDIT*.md archive/audits/ 2>/dev/null || true

# Fixes
mv *FIX*.md archive/fixes/ 2>/dev/null || true
mv *FIXES*.md archive/fixes/ 2>/dev/null || true

# Test Reports  
mv *TEST_REPORT*.md archive/tests/ 2>/dev/null || true
mv *TESTING*.md archive/tests/ 2>/dev/null || true
mv COMPLETE_*_TEST*.md archive/tests/ 2>/dev/null || true

# Status Reports
mv *STATUS*.md archive/reports/ 2>/dev/null || true
mv IMPLEMENTATION_COMPLETE*.md archive/reports/ 2>/dev/null || true
mv PROJECT_COMPLETE.md archive/reports/ 2>/dev/null || true

# Old Issues
mv *ISSUE.md archive/old_issues/ 2>/dev/null || true
mv *PROBLEM*.md archive/old_issues/ 2>/dev/null || true

echo "✅ Files archived"
ls archive/*/ | wc -l
echo "files moved to archive"
```

#### 4. Execute Delete (С ПОДТВЕРЖДЕНИЕМ)
```bash
#!/bin/bash
# execute_delete.sh

echo "⚠️ DELETING temporary and duplicate files"
echo "Last chance to cancel!"
read -p "Continue? (type YES) " response

if [ "$response" != "YES" ]; then
    echo "Cancelled"
    exit 1
fi

# Delete temporary test scripts
rm -f test_qwen_simple.py
rm -f test_qwen_connection.py
rm -f quick_test_functions.py
rm -f check_quen_agent.py

# Delete examples
rm -f telegram_publisher_example.py
rm -f send_post_en.py
rm -f send_post.py

# Delete duplicate protocols
cd prompts/
rm -f market_analysis_protocol.md
rm -f market_analysis_protocol_FIXED.md  
rm -f market_analysis_protocol_optimized.md
cd ..

# Delete duplicate deployment
rm -f DEPLOY_QUICK.md
rm -f DEPLOYMENT_COMPLETE.md
rm -f READY_TO_DEPLOY.md
rm -f PRODUCTION_READY.md

# Delete generated files
rm -f available_symbols.txt
rm -f available_symbols_detailed.txt

echo "✅ Temporary files deleted"
```

#### 5. Validate (проверка что ничего не сломалось)
```bash
#!/bin/bash
# validate_after_cleanup.sh

echo "🔍 Validating after cleanup..."

# Check критические файлы на месте
critical_files=(
    "SYSTEM_MASTER_INSTRUCTIONS.md"
    ".cursorrules"
    "requirements.txt"
    "mcp_server/market_scanner.py"
    "mcp_server/technical_analysis.py"
    "autonomous_agent/autonomous_analyzer.py"
)

all_ok=true
for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ MISSING: $file"
        all_ok=false
    fi
done

# Check imports
python3 << 'EOF'
try:
    from mcp_server.market_scanner import MarketScanner
    from mcp_server.technical_analysis import TechnicalAnalysis
    from mcp_server.whale_detector import WhaleDetector
    from mcp_server.volume_profile import VolumeProfileAnalyzer
    print("✅ All imports working")
except Exception as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF

if [ "$all_ok" = true ]; then
    echo "✅ Validation passed - system intact"
else
    echo "❌ Validation failed - rollback needed!"
    exit 1
fi
```

---

## 📋 ШАГ 7: ФИНАЛЬНАЯ СТРУКТУРА

### Оптимизированная структура после cleanup:

```
TRADER-AGENT/
├── 📁 mcp_server/ (ВСЕ рабочие .py) ✅ KEEP
├── 📁 autonomous_agent/ (ВСЕ .py) ✅ KEEP
├── 📁 knowledge_base/ (9 .md) ✅ KEEP
├── 📁 prompts/ (очищено: ~15 актуальных) ✅ CLEANED
├── 📁 tests/ (рабочие тесты) ✅ KEEP
├── 📁 models/ ✅ KEEP
├── 📁 config/ ✅ KEEP
├── 📁 scripts/ ✅ KEEP
├── 📁 docs/ (организованные docs) ✅ NEW
│   ├── setup/
│   ├── deployment/
│   └── api/
├── 📁 archive/ (исторические файлы) ✅ NEW
│   ├── audits/
│   ├── fixes/
│   ├── tests/
│   ├── reports/
│   └── old_issues/
│
├── 📄 README.md ✅ KEEP
├── 📄 README_RU.md ✅ KEEP
├── 📄 SYSTEM_MASTER_INSTRUCTIONS.md ✅ KEEP
├── 📄 .cursorrules ✅ KEEP
├── 📄 requirements.txt ✅ KEEP
├── 📄 .env ✅ KEEP
└── 📄 ULTIMATE_MASTER_IMPLEMENTATION_GUIDE.md ✅ NEW

TOTAL FILES: ~150 → ~80 (удалено ~70)
```

---

## 🎯 EXECUTION SEQUENCE

### Безопасный порядок (ОБЯЗАТЕЛЬНЫЙ):

```bash
# 1. Git commit (ПЕРЕД cleanup)
git add -A
git commit -m "Pre-cleanup checkpoint"

# 2. Dry run (ПРОВЕРКА)
bash cleanup_dryrun.sh

# 3. Archive (БЕЗОПАСНО - не удаляет)
bash execute_archive.sh

# 4. Test system (убедиться что работает)
python tests/test_advanced_features.py

# 5. Delete temporary (ТОЛЬКО если тесты ✅)
bash execute_delete.sh

# 6. Consolidate duplicates
bash consolidate_duplicates.sh

# 7. Reorganize structure
bash reorganize_structure.sh

# 8. Final validation
bash validate_after_cleanup.sh

# 9. Git commit результата
git add -A
git commit -m "System cleanup: archived history, removed duplicates"

# 10. Create tag
git tag v2.0-clean
```

---

## ⚠️ ROLLBACK PLAN

Если что-то пошло не так:

```bash
#!/bin/bash
# rollback_cleanup.sh

echo "⚠️ Rolling back cleanup..."

# Restore from archive
if [ -d "archive" ]; then
    cp -r archive/* .
    echo "✅ Files restored from archive"
fi

# Git reset к pre-cleanup
git reset --hard HEAD~1

echo "✅ Rollback complete"
echo "System restored to pre-cleanup state"
```

---

## 📊 ОЖИДАЕМЫЕ РЕЗУЛЬТАТЫ

### До Cleanup:
- Total files: **~250+**
- Documentation: **~150 .md**
- Code files: **~60 .py**
- Confusion: **HIGH**
- Navigation: **СЛОЖНО**

### После Cleanup:
- Total files: **~120**
- Documentation: **~40 .md** (актуальные)
- Code files: **~60 .py** (без изменений)
- Archive: **~100 .md** (история сохранена)
- Confusion: **MINIMAL**
- Navigation: **ПРОСТАЯ**

### Улучшения:
- ✅ **-50% файлов** в root
- ✅ **Zero duplicates**
- ✅ **Zero contradictions**
- ✅ **Organized structure**
- ✅ **Easy navigation**
- ✅ **Fast onboarding**

---

## 🎯 КРИТИЧЕСКИЕ ПРАВИЛА CLEANUP

### НИКОГДА НЕ УДАЛЯЙ:

```
❌ mcp_server/*.py (ВЕСЬ код)
❌ autonomous_agent/*.py (ВЕСЬ код)
❌ knowledge_base/*.md (ВСЕ 9)
❌ SYSTEM_MASTER_INSTRUCTIONS.md
❌ .cursorrules
❌ .env, .env.example
❌ requirements.txt
❌ README.md, README_RU.md
❌ config/*.py, config/*.json
❌ tests/*.py (рабочие тесты)
❌ Dockerfile, docker-compose.yml
❌ .github/, k8s/ (CI/CD)
```

### ВСЕГДА СНАЧАЛА:

```
✅ Git commit перед cleanup
✅ Dry run для проверки
✅ Archive вместо delete (когда сомнение)
✅ Test после каждого шага
✅ Validate что систем

а работает
✅ Rollback готов если нужен
```

---

## 📋 MASTER CLEANUP CHECKLIST

```
PREPARATION:
[ ] Git repo clean (no uncommitted changes)
[ ] All tests passing
[ ] Backup created
[ ] Team notified

ANALYSIS:
[ ] All 250+ files categorized
[ ] Duplicates identified
[ ] Outdated files marked
[ ] Archive candidates listed

EXECUTION:
[ ] Dry run completed
[ ] Review manifest approved
[ ] Archive structure created
[ ] Files archived (Phase 1)
[ ] Validation passed
[ ] Temp files deleted (Phase 2)
[ ] Duplicates removed (Phase 3)
[ ] Structure reorganized (Phase 4)
[ ] Final validation ✅

POST-CLEANUP:
[ ] Git committed
[ ] Tag created (v2.0-clean)
[ ] Documentation updated
[ ] Team informed
[ ] System tested
[ ] Performance verified
```

---

## 🎯 IMMEDIATE ACTION

**Запусти прямо сейчас:**

```bash
# Quick cleanup (safe, only archive)
bash << 'EOF'
mkdir -p archive/{audits,fixes,tests,reports}

# Archive завершенные аудиты
for file in *AUDIT*.md *REVIEW*.md; do
    [ -f "$file" ] && mv "$file" archive/audits/
done

# Archive fix промпты
for file in *FIX*.md *FIXES*.md; do
    [ -f "$file" ] && mv "$file" archive/fixes/
done

# Archive test reports
for file in *TEST*.md *TESTING*.md; do
    [ -f "$file" ] && mv "$file" archive/tests/
done

echo "✅ Quick archive complete"
echo "Files archived: $(find archive -type f | wc -l)"
EOF
```

**Проверь:**
```bash
# Система все еще работает?
python -c "from mcp_server.market_scanner import MarketScanner; print('✅ OK')"
```

**Если ✅ - продолжай полный cleanup**  
**Если ❌ - rollback: `cp archive/*/* .`**

---

## 🏆 ФИНАЛЬНЫЙ РЕЗУЛЬТАТ

### После Cleanup Будет:

✅ **Чистая структура** - легко navigate  
✅ **100% актуальные** docs  
✅ **Zero duplicates**  
✅ **Zero contradictions**  
✅ **История сохранена** в archive/  
✅ **Fast onboarding** новых разработчиков  
✅ **Production-ready** organization

### Время Cleanup: 1-2 часа
### Risk: MINIMAL (все с backups)
### Improvement: MASSIVE organization

**СИСТЕМА БУДЕТ КАК НОВАЯ!** 🚀

---

**Версия:** 1.0 CLEANUP  
**Статус:** READY TO EXECUTE  
**Safety:** MAXIMUM (backups + archive + validation)