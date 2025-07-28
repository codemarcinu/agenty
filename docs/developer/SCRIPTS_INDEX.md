# 📋 FoodSave AI - Scripts Index

## 🚀 Main Entry Points

### **For End Users**
- **`scripts/main/foodsave-all.sh`** - 🎯 **RECOMMENDED** - Comprehensive system manager with user-friendly interface
- **`scripts/main/foodsave.sh`** - Production Docker management
- **`scripts/development/foodsave-dev.sh`** - Development environment setup

### **For Developers**
- **`scripts/main/docker-manager.sh`** - Advanced Docker operations and container management
- **`scripts/development/dev-up.sh`** - Quick development environment startup
- **`scripts/deployment/docker-setup.sh`** - Production deployment setup

---

## 📁 Directory Structure

### **`scripts/main/`** - Primary System Management
- `foodsave-all.sh` - Comprehensive system manager (user-friendly)
- `foodsave.sh` - Production Docker management
- `docker-manager.sh` - Advanced Docker operations
- `manage_app.sh` - Application lifecycle management
- `start_manager.sh` - Service startup coordination
- `manager.sh` - System management utilities
- `start.sh` - System startup script
- `stop.sh` - System shutdown script

### **`scripts/development/`** - Development Environment
- `foodsave-dev.sh` - Development Docker environment
- `dev-up.sh` - Quick development startup
- `start_sekwencyjny.sh` - Sequential development startup
- `run_async_dev.sh` - Async development runner
- `start-dev-mode.sh` - Development mode starter
- `start-dev.sh` - Development environment setup
- `start-local.sh` - Local development environment
- `health-check.sh` - Development health monitoring
- `cleanup.sh` - Development environment cleanup
- `dev-environment.sh` - Environment configuration
- `start-integration-tests.sh` - Integration testing
- `start_monitoring.sh` - Development monitoring

### **`scripts/deployment/`** - Production Deployment
- `docker-setup.sh` - Docker environment setup
- `build-all-containers.sh` - Container building
- `build-all-optimized.sh` - Optimized builds
- `rebuild-with-models.sh` - Model-inclusive rebuild
- `deploy-to-vps.sh` - VPS deployment
- `setup-telegram-webhook.sh` - Telegram integration
- `setup-mikrus-subdomain.sh` - Subdomain configuration

### **`scripts/automation/`** - Automated Processes
- `organize-scripts.sh` - Script organization
- `update-documentation.sh` - Documentation updates
- `generate-toc.sh` - Table of contents generation
- `validate-links.sh` - Link validation
- `cleanup_unnecessary_files.sh` - File cleanup
- `full_documentation_update_2025_07_13.sh` - Comprehensive doc update
- `reset_qt_python_env.sh` - Qt environment reset
- `update_dates_2025_07_13.sh` - Date updates

### **`scripts/utils/`** - Utility Scripts
- `setup-logging.sh` - Logging configuration
- `setup-nvidia-docker.sh` - NVIDIA Docker setup
- `stop_all.sh` - System shutdown
- `start_backend.sh` - Backend startup
- `start_foodsave_ai.sh` - AI system startup
- `setup_tests.sh` - Test environment setup
- `setup_gui.sh` - GUI setup
- `fix_gui_env.sh` - GUI environment fixes
- `health-check.sh` - System health verification
- `run_all.sh` - System startup
- `run_system.sh` - System execution

### **`scripts/`** - Desktop Application
- `gui_refactor.sh` - 🎯 **Modern GUI Launcher** (Web + Glassmorphism)

---

## 🎯 Quick Start Commands

### **Start Everything (Recommended)**
```bash
./scripts/main/foodsave-all.sh
```

### **Development Mode**
```bash
./scripts/development/dev-up.sh
```

### **Production Deployment**
```bash
./scripts/deployment/docker-setup.sh
```

### **Modern GUI (Tauri) App**
```bash
./scripts/gui_refactor.sh
```

---

## 🔧 Troubleshooting

### **Health Check**
```bash
./scripts/utils/health-check.sh
```

### **Stop All Services**
```bash
./scripts/utils/stop_all.sh
```

### **Fix GUI Environment**
```bash
./scripts/utils/fix_gui_env.sh
```

---

## 📚 Related Documentation

- **[Main README](README.md)** - Project overview
- **[Quick Start Guide](docs/QUICK_START.md)** - Getting started
- **[Development Setup](docs/guides/development/SETUP.md)** - Developer guide
- **[Architecture](docs/core/ARCHITECTURE.md)** - System architecture
- **[Scripts Documentation](docs/SCRIPTS_DOCUMENTATION.md)** - Detailed script documentation

---

*Generated during project reorganization - July 2025*