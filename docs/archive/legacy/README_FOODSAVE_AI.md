# FoodSave AI - Personal AI Assistant

## 🚀 Overview

FoodSave AI is a comprehensive personal assistant that helps manage food inventory, process receipts, and provide intelligent recommendations for food management. Built with modern technologies including FastAPI, Next.js, Tauri, and AI models.

## ✨ Features

- **AI-Powered Chat Interface** - Natural language conversations with AI agents
- **Receipt Processing** - OCR and data extraction from receipts
- **Food Management** - Inventory tracking and meal planning
- **Smart Recommendations** - AI-driven suggestions for food usage
- **Native Desktop App** - Cross-platform Tauri application
- **Web Search Integration** - Real-time information retrieval
- **Multi-Agent System** - Specialized agents for different tasks

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tauri App     │    │   Next.js Web   │    │   Mobile App    │
│   (Frontend)    │    │   (Frontend)    │    │   (Future)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   FastAPI       │
                    │   Backend       │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   PostgreSQL    │    │   Redis Cache   │    │   Ollama LLM    │
│   Database      │    │                 │    │   (Local AI)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and session management
- **Ollama** - Local LLM inference
- **SQLAlchemy** - ORM for database operations
- **Pydantic** - Data validation and serialization

### Frontend
- **Next.js 15** - React framework with App Router
- **TypeScript** - Type-safe JavaScript
- **Tailwind CSS** - Utility-first CSS framework
- **Tauri** - Cross-platform desktop app framework
- **Rust** - System programming for Tauri backend

### AI & ML
- **Bielik 4.5B** - Polish language model
- **FAISS** - Vector similarity search
- **RAG** - Retrieval-Augmented Generation
- **Multi-Agent System** - Specialized AI agents

## 🚀 Quick Start

### Prerequisites

- **Docker & Docker Compose** - For backend services
- **Node.js 20+** - For frontend development
- **Rust** - For Tauri compilation
- **Git** - Version control

### 1. Clone Repository

```bash
git clone <repository-url>
cd AIASISSTMARUBO
```

### 2. Start Complete System

```bash
# Make startup script executable
chmod +x start_foodsave_ai.sh

# Start all services
./start_foodsave_ai.sh start
```

### 3. Alternative Manual Setup

#### Backend Services
```bash
# Start backend services
docker compose -f docker-compose.dev.yaml up -d

# Check status
docker compose -f docker-compose.dev.yaml ps
```

#### Frontend Development
```bash
# Install dependencies
cd myappassistant-chat-frontend
npm install

# Start development server
npm run dev
```

#### Build Tauri App
```bash
# Build for production
npm run tauri:build

# Run in development
npm run tauri:dev
```

## 🚀 Szybki start (1 polecenie)

1. **Nadaj uprawnienia do uruchamiania skryptu (jednorazowo):**
   ```bash
   chmod +x foodsave-all.sh
   ```
2. **(Opcjonalnie) Dodaj alias, aby uruchamiać system jednym słowem:**
   - Otwórz plik `~/.bashrc` lub `~/.zshrc`:
     ```bash
     nano ~/.bashrc
     # lub
     nano ~/.zshrc
     ```
   - Dodaj na końcu linię (dostosuj ścieżkę do katalogu projektu):
     ```bash
     alias food='/home/marcin/Dokumenty/agentai/makeit/AIASISSTMARUBO/foodsave-all.sh'
     ```
   - Zapisz plik i załaduj ponownie konfigurację:
     ```bash
     source ~/.bashrc
     # lub
     source ~/.zshrc
     ```
3. **Uruchom cały system jednym poleceniem:**
   ```bash
   food dev      # tryb deweloperski (backend + frontend)
   food prod     # tryb produkcyjny (backend + frontend statyczny)
   food tauri    # backend + aplikacja Tauri
   food stop     # zatrzymaj wszystko
   food status   # status systemu
   food logs     # logi backendu
   ```

## 📁 Project Structure

