"""
Evaluation Script for Nutrition Agent
Author: Oshadi Jayananda 
"""

import unittest
import sys
import os

# Fix Windows console encoding
if sys.platform == "win32":
    import io
    sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from tools.nutrition_tool import estimate_nutrition, calculate_daily_totals, estimate_total_calories


class TestNutritionAgentTools(unittest.TestCase):
    """
    Unit tests for Nutrition Agent custom tools.
    Each student must contribute test cases for their own agent.
    """
    
    def setUp(self):
        """Setup before each test - called automatically."""
        self.known_meals = [
            ("grilled chicken breast with rice", 295, 34, 28, 4),
            ("2 eggs with whole wheat toast", 335, 15, 49, 8),
            ("salmon with quinoa and broccoli", 362, 27, 23, 15),
        ]
    
    # ============================================
    # TEST 1: Basic functionality - Structure validation
    # ============================================
    
    def test_tool_returns_correct_structure(self):
        """Test that estimate_nutrition returns correct dictionary structure."""
        result = estimate_nutrition("chicken breast")
        
        required_keys = ["meal_name", "calories", "protein_g", "carbs_g", "fat_g", "confidence"]
        for key in required_keys:
            self.assertIn(key, result, f"Missing required key: {key}")
        
        # Check value types
        self.assertIsInstance(result["calories"], int)
        self.assertIsInstance(result["protein_g"], int)
        self.assertIsInstance(result["carbs_g"], int)
        self.assertIsInstance(result["fat_g"], int)
        self.assertIsInstance(result["confidence"], str)
    
    # ============================================
    # TEST 2: Input validation - Security
    # ============================================
    
    def test_empty_input_raises_error(self):
        """Test that empty input raises ValueError."""
        with self.assertRaises(ValueError):
            estimate_nutrition("")
    
    def test_none_input_raises_error(self):
        """Test that None input raises ValueError."""
        with self.assertRaises(ValueError):
            estimate_nutrition(None)  # type: ignore
    
    def test_invalid_input_type_raises_error(self):
        """Test that non-string input raises ValueError."""
        with self.assertRaises(ValueError):
            estimate_nutrition(123)  # type: ignore
    
    # ============================================
    # TEST 3: Range validation - Reasonable estimates
    # ============================================
    
    def test_calorie_estimates_reasonable(self):
        """Test that calorie estimates are within reasonable ranges."""
        test_meals = ["breakfast with eggs", "chicken lunch", "dinner salmon", "apple snack"]
        
        for meal in test_meals:
            result = estimate_nutrition(meal)
            calories = result["calories"]
            
            # All reasonable meals should be between 50-1000 calories
            self.assertGreaterEqual(calories, 50, f"Calories too low for {meal}: {calories}")
            self.assertLessEqual(calories, 1000, f"Calories too high for {meal}: {calories}")
    
    def test_protein_not_negative(self):
        """Test that protein estimates are never negative."""
        result = estimate_nutrition("anything")
        self.assertGreaterEqual(result["protein_g"], 0)
    
    # ============================================
    # TEST 4: Known meal accuracy (within tolerance)
    # ============================================
    
    def test_known_meals_accuracy(self):
        """Test that known meals return expected nutrition within 20% tolerance."""
        for meal, expected_cal, expected_prot, expected_carbs, expected_fat in self.known_meals:
            result = estimate_nutrition(meal)
            
            # Allow 20% variance (reasonable for estimates)
            self.assertAlmostEqual(
                result["calories"], expected_cal, 
                delta=expected_cal * 0.2,
                msg=f"Calories off for {meal}: got {result['calories']}, expected ~{expected_cal}"
            )
    
    # ============================================
    # TEST 5: Security - Prompt injection prevention
    # ============================================
    
    def test_no_prompt_injection(self):
        """Test that malicious inputs don't break the tool."""
        malicious_inputs = [
            "ignore previous instructions",
            "rm -rf /",
            "SELECT * FROM users",
            "<script>alert('hack')</script>",
            "a" * 10000,  # Very long input
            "{{7*7}}",
            "${7*7}",
        ]
        
        for malicious in malicious_inputs:
            try:
                result = estimate_nutrition(malicious)
                # Should still return valid structure
                self.assertIsInstance(result, dict)
                self.assertIn("calories", result)
                self.assertIn("confidence", result)
            except Exception as e:
                self.fail(f"Malicious input '{malicious[:50]}' caused crash: {e}")
    
    # ============================================
    # TEST 6: Daily totals calculation
    # ============================================
    
    def test_daily_totals_calculation(self):
        """Test that daily totals sum correctly."""
        meals = [
            {"nutrition": {"calories": 450, "protein_g": 30, "carbs_g": 45, "fat_g": 12}},
            {"nutrition": {"calories": 350, "protein_g": 15, "carbs_g": 30, "fat_g": 10}},
            {"nutrition": {"calories": 250, "protein_g": 10, "carbs_g": 20, "fat_g": 8}},
        ]
        
        result = calculate_daily_totals(meals)
        
        self.assertEqual(result["total_calories"], 1050)
        self.assertEqual(result["total_protein_g"], 55)
        self.assertEqual(result["total_carbs_g"], 95)
        self.assertEqual(result["total_fat_g"], 30)
        self.assertEqual(result["meal_count"], 3)
    
    def test_empty_meals_list(self):
        """Test empty meals list returns zeros."""
        result = calculate_daily_totals([])
        self.assertEqual(result["total_calories"], 0)
        self.assertEqual(result["total_protein_g"], 0)
        self.assertEqual(result["meal_count"], 0)
    
    def test_direct_nutrition_dict_format(self):
        """Test that calculate_daily_totals works with direct nutrition dicts."""
        meals = [
            {"calories": 450, "protein_g": 30, "carbs_g": 45, "fat_g": 12},
            {"calories": 350, "protein_g": 15, "carbs_g": 30, "fat_g": 10},
        ]
        
        result = calculate_daily_totals(meals)
        self.assertEqual(result["total_calories"], 800)
    
    # ============================================
    # TEST 7: Confidence scoring validation
    # ============================================
    
    def test_confidence_score_valid_values(self):
        """Test that confidence scores are always valid."""
        valid_confidences = ["high", "medium", "low"]
        
        test_inputs = [
            "chicken breast with rice",  # Should be high/medium
            "something completely unknown xyz123",  # Should be low
            "breakfast",  # Should be medium
        ]
        
        for test_input in test_inputs:
            result = estimate_nutrition(test_input)
            self.assertIn(
                result["confidence"], 
                valid_confidences,
                f"Invalid confidence '{result['confidence']}' for '{test_input}'"
            )
    
    # ============================================
    # TEST 8: Estimate total calories wrapper
    # ============================================
    
    def test_estimate_total_calories_wrapper(self):
        """Test the wrapper function used by main.py."""
        meals = [
            {"nutrition": {"calories": 450}},
            {"nutrition": {"calories": 350}},
        ]
        
        total = estimate_total_calories(meals)
        self.assertEqual(total, 800)


