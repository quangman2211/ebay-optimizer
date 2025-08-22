"""
Optimization Strategy Pattern Implementation
Open/Closed Principle: Open for extension, closed for modification
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from enum import Enum
import re


class OptimizationType(str, Enum):
    """Types of optimization strategies"""
    BASIC = "basic"
    ADVANCED = "advanced"
    SEO_FOCUSED = "seo_focused"
    CONVERSION_FOCUSED = "conversion_focused"
    AI_POWERED = "ai_powered"


class IOptimizationStrategy(ABC):
    """
    Strategy interface for optimization algorithms
    Following OCP: New strategies can be added without modifying existing code
    """
    
    @abstractmethod
    def optimize_title(self, title: str, category: str, keywords: List[str]) -> Dict[str, Any]:
        """Optimize product title"""
        pass
    
    @abstractmethod
    def optimize_description(self, description: str, title: str, keywords: List[str]) -> Dict[str, Any]:
        """Optimize product description"""
        pass
    
    @abstractmethod
    def generate_keywords(self, title: str, category: str, description: str = None) -> List[str]:
        """Generate relevant keywords"""
        pass
    
    @abstractmethod
    def calculate_score(self, title: str, description: str, keywords: List[str]) -> float:
        """Calculate optimization score (0-100)"""
        pass
    
    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Return strategy name"""
        pass
    
    @property
    @abstractmethod
    def strategy_type(self) -> OptimizationType:
        """Return strategy type"""
        pass


