#!/usr/bin/env python3
"""
Token Calculator Module
Provides accurate token estimation for different LLM models without heavy dependencies.
"""

import re
import json
import os
from typing import Dict, Tuple

class TokenCalculator:
    def __init__(self):
        self.pricing_data = self.load_pricing_data()
        
        # Model-specific token estimation rules based on research
        self.model_rules = {
            # Latest 2025 AI Models
            'claude-4-sonnet': {
                'chars_per_token': 3.4,
                'word_multiplier': 1.24,
                'encoding_overhead': 1.02
            },
            'claude-3-7-sonnet': {
                'chars_per_token': 3.5,
                'word_multiplier': 1.25,
                'encoding_overhead': 1.03
            },
            'gpt-4.5': {
                'chars_per_token': 3.6,
                'word_multiplier': 1.27,
                'encoding_overhead': 1.03
            },
            'gpt-o3-pro': {
                'chars_per_token': 3.5,
                'word_multiplier': 1.24,
                'encoding_overhead': 1.02
            },
            'gpt-o4-mini': {
                'chars_per_token': 4.0,
                'word_multiplier': 1.35,
                'encoding_overhead': 1.06
            },
            'gemini-2-5-pro': {
                'chars_per_token': 3.8,
                'word_multiplier': 1.3,
                'encoding_overhead': 1.05
            },
            'gemini-2-5-flash': {
                'chars_per_token': 4.2,
                'word_multiplier': 1.4,
                'encoding_overhead': 1.08
            },
            'grok-3': {
                'chars_per_token': 3.6,
                'word_multiplier': 1.26,
                'encoding_overhead': 1.03
            },
            'grok-3-mini': {
                'chars_per_token': 3.9,
                'word_multiplier': 1.32,
                'encoding_overhead': 1.05
            },
            'deepseek-r1': {
                'chars_per_token': 3.7,
                'word_multiplier': 1.28,
                'encoding_overhead': 1.04
            },
            
            # Existing models
            'gpt-4o': {
                'chars_per_token': 3.8,
                'word_multiplier': 1.3,
                'encoding_overhead': 1.05
            },
            'gpt-4-turbo': {
                'chars_per_token': 3.8,
                'word_multiplier': 1.3,
                'encoding_overhead': 1.05
            },
            'gpt-4.1': {
                'chars_per_token': 3.7,
                'word_multiplier': 1.28,
                'encoding_overhead': 1.04
            },
            'gpt-o3': {
                'chars_per_token': 3.6,
                'word_multiplier': 1.25,
                'encoding_overhead': 1.03
            },
            'claude-3-5-sonnet': {
                'chars_per_token': 3.5,
                'word_multiplier': 1.25,
                'encoding_overhead': 1.03
            },
            'gemini-2-0-flash': {
                'chars_per_token': 4.0,
                'word_multiplier': 1.35,
                'encoding_overhead': 1.08
            },
            'gpt-3.5-turbo': {
                'chars_per_token': 3.8,
                'word_multiplier': 1.3,
                'encoding_overhead': 1.05
            }
        }
    
    def load_pricing_data(self) -> Dict:
        """Load pricing data from JSON file"""
        try:
            pricing_file = os.path.join(os.path.dirname(__file__), '..', 'assets', 'pricing_data.json')
            with open(pricing_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            # Fallback pricing if file not found
            return {
                "models": {
                    "gpt-4o": {"input_cost_per_1k": 0.0025, "output_cost_per_1k": 0.01},
                    "claude-3-5-sonnet": {"input_cost_per_1k": 0.003, "output_cost_per_1k": 0.015}
                }
            }
    
    def estimate_tokens_basic(self, text: str) -> int:
        """Basic token estimation using word count * 1.3"""
        if not text:
            return 0
        word_count = len(text.split())
        return int(word_count * 1.3)
    
    def estimate_tokens_advanced(self, text: str, model: str = 'gpt-4o') -> int:
        """Advanced token estimation based on model-specific rules"""
        if not text:
            return 0
        
        # Get model rules or use default
        rules = self.model_rules.get(model, self.model_rules['gpt-4o'])
        
        # Character-based estimation
        char_count = len(text)
        char_based_tokens = char_count / rules['chars_per_token']
        
        # Word-based estimation
        words = self.count_words_advanced(text)
        word_based_tokens = words * rules['word_multiplier']
        
        # Take average and apply encoding overhead
        avg_tokens = (char_based_tokens + word_based_tokens) / 2
        final_tokens = int(avg_tokens * rules['encoding_overhead'])
        
        return max(final_tokens, 1)  # Minimum 1 token
    
    def count_words_advanced(self, text: str) -> int:
        """Advanced word counting that handles punctuation better"""
        # Remove extra whitespace and split
        words = re.findall(r'\b\w+\b|[^\w\s]', text)
        return len(words)
    
    def estimate_cost(self, token_count: int, model: str = 'gpt-4o', output_ratio: float = 0.1) -> Tuple[float, Dict]:
        """
        Estimate cost for given token count and model
        output_ratio: estimated ratio of output tokens to input tokens (default 10%)
        """
        if model not in self.pricing_data.get('models', {}):
            model = 'gpt-4o'  # fallback
        
        model_data = self.pricing_data['models'][model]
        
        input_tokens = token_count
        estimated_output_tokens = int(token_count * output_ratio)
        
        input_cost = (input_tokens / 1000) * model_data['input_cost_per_1k']
        output_cost = (estimated_output_tokens / 1000) * model_data['output_cost_per_1k']
        total_cost = input_cost + output_cost
        
        return total_cost, {
            'input_tokens': input_tokens,
            'estimated_output_tokens': estimated_output_tokens,
            'input_cost': input_cost,
            'output_cost': output_cost,
            'total_cost': total_cost,
            'model': model_data['name']
        }
    
    def get_available_models(self) -> Dict[str, str]:
        """Get list of available models with their display names"""
        models = {}
        for model_id, model_data in self.pricing_data.get('models', {}).items():
            models[model_id] = model_data.get('name', model_id)
        return models
    
    def format_cost(self, cost: float) -> str:
        """Format cost for display"""
        if cost < 0.01:
            return f"${cost:.4f}"
        elif cost < 0.1:
            return f"${cost:.3f}"
        else:
            return f"${cost:.2f}"
    
    def get_model_info(self, model: str) -> Dict:
        """Get detailed model information"""
        return self.pricing_data.get('models', {}).get(model, {})

# Global instance
token_calc = TokenCalculator()

def estimate_tokens(text: str, model: str = 'gpt-4o') -> int:
    """Quick function to estimate tokens"""
    return token_calc.estimate_tokens_advanced(text, model)

def estimate_cost(token_count: int, model: str = 'gpt-4o') -> Tuple[float, Dict]:
    """Quick function to estimate cost"""
    return token_calc.estimate_cost(token_count, model) 