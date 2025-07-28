# Enhanced Tests Documentation

## 📋 Overview

This document provides comprehensive documentation for all tests covering the enhanced "Add → Receipt Analysis" implementation. The test suite includes unit tests, integration tests, performance tests, and end-to-end tests for the new features.

## 🎯 Test Coverage

### Backend Tests

#### 1. Unit Tests (`tests/unit/`)

##### `test_ocr_advanced_preprocessing.py`
**Purpose**: Tests the advanced OCR preprocessing pipeline with contour detection, perspective correction, and adaptive thresholding.

**Key Test Cases**:
- `test_enhanced_contour_detection()` - Tests receipt contour detection with OpenCV
- `test_contour_detection_fallback_to_bounding_rect()` - Tests fallback to minimal bounding rectangle
- `test_perspective_correction()` - Tests perspective correction using homography
- `test_adaptive_thresholding_clahe()` - Tests CLAHE adaptive thresholding
- `test_300_dpi_scaling()` - Tests 300 DPI scaling for optimal OCR
- `test_contrast_enhancement()` - Tests contrast enhancement
- `test_sharpness_enhancement()` - Tests sharpness enhancement
- `test_lstm_engine_configuration()` - Tests LSTM engine configuration
- `test_process_image_with_advanced_preprocessing()` - Tests full preprocessing pipeline
- `test_preprocessing_error_handling()` - Tests error handling during preprocessing
- `test_metadata_tracking()` - Tests preprocessing metadata tracking
- `test_confidence_distribution_calculation()` - Tests confidence distribution analysis
- `test_processing_time_tracking()` - Tests processing time measurement
- `test_polish_receipt_text_recognition()` - Tests Polish text recognition
- `test_image_quality_analysis()` - Tests image quality analysis
- `test_preprocessing_pipeline_integration()` - Tests complete pipeline integration

**Dependencies**:
- OpenCV (cv2)
- PIL (Pillow)
- NumPy
- pytest
- unittest.mock

#### 2. Integration Tests (`tests/integration/`)

##### `test_receipt_agent_workflow.py`
**Purpose**: Tests the complete agent-based workflow including ReceiptImportAgent, ReceiptValidationAgent, and ReceiptCategorizationAgent.

**Key Test Cases**:
- `test_receipt_import_agent_success()` - Tests successful OCR processing
- `test_receipt_import_agent_ocr_failure()` - Tests OCR failure handling
- `test_receipt_validation_agent_success()` - Tests receipt validation
- `test_receipt_validation_agent_invalid_receipt()` - Tests invalid receipt handling
- `test_receipt_validation_agent_nip_validation()` - Tests NIP validation
- `test_receipt_categorization_agent_success()` - Tests product categorization
- `test_receipt_categorization_agent_fallback_to_dictionary()` - Tests fallback categorization
- `test_complete_workflow_success()` - Tests complete workflow
- `test_workflow_validation_failure()` - Tests validation failure in workflow
- `test_workflow_categorization_failure()` - Tests categorization failure in workflow
- `test_agent_error_handling_and_recovery()` - Tests error handling and recovery
- `test_agent_metadata_tracking()` - Tests metadata tracking across agents
- `test_agent_performance_monitoring()` - Tests performance monitoring
- `test_agent_concurrent_processing()` - Tests concurrent processing
- `test_agent_memory_management()` - Tests memory management
- `test_agent_configuration_validation()` - Tests agent configuration
- `test_agent_response_format_consistency()` - Tests response format consistency

**Dependencies**:
- FastAPI TestClient
- pytest-asyncio
- unittest.mock

#### 3. Performance Tests (`tests/performance/`)

##### `test_ocr_performance_enhanced.py`
**Purpose**: Tests performance characteristics of the enhanced OCR preprocessing pipeline.

