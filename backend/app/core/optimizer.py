import re
from typing import List, Dict, Tuple, Optional
from app.core.config import settings


class EbayOptimizer:
    def __init__(self):
        self.stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'up', 'about', 'into', 'through', 'during'
        }
        
        self.power_words = {
            'new', 'authentic', 'genuine', 'original', 'oem', 'premium', 'pro',
            'limited', 'edition', 'rare', 'vintage', 'sealed', 'mint', 'perfect'
        }
        
    def optimize_title(
        self, 
        title: str, 
        category: str, 
        keywords: List[str] = None,
        item_specifics: Dict[str, str] = None
    ) -> Tuple[str, float]:
        """
        Optimize eBay listing title
        Returns: (optimized_title, score)
        """
        # Clean and tokenize
        title_words = self._tokenize(title)
        
        # Get category-specific keywords
        category_keywords = settings.EBAY_CATEGORIES.get(category.lower(), [])
        
        # Extract important words
        important_words = []
        
        # Add item specifics (brand, model, etc.)
        if item_specifics:
            for key in category_keywords:
                if key in item_specifics and item_specifics[key]:
                    important_words.append(item_specifics[key])
        
        # Add power words if present
        for word in title_words:
            if word.lower() in self.power_words:
                important_words.append(word)
        
        # Add user-provided keywords
        if keywords:
            important_words.extend([k for k in keywords if k not in important_words])
        
        # Add remaining words (excluding stop words)
        for word in title_words:
            if (word.lower() not in self.stop_words and 
                word not in important_words and 
                len(word) > 2):
                important_words.append(word)
        
        # Build optimized title
        optimized_title = self._build_title(important_words)
        
        # Calculate score
        score = self._calculate_title_score(optimized_title, category, keywords)
        
        return optimized_title, score
    
    def optimize_description(
        self,
        title: str,
        description: str,
        category: str,
        item_specifics: Dict[str, str] = None
    ) -> str:
        """
        Generate optimized description with bullet points and SEO keywords
        """
        sections = []
        
        # Title section
        sections.append(f"✨ {title.upper()} ✨\n")
        
        # Key features section
        if item_specifics:
            sections.append("📋 KEY FEATURES:")
            for key, value in item_specifics.items():
                if value:
                    sections.append(f"• {key.title()}: {value}")
            sections.append("")
        
        # Original description (cleaned)
        if description:
            cleaned_desc = self._clean_description(description)
            sections.append("📝 DESCRIPTION:")
            sections.append(cleaned_desc)
            sections.append("")
        
        # Benefits section
        sections.append("✅ WHY BUY FROM US:")
        sections.append("• Fast & Secure Shipping")
        sections.append("• 100% Authentic Products")
        sections.append("• Customer Satisfaction Guaranteed")
        sections.append("• Professional Packaging")
        sections.append("")
        
        # Shipping info
        sections.append("📦 SHIPPING:")
        sections.append("• Same day handling")
        sections.append("• Tracking provided")
        sections.append("• Carefully packaged")
        
        return "\n".join(sections)
    
    def generate_keywords(
        self,
        title: str,
        description: str,
        category: str
    ) -> List[str]:
        """
        Generate relevant keywords for the listing
        """
        keywords = set()
        
        # Extract from title
        title_words = self._tokenize(title)
        for word in title_words:
            if len(word) > 3 and word.lower() not in self.stop_words:
                keywords.add(word.lower())
        
        # Add category-specific keywords
        category_keywords = settings.EBAY_CATEGORIES.get(category.lower(), [])
        keywords.update(category_keywords)
        
        # Extract from description
        if description:
            desc_words = self._tokenize(description)
            # Get most frequent meaningful words
            word_freq = {}
            for word in desc_words:
                if len(word) > 3 and word.lower() not in self.stop_words:
                    word_lower = word.lower()
                    word_freq[word_lower] = word_freq.get(word_lower, 0) + 1
            
            # Add top frequent words
            sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
            for word, _ in sorted_words[:10]:
                keywords.add(word)
        
        return list(keywords)
    
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