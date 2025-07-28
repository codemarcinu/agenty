# FoodSave AI - Promotion Monitoring System Implementation

## Overview

The FoodSave AI project now includes a comprehensive promotion monitoring system that uses Tauri sidecars for web scraping and AI analysis. This system monitors promotions from Polish grocery stores (Lidl and Biedronka) and provides intelligent insights and recommendations.

## Architecture

### 1. Tauri Sidecar Architecture

The system uses a modular sidecar architecture with two main components:

#### Node.js Scraper Sidecar (`sidecar-scraper/`)
- **Technology**: Node.js with Puppeteer and stealth plugins
- **Purpose**: Web scraping of grocery store promotion pages
- **Features**:
  - Stealth browsing to avoid detection
  - Retry mechanism with exponential backoff
  - Support for multiple stores (Lidl, Biedronka)
  - JSON output format
  - Error handling and logging

#### Python AI Agent Sidecar (`sidecar-ai/`)
- **Technology**: Python with pandas, scikit-learn, numpy
- **Purpose**: AI-powered analysis of scraped promotion data
- **Features**:
  - Product categorization
  - Price analysis and trend detection
  - Store comparison
  - Best deals identification
  - Recommendation generation

### 2. Backend Integration

#### PromoScrapingAgent (`src/backend/agents/promo_scraping_agent.py`)
- **Integration**: Seamlessly integrated with existing agent system
- **Capabilities**:
  - Intent detection for user queries
  - Caching mechanism (6-hour cache duration)
  - Fallback to simulated data for testing
  - Multiple operation modes (scrape, analyze, compare, best deals)

#### Agent Factory Registration
- Registered in `src/backend/agents/agent_factory.py`
- Available as both "promo_scraping" and "PromoScraping" (case variations)

### 3. Tauri Integration

#### Rust Commands (`myappassistant-chat-frontend/src-tauri/src/lib.rs`)
- `run_scraper_sidecar()`: Executes the Node.js scraper
- `run_ai_analysis_sidecar()`: Executes the Python AI agent
- `monitor_promotions()`: Combined command for full monitoring workflow

#### Configuration (`myappassistant-chat-frontend/src-tauri/tauri.conf.json`)
- Sidecar binaries configured in `externalBin`
- Shell permissions enabled for sidecar execution
- Proper security scoping

### 4. Frontend Integration

#### PromotionsMonitor Component (`myappassistant-chat-frontend/src/components/promotions/PromotionsMonitor.tsx`)
- **Technology**: React with TypeScript
- **UI Framework**: Custom UI components with Lucide icons
- **Features**:
  - Real-time data fetching via Tauri commands
  - Loading states and error handling
  - Responsive design with summary cards
  - Store comparison visualization
  - Best deals display
  - Category analysis with progress bars
  - Recommendations section

#### Navigation Integration
- Added to sidebar navigation with shopping cart icon
- Polish translations included
- Breadcrumb navigation support
- Route: `/promotions`

## Technical Implementation Details

### 1. Scraper Configuration

```javascript
// Store-specific selectors for different websites
const STORES_CONFIG = {
  lidl: {
    name: 'Lidl',
    url: 'https://www.lidl.pl/pl/promocje',
    selectors: {
      promoItems: '.promo-item, .product-item, [data-testid*="promo"]',
      title: '.title, .product-name, h3, h4',
      discount: '.discount, .price-discount, .savings',
      // ... more selectors
    }
  },
  biedronka: {
    // Similar configuration for Biedronka
  }
};
```

### 2. AI Analysis Features

```python
class PromoAnalysisAgent:
    def analyze(self, scraped_data):
        # Product categorization
        self.product_categories = {
            'nabiał': ['mleko', 'ser', 'jogurt', 'masło'],
            'pieczywo': ['chleb', 'bułka', 'bagietka'],
            'mięso': ['kurczak', 'wieprzowina', 'wołowina'],
            # ... more categories
        }
        
        # Analysis methods
        - _generate_summary()
        - _analyze_categories()
        - _analyze_prices()
        - _compare_stores()
        - _detect_trends()
        - _generate_recommendations()
        - _find_best_deals()
```

