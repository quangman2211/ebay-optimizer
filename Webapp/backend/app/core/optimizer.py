import re
from typing import List, Dict, Tuple, Optional
from app.core.config import settings
from app.core.strategies.optimization_strategies import (
    OptimizationContext, 
    OptimizationType,
    IOptimizationStrategy
)
from app.core.strategies.export_strategies import (
    ExportContext,
    ExportFormat
)


class EbayOptimizer:
    def __init__(self, optimization_strategy: OptimizationType = OptimizationType.BASIC):
        # Legacy attributes for backward compatibility
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'
        }
        
        self.power_words = {
            'new', 'authentic', 'genuine', 'original', 'oem', 'premium', 'pro',
            'limited', 'edition', 'rare', 'vintage', 'sealed', 'mint', 'perfect'
        }
        
        # Strategy pattern implementation
        self.optimization_context = OptimizationContext()
        self.optimization_context.set_strategy(optimization_strategy)
        
        self.export_context = ExportContext()
        
    def optimize_title(
        self, 
        title: str, 
        category: str, 
        keywords: List[str] = None,
        item_specifics: Dict[str, str] = None,
        strategy_type: OptimizationType = None
    ) -> Tuple[str, float]:
        """
        Optimize eBay listing title using strategy pattern
        Returns: (optimized_title, score)
        """
        # Use strategy pattern for optimization
        if strategy_type:
            self.optimization_context.set_strategy(strategy_type)
        
        if not keywords:
            keywords = []
        
        result = self.optimization_context.get_strategy().optimize_title(
            title, category, keywords
        )
        
        return result["optimized_title"], result["title_score"]
    
    def optimize_description(
        self,
        title: str,
        description: str,
        category: str,
        item_specifics: Dict[str, str] = None,
        keywords: List[str] = None,
        strategy_type: OptimizationType = None
    ) -> str:
        """
        Generate optimized description using strategy pattern
        """
        # Use strategy pattern for optimization
        if strategy_type:
            self.optimization_context.set_strategy(strategy_type)
        
        if not keywords:
            keywords = []
        
        result = self.optimization_context.get_strategy().optimize_description(
            description, title, keywords
        )
        
        return result["optimized_description"]
    
    def generate_keywords(
        self,
        title: str,
        description: str,
        category: str,
        strategy_type: OptimizationType = None
    ) -> List[str]:
        """
        Generate relevant keywords using strategy pattern
        """
        # Use strategy pattern for keyword generation
        if strategy_type:
            self.optimization_context.set_strategy(strategy_type)
        
        return self.optimization_context.get_strategy().generate_keywords(
            title, category, description
        )
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text into words"""
        # Remove special characters but keep alphanumeric
        text = re.sub(r'[^\w\s-]', ' ', text)
        words = text.split()
        return [w for w in words if w]
    
    def _build_title(self, words: List[str]) -> str:
        """Build title from words list, respecting character limit"""
        title_parts = []
        current_length = 0
        
        for word in words:
            # Check if adding this word would exceed limit
            word_length = len(word) + (1 if title_parts else 0)  # +1 for space
            if current_length + word_length <= settings.MAX_TITLE_LENGTH:
                title_parts.append(word)
                current_length += word_length
            else:
                break
        
        return ' '.join(title_parts)
    
    def _calculate_title_score(
        self,
        title: str,
        category: str,
        keywords: List[str] = None
    ) -> float:
        """Calculate optimization score for title (0-100)"""
        score = 0.0
        
        # Length score (20 points)
        title_length = len(title)
        if 60 <= title_length <= 80:
            score += 20
        elif 40 <= title_length < 60:
            score += 15
        elif 20 <= title_length < 40:
            score += 10
        
        # Keyword presence (30 points)
        title_lower = title.lower()
        
        # Check for power words (15 points)
        power_word_count = sum(1 for word in self.power_words if word in title_lower)
        score += min(power_word_count * 5, 15)
        
        # Check for category keywords (15 points)
        category_keywords = settings.EBAY_CATEGORIES.get(category.lower(), [])
        category_match = sum(1 for kw in category_keywords if kw in title_lower)
        score += min(category_match * 5, 15)
        
        # User keywords (20 points)
        if keywords:
            keyword_match = sum(1 for kw in keywords if kw.lower() in title_lower)
            score += min(keyword_match * 4, 20)
        
        # Readability (15 points)
        if not any(char * 3 in title for char in title):  # No repeated characters
            score += 5
        if title[0].isupper():  # Starts with capital
            score += 5
        if not title.isupper():  # Not all caps
            score += 5
        
        # Structure (15 points)
        if '-' in title or '|' in title:  # Has separators
            score += 5
        if not re.search(r'\d{5,}', title):  # No long number strings
            score += 5
        if len(self._tokenize(title)) >= 3:  # At least 3 words
            score += 5
        
        return min(score, 100.0)
    
    def _clean_description(self, description: str) -> str:
        """Clean and format description text"""
        # Remove excessive whitespace
        description = re.sub(r'\s+', ' ', description)
        
        # Remove excessive punctuation
        description = re.sub(r'[!]{2,}', '!', description)
        description = re.sub(r'[.]{2,}', '.', description)
        
        # Break into paragraphs if too long
        if len(description) > 500:
            words = description.split()
            paragraphs = []
            current = []
            current_length = 0
            
            for word in words:
                current.append(word)
                current_length += len(word) + 1
                
                if current_length > 400 and word.endswith('.'):
                    paragraphs.append(' '.join(current))
                    current = []
                    current_length = 0
            
            if current:
                paragraphs.append(' '.join(current))
            
            description = '\n\n'.join(paragraphs)
        
        return description
    
    def optimize_listing(
        self,
        listing_data: Dict[str, str],
        strategy_type: OptimizationType = OptimizationType.BASIC
    ) -> Dict[str, any]:
        """
        Optimize complete listing using strategy pattern
        """
        self.optimization_context.set_strategy(strategy_type)
        return self.optimization_context.optimize_listing(listing_data)
    
    def export_data(
        self,
        data: List[Dict[str, any]],
        export_format: ExportFormat = ExportFormat.CSV,
        filename: str = None
    ) -> Dict[str, any]:
        """
        Export data using strategy pattern
        """
        self.export_context.set_strategy(export_format)
        return self.export_context.export_data(data, filename)
    
    def get_available_optimization_strategies(self) -> List[Dict[str, str]]:
        """
        Get available optimization strategies
        """
        return self.optimization_context.get_available_strategies()
    
    def get_available_export_formats(self) -> List[Dict[str, str]]:
        """
        Get available export formats
        """
        return self.export_context.get_available_formats()
    
    def set_optimization_strategy(self, strategy_type: OptimizationType):
        """
        Change optimization strategy
        """
        self.optimization_context.set_strategy(strategy_type)
    
    def set_export_format(self, export_format: ExportFormat):
        """
        Change export format
        """
        self.export_context.set_strategy(export_format)