**Key Test Cases**:
- `test_contour_detection_performance()` - Tests contour detection performance across image sizes
- `test_perspective_correction_performance()` - Tests perspective correction performance
- `test_adaptive_thresholding_performance()` - Tests adaptive thresholding performance
- `test_300_dpi_scaling_performance()` - Tests 300 DPI scaling performance
- `test_full_preprocessing_pipeline_performance()` - Tests complete pipeline performance
- `test_agent_workflow_performance()` - Tests agent workflow performance
- `test_memory_usage_during_preprocessing()` - Tests memory usage during preprocessing
- `test_concurrent_processing_performance()` - Tests concurrent processing performance
- `test_large_batch_processing_performance()` - Tests large batch processing
- `test_accuracy_vs_performance_tradeoff()` - Tests accuracy vs performance tradeoffs
- `test_resource_utilization_under_load()` - Tests resource utilization under load

**Performance Benchmarks**:
- Contour detection: < 1.0s for 3200x2400 images
- Perspective correction: < 0.5s for 1600x1200 images
- Adaptive thresholding: < 0.3s for 1600x1200 images
- 300 DPI scaling: < 0.2s for 1600x1200 images
- Full pipeline: < 2.0s for 800x600 images
- Memory usage: < 100MB increase during processing
- Concurrent processing: 2-3x speedup over sequential

**Dependencies**:
- psutil (for memory monitoring)
- time
- asyncio

### Frontend Tests

#### 1. E2E Tests (`myappassistant-chat-frontend/tests/e2e/`)

##### `receipt-wizard-enhanced.spec.ts`
**Purpose**: Tests the enhanced ReceiptWizard component with single-screen wizard, real-time feedback, and inline editing.

**Key Test Cases**:
- `should load receipt wizard page successfully()` - Tests page loading
- `should display single-screen wizard interface()` - Tests single-screen layout
- `should handle image upload with immediate preview()` - Tests immediate image preview
- `should show contour detection overlay()` - Tests contour detection visualization
- `should display real-time quality warnings()` - Tests quality warning system
- `should show compression feedback()` - Tests compression feedback
- `should process receipt and display results()` - Tests receipt processing
- `should allow inline editing of receipt items()` - Tests inline editing
- `should save inline edits successfully()` - Tests edit saving
- `should cancel inline edits()` - Tests edit cancellation
- `should handle multiple item edits()` - Tests multiple item editing
- `should validate inline edit inputs()` - Tests input validation
- `should show processing progress()` - Tests progress indicators
- `should handle processing errors gracefully()` - Tests error handling
- `should provide keyboard shortcuts for editing()` - Tests keyboard shortcuts
- `should maintain responsive design on different screen sizes()` - Tests responsive design
- `should support drag and drop file upload()` - Tests drag and drop
- `should show accessibility features()` - Tests accessibility
- `should handle large file uploads()` - Tests large file handling
- `should support batch processing()` - Tests batch processing

**Dependencies**:
- Playwright
- TypeScript
- React Testing Library

## 🚀 Test Runner

### `run_enhanced_tests.py`
**Purpose**: Comprehensive test runner that executes all enhanced tests with detailed reporting.

**Features**:
- Automated test execution for all test categories
- Detailed performance reporting
- Coverage analysis
- Error logging and debugging
- JSON result export
- Configurable test selection

**Usage**:
```bash
# Run all tests
python tests/run_enhanced_tests.py

# Run without E2E tests
python tests/run_enhanced_tests.py --no-e2e

# Run without performance tests
python tests/run_enhanced_tests.py --no-performance

# Run only unit tests
python tests/run_enhanced_tests.py --unit-only

# Run only integration tests
python tests/run_enhanced_tests.py --integration-only
```

**Output**:
- Console report with test results
- JSON file with detailed results (`enhanced_test_results.json`)
- Coverage reports (HTML and JSON)
- Performance metrics

## 📊 Test Metrics