### 3. Data Flow

1. **User Request** → Frontend calls `monitor_promotions()`
2. **Tauri Command** → Executes scraper sidecar
3. **Scraper** → Collects data from store websites
4. **AI Analysis** → Processes scraped data through AI sidecar
5. **Results** → Returns comprehensive analysis to frontend
6. **Display** → Renders results in beautiful UI

### 4. Caching Strategy

- **Cache Duration**: 6 hours per store
- **Cache Storage**: In-memory within PromoScrapingAgent
- **Cache Invalidation**: Automatic based on timestamp
- **Fallback**: Simulated data for testing/offline scenarios

## Features

### 1. Real-time Monitoring
- Live scraping of store promotion pages
- Automatic retry on failures
- Stealth browsing to avoid blocking

### 2. Intelligent Analysis
- Product categorization (dairy, bread, meat, etc.)
- Price trend analysis
- Store comparison metrics
- Best deals identification
- Personalized recommendations

### 3. User Interface
- **Summary Cards**: Total promotions, average discount, max discount, status
- **Store Comparison**: Side-by-side metrics for each store
- **Best Deals**: Top 5 promotions with highest discounts
- **Category Analysis**: Breakdown by product categories with progress bars
- **Recommendations**: AI-generated shopping advice

### 4. Error Handling
- Graceful degradation on scraping failures
- User-friendly error messages
- Retry mechanisms
- Fallback to cached data

## Security Considerations

### 1. Tauri Security
- Sidecar execution properly scoped
- No arbitrary command execution
- Sandboxed environment

### 2. Web Scraping Ethics
- Respectful scraping with delays
- Stealth techniques to avoid overwhelming servers
- User-agent rotation
- Rate limiting

### 3. Data Privacy
- No personal data collection
- Only public promotion information
- Local processing where possible

## Performance Optimizations

### 1. Caching
- 6-hour cache reduces redundant scraping
- In-memory storage for fast access
- Automatic cache invalidation

### 2. Parallel Processing
- Sidecar architecture allows parallel execution
- Async/await patterns throughout
- Non-blocking UI updates

### 3. Resource Management
- Proper cleanup of browser instances
- Memory-efficient data structures
- Optimized bundle sizes

## Monitoring and Observability

### 1. Logging
- Comprehensive logging in both sidecars
- Error tracking and reporting
- Performance metrics

### 2. Health Checks
- Sidecar availability monitoring
- Data freshness indicators
- System status reporting

## Future Enhancements

### 1. Additional Stores
- Easy to add new stores by updating configuration
- Modular selector system
- Store-specific optimization

### 2. Advanced Analytics
- Historical trend analysis
- Price prediction models
- Seasonal pattern recognition

### 3. User Preferences
- Personalized recommendations
- Favorite stores selection
- Custom category preferences

### 4. Notifications
- Price drop alerts
- New promotion notifications
- Weekly summary reports

## Testing

### 1. Unit Tests
- Agent functionality testing
- Data processing validation
- Error handling verification

### 2. Integration Tests
- Sidecar communication testing
- End-to-end workflow validation
- Performance benchmarking

### 3. Manual Testing
- UI/UX validation
- Cross-platform compatibility
- Real-world scenario testing

## Deployment

### 1. Build Process
- Sidecar binaries built with pkg (Node.js) and PyInstaller (Python)
- Tauri bundle includes all necessary binaries
- Cross-platform compatibility

### 2. Distribution
- Single executable package
- No external dependencies required
- Self-contained application

## Conclusion

The FoodSave AI promotion monitoring system provides a comprehensive solution for tracking grocery store promotions using modern web technologies and AI analysis. The modular sidecar architecture ensures maintainability and extensibility, while the beautiful UI provides an excellent user experience.

The system successfully integrates with the existing FoodSave AI ecosystem and follows all established patterns and conventions. It's ready for production use and can be easily extended with additional features and store support. 