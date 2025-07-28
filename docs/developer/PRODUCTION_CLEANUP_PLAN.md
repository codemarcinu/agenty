# PRODUCTION CLEANUP PLAN - REMOVE ALL TEST/MOCK DATA

## 🎯 Objective
Remove all test data, mock data, sample data, and development fixtures to make the system production-ready with real data only.

## 📋 Files to Remove/Modify

### 1. TEST DATA FILES (DELETE)
- `tests/fixtures/test_data.json` - Test intent recognition data
- `tests/fixtures/test_receipt.jpg` - Test receipt image
- `data/sample_user_profile.json` - Sample user profile
- `src/backend/core/seed_data.json` - Seed data for database

### 2. MOCK DATA IN CODE (MODIFY)
- `src/backend/agents/promo_scraping_agent.py` - Remove `_simulate_scraped_data()` method
- `examples/demo_*.py` files - Remove sample data creation functions
- `test_*.py` files - Remove mock data and test fixtures

### 3. ENVIRONMENT CONFIGURATION (MODIFY)
- Remove `LOAD_TEST_DATA=true` from all environment files
- Remove `SEED_DATABASE=true` from all environment files
- Set `TESTING_MODE=false` in production

### 4. DATABASE SEEDING (DISABLE)
- Modify `src/backend/core/seed_data.py` to not load test data
- Update `src/backend/app_factory.py` to skip seeding in production

### 5. CONFIGURATION FILES (UPDATE)
- Update Docker Compose files to remove test data loading
- Update development scripts to not load test data

## 🚀 Implementation Steps

### Step 1: Remove Test Data Files
```bash
rm tests/fixtures/test_data.json
rm tests/fixtures/test_receipt.jpg
rm data/sample_user_profile.json
rm src/backend/core/seed_data.json
```

### Step 2: Disable Database Seeding
- Modify seed_data.py to return early in production
- Update app_factory.py to skip seeding

### Step 3: Remove Mock Data from Agents
- Remove `_simulate_scraped_data()` from promo_scraping_agent.py
- Clean up demo files

### Step 4: Update Environment Configuration
- Set production environment variables
- Remove test data loading flags

### Step 5: Clean Database
- Clear existing test data from database
- Ensure only real user data remains

## ⚠️ Safety Checks
- Backup current data before cleanup
- Verify no production data is accidentally removed
- Test system functionality after cleanup
- Ensure all features work with real data only

## 📊 Expected Results
- System runs with real user data only
- No test/mock data in database
- Production-ready configuration
- Clean, professional system state 