```
AIASISSTMARUBO/
├── src/                          # Backend source code
│   ├── backend/                  # Main backend application
│   │   ├── agents/              # AI agents
│   │   ├── api/                 # API endpoints
│   │   ├── core/                # Core functionality
│   │   ├── models/              # Data models
│   │   └── services/            # Business logic
│   └── tasks/                   # Background tasks
├── myappassistant-chat-frontend/ # Frontend application
│   ├── src/                     # React/Next.js source
│   ├── src-tauri/              # Tauri configuration
│   └── public/                 # Static assets
├── docker-compose.dev.yaml      # Development services
├── start_foodsave_ai.sh         # Startup script
└── README_FOODSAVE_AI.md        # This file
```

## 🔧 Configuration

### Environment Variables

Create `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5433/foodsave
REDIS_URL=redis://localhost:6380

# AI Models
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_MODEL=SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
```

### AI Models

The system uses local AI models via Ollama. Required models:

```bash
# Pull Polish language model
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"}'

# Pull embedding model
curl -X POST http://localhost:11434/api/pull \
  -H "Content-Type: application/json" \
  -d '{"name": "nomic-embed-text"}'
```

## 🎯 Usage

### Desktop Application

1. **Launch**: Run the Tauri application
2. **Chat**: Use natural language to interact with AI
3. **Receipts**: Upload and process receipts
4. **Management**: Track food inventory and plan meals

### API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Chat API
curl -X POST http://localhost:8000/api/chat/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "session_id": "test"}'

# Agents API
curl http://localhost:8000/api/agents/agents
```

### Web Interface

Access the web interface at: `http://localhost:3000`

## 🤖 AI Agents

The system includes specialized AI agents:

- **GeneralConversationAgent** - Main chat interface
- **SearchAgent** - Web search and information retrieval
- **RAGAgent** - Document processing and knowledge base
- **ChefAgent** - Recipe recommendations
- **WeatherAgent** - Weather information
- **OCRAgent** - Receipt text extraction

## 🔍 Monitoring

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Ollama status
curl http://localhost:11434/api/tags

# System status
./start_foodsave_ai.sh status
```

### Logs

```bash
# Backend logs
docker compose -f docker-compose.dev.yaml logs -f backend

# Frontend logs
cd myappassistant-chat-frontend && npm run dev
```

## 🧪 Testing

### Backend Tests

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=src/backend
```

### Frontend Tests

```bash
cd myappassistant-chat-frontend

# Unit tests
npm test

# E2E tests
npm run test:e2e

# Type checking
npm run type-check
```

## 🚀 Deployment

### Production Build

```bash
# Backend
docker build -t foodsave-backend .

# Frontend
cd myappassistant-chat-frontend
npm run build
npm run tauri:build
```

### Docker Compose Production

```bash
docker compose -f docker-compose.prod.yaml up -d
```

## 🔧 Troubleshooting

### Common Issues

1. **Backend won't start**
   ```bash
   # Check Docker services
   docker compose -f docker-compose.dev.yaml ps
   
   # Check logs
   docker compose -f docker-compose.dev.yaml logs backend
   ```

2. **AI model not found**
   ```bash
   # Check available models
   curl http://localhost:11434/api/tags
   
   # Pull required model
   curl -X POST http://localhost:11434/api/pull \
     -H "Content-Type: application/json" \
     -d '{"name": "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"}'
   ```

3. **Tauri app won't build**
   ```bash
   # Check Rust installation
   rustc --version
   
   # Clean and rebuild
   cd myappassistant-chat-frontend
   npm run tauri:build
   ```

### Performance Optimization

- **Database**: Use connection pooling
- **Cache**: Enable Redis caching
- **AI Models**: Use quantized models for faster inference
- **Frontend**: Enable code splitting and lazy loading

## 📚 API Documentation

Interactive API documentation available at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI JSON**: `http://localhost:8000/openapi.json`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

### Development Guidelines

- Follow PEP 8 for Python code
- Use TypeScript for frontend
- Write comprehensive tests
- Update documentation
- Follow conventional commits

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: Create GitHub issues for bugs and feature requests
- **Documentation**: Check this README and inline code comments
- **Community**: Join our Discord/Telegram for discussions

## 🔄 Changelog

### v1.0.0 (2025-06-29)
- Initial release
- Complete AI assistant system
- Tauri desktop application
- Multi-agent architecture
- Receipt processing capabilities

---

**FoodSave AI** - Making food management intelligent and effortless! 🍎🤖 