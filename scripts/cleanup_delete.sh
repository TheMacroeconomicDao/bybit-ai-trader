#!/bin/bash
# Delete Temporary and Duplicate Files

set -e

echo "🗑️ DELETING TEMPORARY AND DUPLICATE FILES..."
echo ""

# Temporary test scripts
echo "Removing temporary test scripts..."
rm -f test_qwen_simple.py test_qwen_connection.py quick_test_functions.py check_quen_agent.py 2>/dev/null || true

# Example scripts (if already integrated)
echo "Removing example scripts..."
rm -f telegram_publisher_example.py send_post_en.py send_post.py 2>/dev/null || true

# Duplicate protocols in prompts/
echo "Removing duplicate protocols..."
cd prompts/ 2>/dev/null && {
    rm -f market_analysis_protocol.md market_analysis_protocol_FIXED.md market_analysis_protocol_optimized.md 2>/dev/null || true
    cd ..
}

# Duplicate deployment guides
echo "Removing duplicate deployment guides..."
rm -f DEPLOY_QUICK.md 2>/dev/null || true

# Generated files
echo "Removing generated files..."
rm -f available_symbols.txt available_symbols_detailed.txt 2>/dev/null || true

# Duplicate improvement reports
echo "Removing duplicate improvement reports..."
rm -f IMPROVEMENTS_SUMMARY.md SYSTEM_IMPROVEMENTS_COMPLETE.md SYSTEM_IMPROVEMENT_REPORT.md 2>/dev/null || true

echo ""
echo "✅ Temporary files deleted"






