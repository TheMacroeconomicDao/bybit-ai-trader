#!/bin/bash
# Safe Archive Script - перемещает файлы в archive, не удаляет

set -e

echo "📦 ARCHIVING HISTORICAL FILES..."
echo ""

# Audits & Reviews
echo "📋 Archiving audits..."
for file in *AUDIT*.md *REVIEW*.md DEEP_SYSTEM_AUDIT*.md SYSTEM_COMPLETE_AUDIT*.md AUTONOMOUS_AGENT_FULL_AUDIT*.md SYSTEM_DEEP_REVIEW*.md SYSTEM_WEAKNESS_ANALYSIS*.md; do
    [ -f "$file" ] && mv "$file" archive/audits/ 2>/dev/null || true
done

# Fixes Applied
echo "🔧 Archiving fixes..."
for file in *FIX*.md *FIXES*.md PROMPT_FIX*.md BYBIT_API_FIXES*.md AUDIT_FIXES*.md MCP_FIXES*.md ACCOUNT_AUTHENTICATION_FIX.md DOTENV_LOADING_FIX.md; do
    [ -f "$file" ] && mv "$file" archive/fixes/ 2>/dev/null || true
done

# Test Reports
echo "🧪 Archiving test reports..."
for file in *TEST_REPORT*.md *TESTING*.md COMPLETE_*_TEST*.md MCP_*_TOOLS*.md FUNCTIONS_TEST*.md ALL_TRADING_FUNCTIONS*.md ALTCOINS_TESTING*.md CHEAP_COIN_TESTING*.md TESTING_CHECKLIST*.md; do
    [ -f "$file" ] && mv "$file" archive/tests/ 2>/dev/null || true
done

# Status Reports
echo "📊 Archiving status reports..."
for file in *STATUS*.md IMPLEMENTATION_COMPLETE*.md INTEGRATION_STATUS*.md PROJECT_COMPLETE.md FINAL_VERIFICATION*.md QUEN_AGENT_STATUS*.md; do
    [ -f "$file" ] && mv "$file" archive/reports/ 2>/dev/null || true
done

# Old Issues
echo "⚠️ Archiving old issues..."
for file in *ISSUE.md *PROBLEM*.md BYBIT_API_DELIVERY_PROBLEM.md ANALYSIS_FAILURE*.md QWEN_API_ISSUE.md DEPLOYMENT_ISSUE*.md; do
    [ -f "$file" ] && mv "$file" archive/old_issues/ 2>/dev/null || true
done

# Old Deployment Guides
echo "🚀 Archiving old deployment guides..."
for file in DEPLOYMENT_COMPLETE.md READY_TO_DEPLOY.md PRODUCTION_READY.md; do
    [ -f "$file" ] && mv "$file" archive/deployment/ 2>/dev/null || true
done

# Old Setup Guides (keep only essential)
echo "⚙️ Archiving old setup guides..."
for file in DASHSCOPE_QUICK_START.md QUICK_START_WEBUI.md START_WEBUI*.md ENV_SETUP_COMPLETE.md INTERNAL_CREDENTIALS_SETUP.md; do
    [ -f "$file" ] && mv "$file" archive/setup/ 2>/dev/null || true
done

echo ""
echo "✅ Archive complete!"
echo "Files archived: $(find archive -type f | wc -l | tr -d ' ')"