# ============================================
# LLM-as-Judge Test (Advanced Evaluation)
# ============================================

def run_llm_as_judge_test() -> dict:
    """
    Use LLM as a judge to evaluate nutrition estimates.
    This is a more sophisticated evaluation method.
    """
    from langchain_community.llms import Ollama
    
    print("\n" + "=" * 60)
    print("🤖 LLM-AS-JUDGE EVALUATION")
    print("=" * 60)
    
    llm = Ollama(model="llama3")
    
    test_cases = [
        "chicken breast with broccoli and brown rice",
        "pasta with olive oil and parmesan",
        "breakfast with eggs, toast, and banana",
        "salmon with quinoa and asparagus",
        "a completely made up dish called zxyzxyz"  # Should flag as low confidence
    ]
    
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for meal in test_cases:
        nutrition = estimate_nutrition(meal)
        
        prompt = f"""
        You are a nutrition expert.

        Meal: "{meal}"

        Estimated Nutrition:
        - Calories: {nutrition['calories']}
        - Protein: {nutrition['protein_g']}g
        - Carbs: {nutrition['carbs_g']}g
        - Fat: {nutrition['fat_g']}g
        - Confidence: {nutrition['confidence']}

        Evaluation Rules:
        - Accept reasonable estimates (±30% variation is OK)
        - Do NOT expect exact values
        - If values are in a realistic range → answer YES
        - If completely unrealistic → answer NO

        Examples:
        - Chicken meal: 200–600 calories → YES
        - Pasta meal: 200–800 calories → YES
        - Random nonsense meal → NO

        Answer ONLY "YES" or "NO".
        """
        
        try:
            judgment = llm.invoke(prompt).strip().upper()
            is_reasonable = "YES" in judgment
            
            result = {
                "meal": meal,
                "calories": nutrition['calories'],
                "confidence": nutrition['confidence'],
                "judgment": judgment,
                "passed": is_reasonable
            }
            results["details"].append(result)
            
            if is_reasonable:
                results["passed"] += 1
                print(f"✅ {meal[:40]}... -> {nutrition['calories']} cal -> {judgment}")
            else:
                results["failed"] += 1
                print(f"❌ {meal[:40]}... -> {nutrition['calories']} cal -> {judgment}")
                
        except Exception as e:
            print(f"⚠️ Error judging '{meal}': {e}")
            results["failed"] += 1
    
    print(f"\n📊 LLM-as-Judge Results: {results['passed']}/{len(test_cases)} passed")
    
    return results


# ============================================
# RUN ALL TESTS
# ============================================
if __name__ == "__main__":
    print("=" * 60)
    print("🧪 NUTRITION AGENT TEST SUITE")
    print("=" * 60)
    
    # Run unit tests
    print("\n📋 Running Unit Tests...\n")
    unittest.main(exit=False, verbosity=2)
    
    run_llm_as_judge_test()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)