### Coverage Requirements
- **Unit Tests**: > 90% coverage for OCR preprocessing
- **Integration Tests**: > 85% coverage for agent workflow
- **Performance Tests**: All performance benchmarks must pass
- **E2E Tests**: All user workflows must pass

### Performance Benchmarks
- **OCR Processing**: < 2.0s for standard receipt images
- **Agent Workflow**: < 5.0s for complete processing
- **Memory Usage**: < 100MB increase during processing
- **Concurrent Processing**: 2-3x speedup over sequential
- **Frontend Response**: < 200ms for UI interactions

### Quality Gates
- All unit tests must pass
- All integration tests must pass
- Performance benchmarks must be met
- E2E tests must pass on all supported browsers
- Code coverage must meet minimum requirements

## 🔧 Test Environment Setup

### Backend Dependencies
```bash
pip install pytest pytest-asyncio pytest-cov
pip install opencv-python pillow numpy
pip install fastapi[testing] httpx
```

### Frontend Dependencies
```bash
cd myappassistant-chat-frontend
npm install --save-dev @playwright/test
npx playwright install
```

### Environment Variables
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
export TEST_ENV=enhanced
export OCR_DEBUG=true
```

## 🐛 Debugging Tests

### Common Issues

1. **OpenCV Import Errors**
   ```bash
   pip install opencv-python-headless
   ```

2. **Tesseract Not Found**
   ```bash
   # Ubuntu/Debian
   sudo apt install tesseract-ocr tesseract-ocr-pol
   
   # macOS
   brew install tesseract tesseract-lang
   ```

3. **Playwright Browser Issues**
   ```bash
   npx playwright install --force
   ```

4. **Memory Issues**
   ```bash
   # Increase memory limit for Node.js
   export NODE_OPTIONS="--max-old-space-size=4096"
   ```

### Debug Mode
```bash
# Run tests with debug output
python tests/run_enhanced_tests.py --debug

# Run specific test with verbose output
pytest tests/unit/test_ocr_advanced_preprocessing.py::TestOCRAdvancedPreprocessing::test_enhanced_contour_detection -v -s
```

## 📈 Continuous Integration

### GitHub Actions Workflow
```yaml
name: Enhanced Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-asyncio pytest-cov
      - name: Run enhanced tests
        run: python tests/run_enhanced_tests.py
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: enhanced-tests
        name: Enhanced Tests
        entry: python tests/run_enhanced_tests.py --unit-only
        language: system
        pass_filenames: false
```

## 📝 Test Data

### Sample Receipt Images
- `tests/fixtures/test_receipt.jpg` - Standard receipt for testing
- `tests/fixtures/low_quality_receipt.jpg` - Low quality receipt for error testing
- `tests/fixtures/large_receipt.jpg` - Large receipt for performance testing

### Mock Data
- OCR text samples with Polish characters
- Validation results with different confidence levels
- Categorization results with product mappings

## 🔄 Test Maintenance

### Regular Tasks
1. **Weekly**: Update test data with new receipt formats
2. **Monthly**: Review and update performance benchmarks
3. **Quarterly**: Update test dependencies
4. **Annually**: Comprehensive test suite review

### Adding New Tests
1. Follow existing naming conventions
2. Include proper docstrings and comments
3. Add to appropriate test category
4. Update test runner if needed
5. Update documentation

### Test Data Management
- Keep test data minimal and focused
- Use realistic but anonymized data
- Version control test data
- Document data sources and formats

## 📚 Additional Resources

### Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [OpenCV Python Documentation](https://docs.opencv.org/4.x/d6/d00/tutorial_py_root.html)

### Best Practices
- Write tests that are independent and repeatable
- Use descriptive test names
- Mock external dependencies
- Test both success and failure scenarios
- Include performance benchmarks
- Maintain good test coverage

### Troubleshooting
- Check test logs for detailed error messages
- Verify environment setup
- Ensure all dependencies are installed
- Check file permissions and paths
- Validate test data integrity 