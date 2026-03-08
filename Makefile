.PHONY: help clean

# Default target
help:
	@echo "Claude Code Team System"
	@echo ""
	@echo "Commands:"
	@echo "  make help    - Show this help"
	@echo "  make clean   - Remove __pycache__ directories"
	@echo ""

# Clean Python cache files
clean:
	@echo "🧹 Cleaning Python cache files..."
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean completed!"
