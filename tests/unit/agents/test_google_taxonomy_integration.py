"""
Unit tests for Google Product Taxonomy Integration
==================================================

Tests the integration of Google Product Taxonomy with FoodSave AI.
Zgodny z .cursorrules - comprehensive testing, async operations.

Author: @backend-lead
Version: 2025-01-06
"""

from unittest.mock import patch

import pytest

from backend.core.google_taxonomy_enhancer import (
    GoogleTaxonomyEnhancer,
    TaxonomyCategory,
    get_google_taxonomy_enhancer,
)
from backend.core.product_categorizer import ProductCategorizer


class TestTaxonomyCategory:
    """Tests for TaxonomyCategory dataclass"""

    def test_taxonomy_category_creation(self):
        """Test creating a TaxonomyCategory instance"""
        category = TaxonomyCategory(
            id="412",
            path="Food, Beverages & Tobacco > Food Items > Dairy Products",
            name_en="Dairy Products",
            name_pl="Nabiał",
        )

        assert category.id == "412"
        assert (
            category.path == "Food, Beverages & Tobacco > Food Items > Dairy Products"
        )
        assert category.name_en == "Dairy Products"
        assert category.name_pl == "Nabiał"
        assert category.level == 2
        assert category.is_food_related is True

    def test_food_related_detection(self):
        """Test automatic food-related detection"""
        # Food category
        food_category = TaxonomyCategory(
            id="413", path="Food, Beverages & Tobacco > Beverages", name_en="Beverages"
        )
        assert food_category.is_food_related is True

        # Non-food category
        non_food_category = TaxonomyCategory(
            id="166", path="Apparel & Accessories > Clothing", name_en="Clothing"
        )
        assert non_food_category.is_food_related is False