class BasicOptimizationStrategy(IOptimizationStrategy):
    """
    Basic optimization strategy
    Focus on fundamental SEO principles
    """
    
    def __init__(self):
        self.max_title_length = 80
        self.power_words = [
            "new", "premium", "authentic", "genuine", "original", "professional",
            "quality", "durable", "lightweight", "compact", "portable", "wireless",
            "fast", "quick", "instant", "easy", "simple", "secure", "safe",
            "bestseller", "popular", "trending", "limited", "exclusive", "rare"
        ]
        
        self.stop_words = {
            "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being"
        }
    
    def optimize_title(self, title: str, category: str, keywords: List[str]) -> Dict[str, Any]:
        """Basic title optimization"""
        original_title = title.strip()
        
        # Clean and normalize
        cleaned_title = self._clean_title(original_title)
        
        # Add power words strategically
        optimized_title = self._add_power_words(cleaned_title, keywords)
        
        # Add category if not present
        optimized_title = self._add_category_keywords(optimized_title, category)
        
        # Ensure length limit
        optimized_title = self._truncate_title(optimized_title)
        
        # Calculate improvement score
        score = self._calculate_title_score(optimized_title, keywords)
        
        return {
            "original_title": original_title,
            "optimized_title": optimized_title,
            "title_score": score,
            "improvements": self._get_title_improvements(original_title, optimized_title),
            "strategy_used": self.strategy_name
        }
    
    def optimize_description(self, description: str, title: str, keywords: List[str]) -> Dict[str, Any]:
        """Basic description optimization"""
        
        # Template-based description
        optimized_desc = self._create_structured_description(description, title, keywords)
        
        return {
            "original_description": description,
            "optimized_description": optimized_desc,
            "description_score": 75.0,  # Basic template score
            "improvements": ["Added structured format", "Included key features", "Added call-to-action"],
            "strategy_used": self.strategy_name
        }
    
    def generate_keywords(self, title: str, category: str, description: str = None) -> List[str]:
        """Generate basic keywords from title and category"""
        keywords = set()
        
        # Extract from title
        title_words = self._extract_words(title)
        keywords.update(title_words)
        
        # Add category-specific keywords
        category_keywords = self._get_category_keywords(category)
        keywords.update(category_keywords)
        
        # Remove stop words
        keywords = keywords - self.stop_words
        
        return list(keywords)[:20]  # Limit to 20 keywords
    
    def calculate_score(self, title: str, description: str, keywords: List[str]) -> float:
        """Calculate basic optimization score"""
        score = 0.0
        
        # Title scoring (40% weight)
        title_score = self._calculate_title_score(title, keywords)
        score += title_score * 0.4
        
        # Description scoring (30% weight)  
        desc_score = self._calculate_description_score(description, keywords)
        score += desc_score * 0.3
        
        # Keyword relevance (30% weight)
        keyword_score = self._calculate_keyword_score(title, description, keywords)
        score += keyword_score * 0.3
        
        return min(100.0, max(0.0, score))
    
    @property
    def strategy_name(self) -> str:
        return "Basic SEO Optimization"
    
    @property
    def strategy_type(self) -> OptimizationType:
        return OptimizationType.BASIC
    
    # Helper methods
    def _clean_title(self, title: str) -> str:
        """Clean and normalize title"""
        # Remove extra spaces and special characters
        cleaned = re.sub(r'\s+', ' ', title)
        cleaned = re.sub(r'[^\w\s\-]', '', cleaned)
        return cleaned.strip()
    
    def _add_power_words(self, title: str, keywords: List[str]) -> str:
        """Add relevant power words"""
        words = title.split()
        
        # Add "New" if not present and appropriate
        if not any(word.lower() in ["new", "used", "refurbished"] for word in words):
            words.insert(0, "New")
        
        return " ".join(words)
    
    def _add_category_keywords(self, title: str, category: str) -> str:
        """Add category-specific keywords"""
        category_keywords = self._get_category_keywords(category)
        
        for keyword in category_keywords[:2]:  # Add max 2 category keywords
            if keyword.lower() not in title.lower():
                title = f"{title} {keyword}"
        
        return title
    
    def _truncate_title(self, title: str) -> str:
        """Ensure title doesn't exceed length limit"""
        if len(title) <= self.max_title_length:
            return title
        
        words = title.split()
        truncated = ""
        
        for word in words:
            if len(truncated + " " + word) <= self.max_title_length:
                if truncated:
                    truncated += " " + word
                else:
                    truncated = word
            else:
                break
        
        return truncated
    
    def _calculate_title_score(self, title: str, keywords: List[str]) -> float:
        """Calculate title optimization score"""
        score = 50.0  # Base score
        
        # Length optimization
        if 40 <= len(title) <= 70:
            score += 15
        elif 30 <= len(title) <= 80:
            score += 10
        
        # Keyword inclusion
        title_lower = title.lower()
        keyword_matches = sum(1 for kw in keywords if kw.lower() in title_lower)
        score += min(20, keyword_matches * 5)
        
        # Power words
        power_word_count = sum(1 for pw in self.power_words if pw in title_lower)
        score += min(10, power_word_count * 3)
        
        # No excessive capitalization
        if not title.isupper():
            score += 5
        
        return min(100.0, score)
    
    def _calculate_description_score(self, description: str, keywords: List[str]) -> float:
        """Calculate description optimization score"""
        if not description:
            return 20.0
        
        score = 40.0  # Base score
        
        # Length check
        if 200 <= len(description) <= 1000:
            score += 15
        elif len(description) > 100:
            score += 10
        
        # Keyword density
        desc_lower = description.lower()
        keyword_matches = sum(1 for kw in keywords if kw.lower() in desc_lower)
        score += min(25, keyword_matches * 3)
        
        # Structure indicators
        if "•" in description or "-" in description:
            score += 10  # Bullet points
        
        if any(word in desc_lower for word in ["features", "benefits", "shipping"]):
            score += 10  # Good structure words
        
        return min(100.0, score)
    
    def _calculate_keyword_score(self, title: str, description: str, keywords: List[str]) -> float:
        """Calculate keyword relevance score"""
        if not keywords:
            return 50.0
        
        combined_text = f"{title} {description}".lower()
        
        relevant_keywords = sum(1 for kw in keywords if kw.lower() in combined_text)
        relevance_ratio = relevant_keywords / len(keywords)
        
        return relevance_ratio * 100
    
    def _get_title_improvements(self, original: str, optimized: str) -> List[str]:
        """Generate list of improvements made"""
        improvements = []
        
        if len(optimized) > len(original):
            improvements.append("Added relevant keywords")
        
        if "New" in optimized and "New" not in original:
            improvements.append("Added condition keyword")
        
        if len(optimized) <= 80:
            improvements.append("Optimized length for eBay")
        
        return improvements or ["Basic formatting applied"]
    
    def _create_structured_description(self, description: str, title: str, keywords: List[str]) -> str:
        """Create structured description template"""
        
        # Extract brand if possible
        brand = self._extract_brand(title)
        
        template = f"""✨ {title.upper()} ✨

📋 KEY FEATURES:"""
        
        if brand:
            template += f"\n• Brand: {brand}"
        
        # Add key features from keywords
        for keyword in keywords[:5]:
            if keyword.lower() not in ["new", "used", "the", "and"]:
                template += f"\n• {keyword.title()}"
        
        template += f"""

📝 DESCRIPTION:
{description or "High-quality product with excellent features and performance."}

✅ WHY BUY FROM US:
• Fast & Secure Shipping
• 100% Authentic Products
• Customer Satisfaction Guaranteed
• Professional Packaging

📦 SHIPPING:
• Same day handling
• Tracking provided
• Carefully packaged"""
        
        return template
    
    def _extract_words(self, text: str) -> List[str]:
        """Extract meaningful words from text"""
        words = re.findall(r'\b\w+\b', text.lower())
        return [word for word in words if len(word) > 2]
    
    def _extract_brand(self, title: str) -> Optional[str]:
        """Try to extract brand from title"""
        # Common brand patterns
        common_brands = [
            "Apple", "Samsung", "Sony", "LG", "Dell", "HP", "Lenovo", "Nike",
            "Adidas", "Canon", "Nikon", "Microsoft", "Google", "Amazon"
        ]
        
        title_words = title.split()
        for word in title_words:
            if word in common_brands:
                return word
        
        return None
    
    def _get_category_keywords(self, category: str) -> List[str]:
        """Get category-specific keywords"""
        category_map = {
            "electronics": ["electronic", "digital", "tech", "gadget"],
            "clothing": ["apparel", "fashion", "wear", "style"],
            "home": ["household", "indoor", "domestic", "living"],
            "automotive": ["car", "vehicle", "auto", "motor"],
            "collectibles": ["collectible", "vintage", "rare", "antique"],
            "books": ["book", "literature", "reading", "educational"],
            "toys": ["toy", "kids", "children", "play"],
            "sports": ["sport", "fitness", "athletic", "outdoor"],
            "jewelry": ["jewelry", "accessory", "fashion", "elegant"],
            "health": ["health", "wellness", "care", "medical"]
        }
        
        return category_map.get(category.lower(), ["quality", "premium"])


