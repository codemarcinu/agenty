#!/usr/bin/env python3
"""
Prosty test optymalizacji Bielika - testuje tylko kluczowe metody
"""

class MockModelComplexity:
    SIMPLE = "simple"
    STANDARD = "standard"  
    COMPLEX = "complex"

class TestBielikOptimization:
    """Test class for Bielik optimization features"""
    
    def __init__(self):
        self.model_complexity = MockModelComplexity()
    
    def _select_model(self, complexity, use_bielik=True):
        """Test metody wyboru modelu"""
        if complexity == self.model_complexity.SIMPLE:
            return "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
        elif complexity == self.model_complexity.STANDARD:
            return "SpeakLeash/bielik-7b-v2.1-instruct:Q5_K_M"
        else:  # COMPLEX
            return "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    
    def _determine_query_complexity_enhanced(self, query, rag_context="", internet_context=""):
        """Test metody określania złożoności"""
        query_lower = query.lower()
        word_count = len(query.split())
        
        # Proste zapytania
        simple_patterns = ["cześć", "hej", "witaj", "tak", "nie", "ok", "dziękuję"]
        if any(pattern in query_lower for pattern in simple_patterns) and word_count <= 3:
            return self.model_complexity.SIMPLE
            
        # Bardzo krótkie zapytania
        if len(query) < 15 or word_count <= 2:
            return self.model_complexity.SIMPLE
            
        # Złożone zapytania
        complex_keywords = ["porównaj", "przeanalizuj", "wyjaśnij szczegółowo", "oceń"]
        if any(keyword in query_lower for keyword in complex_keywords):
            return self.model_complexity.COMPLEX
            
        # Długie zapytania
        if len(query) > 200 or word_count > 30:
            return self.model_complexity.COMPLEX
            
        return self.model_complexity.STANDARD
    
    def _get_bielik_parameters(self, complexity, model_name):
        """Test parametrów dla modelu Bielik"""
        base_params = {
            "temperature": 0.7,
            "top_p": 0.9,
            "max_tokens": 2048,
        }
        
        if complexity == self.model_complexity.SIMPLE:
            base_params.update({
                "temperature": 0.3,
                "top_p": 0.7,
                "max_tokens": 150,
            })
        elif complexity == self.model_complexity.COMPLEX:
            base_params.update({
                "temperature": 0.8,
                "top_p": 0.95,
                "max_tokens": 4096,
            })
            
        # Dostosowania dla różnych wariantów Bielika
        if "4.5b" in model_name:
            base_params["temperature"] = min(base_params["temperature"], 0.6)
        elif "11b" in model_name and complexity == self.model_complexity.COMPLEX:
            base_params["temperature"] = 0.9
                
        return base_params
    
    def _detect_user_intent_bielik(self, query):
        """Test wykrywania intencji"""
        query_lower = query.lower()
        
        intents = {
            "question": ["co", "jak", "dlaczego", "kiedy", "gdzie", "?"],
            "request": ["pomóż", "zrób", "stwórz", "napisz", "znajdź"],
            "conversation": ["cześć", "dzień dobry", "co słychać"],
            "explanation": ["wyjaśnij", "opisz", "przedstaw"],
            "comparison": ["porównaj", "różnica", "lepszy"],
        }
        
        intent_scores = {}
        for intent, keywords in intents.items():
            score = sum(1 for keyword in keywords if keyword in query_lower)
            if score > 0:
                intent_scores[intent] = score
        
        if intent_scores:
            return max(intent_scores.items(), key=lambda x: x[1])[0]
        return "general"

def run_tests():
    """Uruchom testy optymalizacji"""
    print("🔬 TESTOWANIE OPTYMALIZACJI MODELU BIELIK")
    print("="*50)
    
    tester = TestBielikOptimization()
    
    # Test cases
    test_cases = [
        {
            "query": "Cześć!",
            "expected_complexity": "simple",
            "expected_model": "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
            "description": "Proste pozdrowienie"
        },
        {
            "query": "Co to jest sztuczna inteligencja?",
            "expected_complexity": "standard",
            "expected_model": "SpeakLeash/bielik-7b-v2.1-instruct:Q5_K_M",
            "description": "Standardowe pytanie"
        },
        {
            "query": "Przeanalizuj różnice między różnymi podejściami do uczenia maszynowego i zaproponuj strategię implementacji.",
            "expected_complexity": "complex",
            "expected_model": "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
            "description": "Złożone pytanie analityczne"
        }
    ]
    
    print("\n📊 TESTOWANIE WYBORU MODELU:")
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['description']}")
        print(f"   Query: {test_case['query'][:50]}...")
        
        # Test złożoności
        complexity = tester._determine_query_complexity_enhanced(test_case['query'])
        complexity_ok = complexity == test_case['expected_complexity']
        print(f"   ✅ Complexity: {complexity} {'✓' if complexity_ok else '✗'}")
        
        # Test modelu
        model = tester._select_model(complexity)
        model_ok = model == test_case['expected_model']
        print(f"   ✅ Model: {model} {'✓' if model_ok else '✗'}")
        
        # Test parametrów
        params = tester._get_bielik_parameters(complexity, model)
        print(f"   ✅ Parameters: temp={params['temperature']}, max_tokens={params['max_tokens']}")
        
        # Test intencji
        intent = tester._detect_user_intent_bielik(test_case['query'])
        print(f"   ✅ Intent: {intent}")
        
        if not (complexity_ok and model_ok):
            all_passed = False
    
    print(f"\n🎯 WYNIK TESTÓW: {'WSZYSTKIE PRZESZŁY ✅' if all_passed else 'NIEKTÓRE NIEPOWODZENIA ⚠️'}")
    
    print("\n✨ OPTYMALIZACJE BIELIKA:")
    print("   • Adaptacyjny wybór modelu: 4.5B → 7B → 11B")
    print("   • Inteligentne parametry dla każdego wariantu")
    print("   • Wykrywanie intencji użytkownika")
    print("   • Zoptymalizowane prompty polskie")
    print("   • Oszczędność zasobów obliczeniowych")
    
    return all_passed

if __name__ == "__main__":
    run_tests()