class TestGoogleTaxonomyEnhancer:
    """Tests for GoogleTaxonomyEnhancer class"""

    @pytest.fixture
    def enhancer(self):
        """Create a test enhancer instance"""
        return GoogleTaxonomyEnhancer("Google_Product_Taxonomy.txt")

    @pytest.fixture
    def mock_taxonomy_file(self, tmp_path):
        """Create a mock taxonomy file for testing"""
        taxonomy_file = tmp_path / "test_taxonomy.txt"
        taxonomy_content = """# Google_Product_Taxonomy_Version: 2021-09-21
412 - Food, Beverages & Tobacco
413 - Food, Beverages & Tobacco > Beverages
414 - Food, Beverages & Tobacco > Beverages > Alcoholic Beverages
422 - Food, Beverages & Tobacco > Food Items
423 - Food, Beverages & Tobacco > Food Items > Dairy Products
424 - Food, Beverages & Tobacco > Food Items > Dairy Products > Milk
425 - Food, Beverages & Tobacco > Food Items > Dairy Products > Cheese
166 - Apparel & Accessories
167 - Apparel & Accessories > Clothing
"""
        taxonomy_file.write_text(taxonomy_content)
        return str(taxonomy_file)

    def test_enhancer_initialization(self, mock_taxonomy_file):
        """Test enhancer initialization with taxonomy file"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        assert len(enhancer.categories) > 0
        assert len(enhancer.food_categories) > 0
        assert len(enhancer.polish_translations) > 0

        # Check that food categories are properly identified
        food_category_ids = list(enhancer.food_categories.keys())
        assert "412" in food_category_ids  # Food, Beverages & Tobacco
        assert "413" in food_category_ids  # Beverages
        assert "422" in food_category_ids  # Food Items

    def test_category_loading(self, mock_taxonomy_file):
        """Test loading categories from taxonomy file"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Check specific categories
        dairy_category = enhancer.categories.get("423")
        assert dairy_category is not None
        assert dairy_category.name_en == "Dairy Products"
        assert (
            dairy_category.path
            == "Food, Beverages & Tobacco > Food Items > Dairy Products"
        )
        assert dairy_category.level == 2
        assert dairy_category.is_food_related is True

    def test_polish_translations(self, mock_taxonomy_file):
        """Test Polish translations loading"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Check some translations
        assert enhancer.polish_translations.get("Dairy Products") == "Nabiał"
        assert enhancer.polish_translations.get("Beverages") == "Napoje"
        assert enhancer.polish_translations.get("Food Items") == "Produkty spożywcze"

    def test_category_scoring(self, mock_taxonomy_file):
        """Test category scoring algorithm"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Get a dairy category
        dairy_category = enhancer.categories.get("423")
        assert dairy_category is not None

        # Test scoring with dairy-related text
        score = enhancer._calculate_category_score(dairy_category, "milk cheese yogurt")
        assert score > 0.1  # Should have some relevance

        # Test scoring with non-dairy text
        score = enhancer._calculate_category_score(dairy_category, "shoes clothing")
        assert score < 0.5  # Should have low relevance

    def test_search_categories(self, mock_taxonomy_file):
        """Test category search functionality"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Search for dairy-related categories
        results = enhancer.search_categories("dairy milk cheese", limit=5)
        assert len(results) > 0

        # Check that results are sorted by score
        scores = [result["score"] for result in results]
        assert scores == sorted(scores, reverse=True)

        # Check that food-related categories are prioritized
        food_results = [r for r in results if r["is_food_related"]]
        assert len(food_results) > 0

    def test_get_food_categories_stats(self, mock_taxonomy_file):
        """Test food categories statistics"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        stats = enhancer.get_food_categories_stats()

        assert "total_categories" in stats
        assert "food_categories" in stats
        assert "food_percentage" in stats
        assert "polish_translations" in stats

        assert stats["total_categories"] > 0
        assert stats["food_categories"] > 0
        assert 0 <= stats["food_percentage"] <= 100

    def test_get_category_hierarchy(self, mock_taxonomy_file):
        """Test category hierarchy retrieval"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Get hierarchy for Food Items
        hierarchy = enhancer.get_category_hierarchy("422", max_depth=2)

        assert hierarchy["id"] == "422"
        assert hierarchy["name_en"] == "Food Items"
        assert hierarchy["level"] == 1
        assert "children" in hierarchy

        # Should have dairy products as child
        children_names = [child["name_en"] for child in hierarchy["children"]]
        assert "Dairy Products" in children_names

    def test_batch_categorize_products(self, mock_taxonomy_file):
        """Test batch product categorization"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        products = [
            {"name": "milk", "description": "fresh dairy milk"},
            {"name": "cheese", "description": "aged cheddar cheese"},
            {"name": "bread", "description": "whole grain bread"},
        ]

        categorized = enhancer.batch_categorize_products(products)

        assert len(categorized) == 3

        # Check that products have category information
        for product in categorized:
            assert "gpt_category" in product
            assert "gpt_category_pl" in product
            assert "gpt_id" in product
            assert "gpt_path" in product
            assert "gpt_confidence" in product
            assert "gpt_method" in product
            assert "is_food_related" in product

    @pytest.mark.asyncio
    async def test_categorize_product_advanced(self, mock_taxonomy_file):
        """Test advanced product categorization"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Test categorization of dairy product
        result = await enhancer.categorize_product_advanced(
            "fresh milk", "organic dairy milk"
        )

        assert result is not None
        assert "gpt_id" in result
        assert "gpt_path" in result
        assert "name_en" in result
        assert "name_pl" in result
        assert "confidence" in result
        assert "method" in result
        assert "is_food_related" in result

        # Should be food-related
        assert result["is_food_related"] is True
        assert result["confidence"] > 0.0

    def test_fallback_category(self, mock_taxonomy_file):
        """Test fallback category handling"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        fallback = enhancer._get_fallback_food_category()

        assert fallback.id == "412"
        assert fallback.path == "Food, Beverages & Tobacco > Food Items"
        assert fallback.name_en == "Food Items"
        assert fallback.is_food_related is True

    def test_error_category(self, mock_taxonomy_file):
        """Test error category handling"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        error_cat = enhancer._get_error_category()

        assert error_cat["gpt_id"] == "error"
        assert error_cat["name_en"] == "Unknown"
        assert error_cat["name_pl"] == "Nieznana"
        assert error_cat["confidence"] == 0.0
        assert error_cat["method"] == "error"
        assert error_cat["is_food_related"] is False


class TestProductCategorizerIntegration:
    """Tests for ProductCategorizer integration with Google Taxonomy"""

    @pytest.fixture
    def mock_categories_file(self, tmp_path):
        """Create a mock categories file"""
        categories_file = tmp_path / "test_categories.json"
        categories_data = {
            "version": "2021-09-21",
            "description": "Test categories",
            "categories": [
                {
                    "id": "1",
                    "gpt_id": "423",
                    "gpt_path": "Food, Beverages & Tobacco > Food Items > Dairy Products",
                    "name_pl": "Nabiał",
                    "name_en": "Dairy Products",
                    "keywords": ["mleko", "ser", "jogurt"],
                    "parent_id": None,
                },
                {
                    "id": "2",
                    "gpt_id": "424",
                    "gpt_path": "Food, Beverages & Tobacco > Food Items > Dairy Products > Milk",
                    "name_pl": "Mleko",
                    "name_en": "Milk",
                    "keywords": ["mleko", "milk"],
                    "parent_id": None,
                },
            ],
        }
        categories_file.write_text(str(categories_data).replace("'", '"'))
        return str(categories_file)

    @pytest.mark.asyncio
    async def test_categorizer_with_google_taxonomy(
        self, mock_categories_file, mock_taxonomy_file
    ):
        """Test ProductCategorizer integration with Google Taxonomy"""
        with patch(
            "backend.core.product_categorizer.ProductCategorizer.__init__"
        ) as mock_init:
            mock_init.return_value = None

            categorizer = ProductCategorizer()
            categorizer.categories_file = mock_categories_file
            categorizer.categories = [
                {
                    "id": "1",
                    "gpt_id": "423",
                    "gpt_path": "Food, Beverages & Tobacco > Food Items > Dairy Products",
                    "name_pl": "Nabiał",
                    "name_en": "Dairy Products",
                    "keywords": ["mleko", "ser", "jogurt"],
                    "parent_id": None,
                }
            ]
            categorizer.google_taxonomy_enhancer = GoogleTaxonomyEnhancer(
                mock_taxonomy_file
            )

            # Test categorization
            result = await categorizer.categorize_product_with_bielik("fresh milk")

            assert result is not None
            assert "name_pl" in result
            assert "confidence" in result
            assert "method" in result

    @pytest.mark.asyncio
    async def test_google_taxonomy_singleton(self):
        """Test singleton pattern for Google Taxonomy Enhancer"""
        # First call
        enhancer1 = await get_google_taxonomy_enhancer()

        # Second call should return the same instance
        enhancer2 = await get_google_taxonomy_enhancer()

        assert enhancer1 is enhancer2


class TestGoogleTaxonomyPerformance:
    """Performance tests for Google Taxonomy integration"""

    @pytest.mark.asyncio
    async def test_batch_categorization_performance(self, mock_taxonomy_file):
        """Test performance of batch categorization"""
        enhancer = GoogleTaxonomyEnhancer(mock_taxonomy_file)

        # Create test products
        products = [
            {"name": f"product_{i}", "description": f"description_{i}"}
            for i in range(100)
        ]

        # Measure categorization time
        import time

        start_time = time.time()

        categorized = enhancer.batch_categorize_products(products)

        end_time = time.time()
        processing_time = end_time - start_time

        assert len(categorized) == 100
        assert processing_time < 5.0  # Should complete within 5 seconds

        # Check that all products have category information
        for product in categorized:
            assert "gpt_category" in product
            assert "gpt_confidence" in product

    def test_memory_usage(self, mock_taxonomy_file):
        """Test memory usage of taxonomy enhancer"""
        import os

        import psutil

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Create enhancer
        GoogleTaxonomyEnhancer(mock_taxonomy_file)

        memory_after_init = process.memory_info().rss
        memory_increase = memory_after_init - initial_memory

        # Memory increase should be reasonable (less than 50MB)
        assert memory_increase < 50 * 1024 * 1024  # 50MB in bytes


if __name__ == "__main__":
    pytest.main([__file__])