class AdvancedOptimizationStrategy(IOptimizationStrategy):
    """
    Advanced optimization strategy
    Includes competitor analysis and advanced SEO techniques
    """
    
    def __init__(self):
        self.basic_strategy = BasicOptimizationStrategy()
        self.advanced_keywords = {
            "electronics": ["wireless", "bluetooth", "HD", "4K", "smart", "digital", "portable"],
            "clothing": ["comfortable", "stylish", "breathable", "durable", "trendy", "casual"],
            "home": ["modern", "elegant", "space-saving", "energy-efficient", "decorative"]
        }
    
    def optimize_title(self, title: str, category: str, keywords: List[str]) -> Dict[str, Any]:
        """Advanced title optimization with competitive analysis"""
        
        # Start with basic optimization
        basic_result = self.basic_strategy.optimize_title(title, category, keywords)
        
        # Apply advanced enhancements
        advanced_title = self._apply_advanced_title_techniques(
            basic_result["optimized_title"], category, keywords
        )
        
        # Calculate advanced score
        advanced_score = self._calculate_advanced_title_score(advanced_title, keywords, category)
        
        return {
            "original_title": title,
            "optimized_title": advanced_title,
            "title_score": advanced_score,
            "improvements": basic_result["improvements"] + [
                "Applied advanced SEO techniques",
                "Added category-specific power words",
                "Optimized keyword positioning"
            ],
            "strategy_used": self.strategy_name
        }
    
    def optimize_description(self, description: str, title: str, keywords: List[str]) -> Dict[str, Any]:
        """Advanced description with SEO optimization"""
        
        # Create advanced structured description
        optimized_desc = self._create_advanced_description(description, title, keywords)
        
        return {
            "original_description": description,
            "optimized_description": optimized_desc,
            "description_score": 85.0,
            "improvements": [
                "Added advanced SEO structure",
                "Included emotional triggers",
                "Optimized for conversions",
                "Added trust signals"
            ],
            "strategy_used": self.strategy_name
        }
    
    def generate_keywords(self, title: str, category: str, description: str = None) -> List[str]:
        """Advanced keyword generation with semantic analysis"""
        
        # Get basic keywords
        basic_keywords = self.basic_strategy.generate_keywords(title, category, description)
        
        # Add advanced category-specific keywords
        advanced_kw = self.advanced_keywords.get(category.lower(), [])
        
        # Combine and prioritize
        all_keywords = list(set(basic_keywords + advanced_kw))
        
        # Add long-tail keywords
        long_tail = self._generate_long_tail_keywords(title, category)
        all_keywords.extend(long_tail)
        
        return all_keywords[:25]  # Return top 25 keywords
    
    def calculate_score(self, title: str, description: str, keywords: List[str]) -> float:
        """Advanced scoring with additional factors"""
        
        # Get basic score
        basic_score = self.basic_strategy.calculate_score(title, description, keywords)
        
        # Add advanced scoring factors
        advanced_bonus = 0.0
        
        # Keyword positioning bonus
        title_words = title.lower().split()
        if keywords and keywords[0].lower() in title_words[:3]:
            advanced_bonus += 5  # Primary keyword in first 3 words
        
        # Description structure bonus
        if description and ("✨" in description or "📋" in description):
            advanced_bonus += 10  # Structured format
        
        # Category relevance bonus
        category_relevance = self._calculate_category_relevance(title, description, keywords)
        advanced_bonus += category_relevance * 0.1
        
        return min(100.0, basic_score + advanced_bonus)
    
    @property
    def strategy_name(self) -> str:
        return "Advanced SEO Optimization"
    
    @property
    def strategy_type(self) -> OptimizationType:
        return OptimizationType.ADVANCED
    
    # Advanced helper methods
    def _apply_advanced_title_techniques(self, title: str, category: str, keywords: List[str]) -> str:
        """Apply advanced title optimization techniques"""
        
        words = title.split()
        
        # Front-load the most important keyword
        if keywords:
            primary_keyword = keywords[0]
            if primary_keyword.lower() not in " ".join(words[:2]).lower():
                # Move primary keyword to front
                words = [primary_keyword] + [w for w in words if w.lower() != primary_keyword.lower()]
        
        # Add category-specific advanced keywords
        category_advanced = self.advanced_keywords.get(category.lower(), [])
        for adv_kw in category_advanced[:1]:  # Add one advanced keyword
            if adv_kw.lower() not in title.lower():
                words.append(adv_kw)
        
        # Reconstruct title with length limit
        optimized = " ".join(words)
        if len(optimized) > 80:
            optimized = optimized[:77] + "..."
        
        return optimized
    
    def _calculate_advanced_title_score(self, title: str, keywords: List[str], category: str) -> float:
        """Calculate advanced title score"""
        
        # Start with basic score
        score = self.basic_strategy._calculate_title_score(title, keywords)
        
        # Advanced bonuses
        title_lower = title.lower()
        
        # Primary keyword positioning
        if keywords and keywords[0].lower() in title_lower.split()[:2]:
            score += 5
        
        # Category keyword inclusion
        category_kw = self.advanced_keywords.get(category.lower(), [])
        category_matches = sum(1 for kw in category_kw if kw.lower() in title_lower)
        score += min(10, category_matches * 3)
        
        # Title readability (not too keyword-stuffed)
        word_count = len(title.split())
        if 6 <= word_count <= 12:
            score += 5
        
        return min(100.0, score)
    
    def _create_advanced_description(self, description: str, title: str, keywords: List[str]) -> str:
        """Create advanced description with conversion optimization"""
        
        # Extract brand and key features
        brand = self.basic_strategy._extract_brand(title)
        
        template = f"""🌟 {title.upper()} - PREMIUM QUALITY 🌟

🚀 TRANSFORM YOUR EXPERIENCE with this exceptional product!

📋 KEY FEATURES & BENEFITS:
"""
        
        if brand:
            template += f"• ⭐ BRAND: {brand} - Trusted Quality Guarantee\n"
        
        # Add feature benefits (not just features)
        feature_benefits = {
            "wireless": "Enjoy complete freedom of movement",
            "portable": "Take it anywhere with ease", 
            "durable": "Built to last for years of reliable use",
            "lightweight": "Easy to carry and handle",
            "smart": "Intelligent features for enhanced performance"
        }
        
        for keyword in keywords[:4]:
            benefit = feature_benefits.get(keyword.lower())
            if benefit:
                template += f"• ✅ {keyword.upper()}: {benefit}\n"
            else:
                template += f"• ✅ {keyword.upper()}: Premium quality and performance\n"
        
        template += f"""
📝 DETAILED DESCRIPTION:
{description or "Experience premium quality and exceptional performance with this carefully selected product. Designed with attention to detail and built to exceed your expectations."}

🎯 WHY THOUSANDS CHOOSE US:
• 🚚 LIGHTNING-FAST Shipping (Same Day Processing)
• 🛡️ 100% AUTHENTIC Products - No Counterfeits!
• ⭐ 99.8% Customer Satisfaction Rating
• 💎 Premium Packaging & Care
• 🔒 Secure Payment & Privacy Protection
• 🎉 BONUS: Free Customer Support

📦 SHIPPING & DELIVERY:
• 📍 Ships from certified facility
• 📱 Real-time tracking included
• 🎁 Professional gift packaging available
• 🌍 International shipping options

💰 SPECIAL OFFER: Order now and join thousands of satisfied customers!

⚡ Limited stock - Don't miss out on this amazing deal!"""
        
        return template
    
    def _generate_long_tail_keywords(self, title: str, category: str) -> List[str]:
        """Generate long-tail keyword phrases"""
        
        long_tail = []
        
        # Extract main product type
        title_words = title.lower().split()
        
        # Category-specific long-tail patterns
        if category.lower() == "electronics":
            patterns = [
                "best {} for home",
                "professional {} wireless",
                "{} with warranty",
                "premium {} sale"
            ]
        elif category.lower() == "clothing":
            patterns = [
                "comfortable {} wear",
                "stylish {} fashion",
                "{} for all seasons",
                "designer {} collection"
            ]
        else:
            patterns = [
                "high quality {}",
                "best {} deal",
                "professional {}",
                "premium {}"
            ]
        
        # Generate long-tail keywords
        for word in title_words[:3]:  # Use first 3 words
            if len(word) > 3:  # Skip short words
                for pattern in patterns[:2]:  # Use first 2 patterns
                    long_tail.append(pattern.format(word))
        
        return long_tail[:5]  # Return max 5 long-tail keywords
    
    def _calculate_category_relevance(self, title: str, description: str, keywords: List[str]) -> float:
        """Calculate how relevant content is to its category"""
        
        combined_text = f"{title} {description}".lower()
        
        # Count category-relevant terms
        relevance_score = 0
        total_possible = len(keywords) * 2  # Each keyword can appear in title and description
        
        for keyword in keywords:
            if keyword.lower() in combined_text:
                relevance_score += 1
        
        return (relevance_score / total_possible * 100) if total_possible > 0 else 50.0


