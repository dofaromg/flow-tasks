# Makefile for Particle Satellite Network
# 粒子AI未來星鏈平行粒子雲網路 - 便捷命令集合

.PHONY: help install start stop test clean demo

help:
	@echo "================================================"
	@echo "🚀 Particle Satellite Network - Commands"
	@echo "================================================"
	@echo "  make install      - Install dependencies"
	@echo "  make start        - Start the system"
	@echo "  make stop         - Stop all services"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-int     - Run integration tests only"
	@echo "  make demo         - Run demo scenarios"
	@echo "  make clean        - Clean temporary files"
	@echo "  make lint         - Run code linting"
	@echo "  make format       - Format code"
	@echo "================================================"

install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt
	@echo "✅ Dependencies installed"

start:
	@echo "🚀 Starting Particle Satellite Network..."
	./scripts/start_system.sh

stop:
	@echo "🛑 Stopping all services..."
	pkill -f "particle_satellite_network" || true
	@echo "✅ Services stopped"

test:
	@echo "🧪 Running all tests..."
	pytest tests/ -v

test-unit:
	@echo "🧪 Running unit tests..."
	pytest tests/unit/ -v

test-int:
	@echo "🧪 Running integration tests..."
	pytest tests/integration/ -v

test-perf:
	@echo "🧪 Running performance tests..."
	pytest tests/performance/ -v

demo:
	@echo "🎬 Running demo scenarios..."
	python core/satellite_layers/geo_layer.py
	python core/satellite_layers/meo_layer.py
	python core/satellite_layers/leo_layer.py

clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	@echo "✅ Cleaned"

lint:
	@echo "🔍 Running linter..."
	pylint core/ cicd_pipeline/ api/ || true

format:
	@echo "✨ Formatting code..."
	black core/ cicd_pipeline/ api/
	isort core/ cicd_pipeline/ api/
	@echo "✅ Code formatted"

status:
	@echo "📊 System Status:"
	@ps aux | grep -i "particle_satellite_network" | grep -v grep || echo "No services running"

# Development helpers
dev-install:
	@echo "🛠️  Installing dev dependencies..."
	pip install -r requirements.txt
	pip install pytest black pylint isort
	@echo "✅ Dev dependencies installed"

watch:
	@echo "👀 Watching for changes..."
	watchmedo auto-restart --patterns="*.py" --recursive python core/satellite_layers/geo_layer.py
