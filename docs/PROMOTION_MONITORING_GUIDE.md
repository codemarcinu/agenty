# 🛒 Promotion Monitoring System Guide

## 📋 Overview

The Promotion Monitoring System is a comprehensive solution for tracking and analyzing retail promotions in real-time. It combines automated web scraping, AI-powered analysis, and a modern desktop interface to help users find the best deals across major retailers.

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Sidecar       │
│   (Tauri/React) │◄──►│   (FastAPI)     │◄──►│   Services      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌─────────────────┐              │
         └──────────────►│   Database      │◄─────────────┘
                        │   (SQLite)      │
                        └─────────────────┘
```

### Components

1. **PromotionsMonitor Component** - React-based dashboard with real-time data
2. **Promotion Scraping Agent** - AI agent for automated data collection
3. **Sidecar Services** - Scalable microservices for processing
4. **Tauri Integration** - Desktop application capabilities

## 🚀 Features

### Real-time Promotion Tracking
- Automated monitoring of major Polish retailers (Lidl, Biedronka, etc.)
- Real-time price comparison and analysis
- Historical data tracking for trend analysis

### AI-Powered Analysis
- Intelligent deal scoring and recommendations
- Category-based analysis and insights
- Personalized shopping recommendations

### Desktop Application
- Native desktop experience via Tauri
- Offline capability with local data storage
- Cross-platform compatibility (Windows, macOS, Linux)

### Polish Market Support
- Localized interface in Polish
- Support for Polish retailers and currency
- Regional promotion patterns and analysis

## 📦 Installation

### Prerequisites
- Node.js 18+ and npm
- Rust toolchain (for Tauri)
- Python 3.12+ (for backend services)

### Quick Start
```bash
# Navigate to frontend directory
cd myappassistant-chat-frontend

# Install dependencies
npm install

# Start development server
npm run tauri dev
```

### Sidecar Services Setup
```bash
# AI Agent Service
cd sidecar-ai
pip install -r requirements.txt
python agent.py

# Web Scraper Service
cd sidecar-scraper
npm install
node index.js
```

## 🎯 Usage

### Accessing the Dashboard
1. Launch the Tauri application
2. Navigate to the "Promotions" section
3. View real-time promotion data and analysis

### Key Dashboard Features
- **Summary Cards**: Total promotions, average discounts, store comparisons
- **Best Deals**: Highlighted offers with highest savings
- **Store Analysis**: Performance comparison across retailers
- **Category Insights**: Product category analysis and trends

### Data Refresh
- Manual refresh via "Odśwież" button
- Automatic updates every 30 minutes
- Real-time notifications for new deals

## 🔧 Configuration

### Environment Variables
```env
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./foodsave.db

# Scraping Configuration
SCRAPER_INTERVAL=1800  # 30 minutes
MAX_CONCURRENT_SCRAPERS=5

# AI Model Configuration
OLLAMA_BASE_URL=http://localhost:11434
MODEL_NAME=bielik-4.5b
```

### Retailer Configuration
```json
{
  "retailers": [
    {
      "name": "Lidl",
      "base_url": "https://www.lidl.pl",
      "scraping_rules": {
        "promotion_selector": ".promotion-item",
        "price_selector": ".price",
        "title_selector": ".product-title"
      }
    },
    {
      "name": "Biedronka",
      "base_url": "https://www.biedronka.pl",
      "scraping_rules": {
        "promotion_selector": ".offer-item",
        "price_selector": ".current-price",
        "title_selector": ".product-name"
      }
    }
  ]
}
```

## 🧪 Testing

### Component Tests
```bash
# Frontend tests
npm test

# Backend agent tests
pytest tests/unit/test_promo_scraping_agent.py

# Integration tests
pytest tests/integration/test_promotion_monitoring.py
```

### E2E Tests
```bash
# Run Playwright tests
npm run test:e2e

# Specific promotion tests
npm run test:e2e -- --grep "promotion"
```

## 📊 Monitoring

### Key Metrics
- **Scraping Success Rate**: Percentage of successful data collection
- **Data Freshness**: Time since last successful update
- **Error Rates**: Failed scraping attempts and reasons
- **Performance**: Response times and processing speed

### Logs
```bash
# View promotion monitoring logs
tail -f logs/promotion_monitoring.log

# Scraper service logs
tail -f logs/scraper.log

# AI agent logs
tail -f logs/ai_agent.log
```

## 🔒 Security

### Data Protection
- No personal data collection
- Local data storage only
- Encrypted database connections
- Secure API endpoints

### Rate Limiting
- Respectful scraping with delays
- User-agent rotation
- IP rotation for large-scale operations
- Compliance with robots.txt

## 🐛 Troubleshooting

### Common Issues

#### Scraping Failures
```bash
# Check scraper service status
ps aux | grep scraper

# Verify network connectivity
curl -I https://www.lidl.pl

# Check scraping logs
tail -f logs/scraper.log
```

#### Database Connection Issues
```bash
# Test database connectivity
sqlite3 foodsave.db "SELECT 1;"

# Check database schema
sqlite3 foodsave.db ".schema promotions"
```

#### Tauri Build Issues
```bash
# Clean and rebuild
npm run tauri clean
npm run tauri build

# Check Rust dependencies
cargo check
```

### Performance Optimization

#### Database Optimization
```sql
-- Optymalizacja SQLite

#### Caching Strategy
```python
# Redis caching for frequently accessed data
@cache(expire=300)  # 5 minutes
def get_store_summary(store_name: str):
    return db.query(Promotion).filter_by(store=store_name).all()
```

## 📈 Future Enhancements

### Planned Features
- **Mobile App**: React Native version for mobile devices
- **Push Notifications**: Real-time deal alerts
- **Price History**: Historical price tracking and analysis
- **Shopping Lists**: Integration with existing shopping features
- **Social Features**: Share deals and recommendations

### Technical Improvements
- **Machine Learning**: Predictive pricing models
- **Advanced Scraping**: JavaScript rendering and anti-bot bypass
- **API Integration**: Direct retailer API connections
- **Cloud Deployment**: Scalable cloud infrastructure

## 📚 Related Documentation

- [Frontend Architecture](FRONTEND_ARCHITECTURE.md)
- [AI Agents Guide](AGENTS_GUIDE.md)
- [Database Guide](DATABASE_GUIDE.md)
- [Testing Guide](TESTING_GUIDE.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)

## 🤝 Contributing

### Development Guidelines
- Follow existing code patterns and conventions
- Add comprehensive tests for new features
- Update documentation for any changes
- Use conventional commit messages

### Code Standards
- **TypeScript**: Strict mode, ESLint, Prettier
- **Python**: PEP 8, type hints, docstrings
- **React**: Functional components, hooks, TypeScript
- **Testing**: >90% coverage required

---

**Last Updated**: 30.06.2025  
**Version**: 1.0.0  
**Status**: Production Ready ✅ 