class OptimizationContext:
    """
    Context class for strategy pattern implementation
    Following OCP: Easy to add new strategies without modifying existing code
    """
    
    def __init__(self, strategy: IOptimizationStrategy = None):
        self._strategy = strategy or BasicOptimizationStrategy()
        self._available_strategies = {
            OptimizationType.BASIC: BasicOptimizationStrategy,
            OptimizationType.ADVANCED: AdvancedOptimizationStrategy,
            # Future strategies can be added here without modifying existing code
        }
    
    def set_strategy(self, strategy_type: OptimizationType):
        """Change optimization strategy at runtime"""
        if strategy_type in self._available_strategies:
            self._strategy = self._available_strategies[strategy_type]()
        else:
            raise ValueError(f"Strategy {strategy_type} not implemented")
    
    def get_strategy(self) -> IOptimizationStrategy:
        """Get current strategy"""
        return self._strategy
    
    def optimize_listing(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize complete listing using current strategy"""
        
        title = listing_data.get("title", "")
        description = listing_data.get("description", "")
        category = listing_data.get("category", "general")
        keywords = listing_data.get("keywords", [])
        
        # Generate keywords if not provided
        if not keywords:
            keywords = self._strategy.generate_keywords(title, category, description)
        
        # Optimize title
        title_result = self._strategy.optimize_title(title, category, keywords)
        
        # Optimize description  
        desc_result = self._strategy.optimize_description(description, title, keywords)
        
        # Calculate overall score
        overall_score = self._strategy.calculate_score(
            title_result["optimized_title"],
            desc_result["optimized_description"], 
            keywords
        )
        
        return {
            "title_optimization": title_result,
            "description_optimization": desc_result,
            "suggested_keywords": keywords,
            "overall_score": overall_score,
            "strategy_used": self._strategy.strategy_name,
            "strategy_type": self._strategy.strategy_type.value
        }
    
    def get_available_strategies(self) -> List[Dict[str, str]]:
        """Get list of available optimization strategies"""
        return [
            {
                "type": strategy_type.value,
                "name": strategy_class().strategy_name,
                "description": self._get_strategy_description(strategy_type)
            }
            for strategy_type, strategy_class in self._available_strategies.items()
        ]
    
    def _get_strategy_description(self, strategy_type: OptimizationType) -> str:
        """Get description for strategy type"""
        descriptions = {
            OptimizationType.BASIC: "Fundamental SEO optimization with proven techniques",
            OptimizationType.ADVANCED: "Advanced SEO with competitive analysis and conversion optimization",
            OptimizationType.SEO_FOCUSED: "Pure SEO optimization for maximum search visibility",
            OptimizationType.CONVERSION_FOCUSED: "Optimized for maximum conversion rates and sales",
            OptimizationType.AI_POWERED: "AI-driven optimization with machine learning insights"
        }
        return descriptions.get(strategy_type, "Custom optimization strategy")