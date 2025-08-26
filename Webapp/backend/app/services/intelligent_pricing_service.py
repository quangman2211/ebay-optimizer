"""
Intelligent Pricing Service - SOLID Architecture Implementation
Advanced pricing optimization algorithms với AI-powered recommendations
Single Responsibility: Manages intelligent pricing algorithms và optimization strategies
"""

import math
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.models.database_models import Product, Supplier, Order, Listing
from app.schemas.schemas import PaginationParams


class PricingStrategy(str, Enum):
    """Advanced pricing strategies"""
    COST_PLUS = "cost_plus"
    COMPETITIVE = "competitive"
    VALUE_BASED = "value_based"
    PENETRATION = "penetration"
    SKIMMING = "skimming"
    DYNAMIC = "dynamic"
    PSYCHOLOGICAL = "psychological"
    BUNDLE = "bundle"
    SEASONAL = "seasonal"
    DEMAND_BASED = "demand_based"


class MarketCondition(str, Enum):
    """Market condition types"""
    BULL = "bull"          # Rising market
    BEAR = "bear"          # Falling market
    STABLE = "stable"      # Stable market
    VOLATILE = "volatile"  # High volatility
    SEASONAL = "seasonal"  # Seasonal patterns


class PriceElasticity(str, Enum):
    """Price elasticity levels"""
    INELASTIC = "inelastic"      # <0.5 - Little price sensitivity
    MODERATE = "moderate"        # 0.5-1.5 - Moderate sensitivity
    ELASTIC = "elastic"          # >1.5 - High price sensitivity


@dataclass
class PricingContext:
    """Context for pricing decisions"""
    product_id: int
    category: str
    brand: str
    cost_price: float
    current_price: float
    competitor_prices: List[float]
    sales_history: List[Dict[str, Any]]
    inventory_level: int
    supplier_performance: float
    market_condition: MarketCondition
    seasonality_factor: float
    demand_trend: float
    profit_target: float


@dataclass
class PricingRecommendation:
    """Pricing recommendation result"""
    recommended_price: float
    strategy_used: PricingStrategy
    confidence_score: float
    expected_profit_margin: float
    expected_sales_volume: int
    risk_assessment: str
    reasoning: str
    alternative_prices: List[Dict[str, Any]]


class IntelligentPricingService:
    """
    SOLID Principle: Single Responsibility
    Advanced pricing optimization service với AI-powered algorithms
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.pricing_strategies = {
            PricingStrategy.COST_PLUS: self._cost_plus_pricing,
            PricingStrategy.COMPETITIVE: self._competitive_pricing,
            PricingStrategy.VALUE_BASED: self._value_based_pricing,
            PricingStrategy.PENETRATION: self._penetration_pricing,
            PricingStrategy.SKIMMING: self._skimming_pricing,
            PricingStrategy.DYNAMIC: self._dynamic_pricing,
            PricingStrategy.PSYCHOLOGICAL: self._psychological_pricing,
            PricingStrategy.DEMAND_BASED: self._demand_based_pricing
        }
    
    # ===========================================
    # MAIN OPTIMIZATION FUNCTIONS
    # ===========================================
    
    def optimize_product_pricing(
        self, 
        product_id: int, 
        strategy: Optional[PricingStrategy] = None,
        context_override: Optional[Dict[str, Any]] = None
    ) -> PricingRecommendation:
        """
        Optimize pricing for a specific product using intelligent algorithms
        """
        try:
            # Get product and build context
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                raise ValueError(f"Product {product_id} not found")
            
            context = self._build_pricing_context(product, context_override)
            
            # Determine optimal strategy if not specified
            if strategy is None:
                strategy = self._determine_optimal_strategy(context)
            
            # Apply pricing strategy
            recommendation = self._apply_pricing_strategy(context, strategy)
            
            # Enhance with market intelligence
            recommendation = self._enhance_with_market_intelligence(context, recommendation)
            
            # Validate and adjust recommendation
            recommendation = self._validate_pricing_recommendation(context, recommendation)
            
            return recommendation
            
        except Exception as e:
            # Return safe fallback recommendation
            return self._fallback_recommendation(product, str(e))
    
    def optimize_portfolio_pricing(
        self, 
        category: Optional[str] = None,
        supplier_id: Optional[int] = None,
        batch_size: int = 50
    ) -> List[PricingRecommendation]:
        """
        Optimize pricing for entire product portfolio
        """
        try:
            # Get products to optimize
            query = self.db.query(Product).filter(Product.status == "active")
            
            if category:
                query = query.filter(Product.category == category)
            if supplier_id:
                query = query.filter(Product.primary_supplier_id == supplier_id)
            
            products = query.limit(batch_size).all()
            
            recommendations = []
            for product in products:
                try:
                    recommendation = self.optimize_product_pricing(product.id)
                    recommendations.append(recommendation)
                except Exception as e:
                    # Log error but continue with other products
                    print(f"Failed to optimize pricing for product {product.id}: {e}")
            
            return recommendations
            
        except Exception as e:
            print(f"Portfolio optimization failed: {e}")
            return []
    
    def analyze_price_elasticity(self, product_id: int, price_range: Tuple[float, float] = None) -> Dict[str, Any]:
        """
        Analyze price elasticity for a product
        """
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "Product not found"}
            
            # Get historical sales data
            sales_history = self._get_sales_history(product_id, days=90)
            
            if len(sales_history) < 10:
                return {"error": "Insufficient sales data for elasticity analysis"}
            
            # Calculate price elasticity
            elasticity = self._calculate_price_elasticity(sales_history)
            
            # Determine elasticity category
            if elasticity < 0.5:
                category = PriceElasticity.INELASTIC
                description = "Price changes have minimal impact on demand"
            elif elasticity < 1.5:
                category = PriceElasticity.MODERATE
                description = "Price changes have moderate impact on demand"
            else:
                category = PriceElasticity.ELASTIC
                description = "Price changes significantly impact demand"
            
            # Generate price-demand curve
            price_points = self._generate_demand_curve(product, elasticity, price_range)
            
            return {
                "product_id": product_id,
                "elasticity_coefficient": elasticity,
                "elasticity_category": category.value,
                "description": description,
                "price_demand_curve": price_points,
                "optimal_price_range": self._find_optimal_price_range(price_points),
                "recommendations": self._generate_elasticity_recommendations(elasticity, product)
            }
            
        except Exception as e:
            return {"error": f"Elasticity analysis failed: {str(e)}"}
    
    def predict_market_response(
        self, 
        product_id: int, 
        proposed_price: float,
        time_horizon_days: int = 30
    ) -> Dict[str, Any]:
        """
        Predict market response to price change
        """
        try:
            product = self.db.query(Product).filter(Product.id == product_id).first()
            if not product:
                return {"error": "Product not found"}
            
            context = self._build_pricing_context(product)
            
            # Calculate price change impact
            price_change_percent = (proposed_price - context.current_price) / context.current_price * 100
            
            # Predict sales volume change
            elasticity = self._calculate_price_elasticity(context.sales_history)
            volume_change_percent = -elasticity * price_change_percent
            
            # Estimate current sales volume
            current_volume = self._estimate_current_sales_volume(product_id, time_horizon_days)
            predicted_volume = current_volume * (1 + volume_change_percent / 100)
            
            # Calculate profit impact
            current_profit = (context.current_price - context.cost_price) * current_volume
            predicted_profit = (proposed_price - context.cost_price) * predicted_volume
            profit_change = predicted_profit - current_profit
            
            # Risk assessment
            risk_factors = self._assess_price_change_risks(context, price_change_percent)
            
            return {
                "product_id": product_id,
                "current_price": context.current_price,
                "proposed_price": proposed_price,
                "price_change_percent": round(price_change_percent, 2),
                "predictions": {
                    "volume_change_percent": round(volume_change_percent, 2),
                    "current_volume": current_volume,
                    "predicted_volume": round(predicted_volume),
                    "current_profit": round(current_profit, 2),
                    "predicted_profit": round(predicted_profit, 2),
                    "profit_change": round(profit_change, 2)
                },
                "risk_assessment": risk_factors,
                "confidence_level": self._calculate_prediction_confidence(context),
                "recommendations": self._generate_response_recommendations(context, price_change_percent)
            }
            
        except Exception as e:
            return {"error": f"Market response prediction failed: {str(e)}"}
    
    # ===========================================
    # PRICING STRATEGY IMPLEMENTATIONS
    # ===========================================
    
    def _cost_plus_pricing(self, context: PricingContext, margin_target: float = 0.3) -> float:
        """Cost-plus pricing strategy"""
        margin = context.profit_target if context.profit_target > 0 else margin_target
        return context.cost_price * (1 + margin)
    
    def _competitive_pricing(self, context: PricingContext) -> float:
        """Competitive pricing based on market prices"""
        if not context.competitor_prices:
            return self._cost_plus_pricing(context)
        
        avg_competitor_price = sum(context.competitor_prices) / len(context.competitor_prices)
        
        # Position based on supplier performance
        if context.supplier_performance > 4.0:
            # Premium positioning for high-performance suppliers
            return avg_competitor_price * 1.05
        elif context.supplier_performance < 3.0:
            # Competitive positioning for lower-performance suppliers
            return avg_competitor_price * 0.95
        else:
            # Match average
            return avg_competitor_price
    
    def _value_based_pricing(self, context: PricingContext) -> float:
        """Value-based pricing considering perceived value"""
        base_price = self._competitive_pricing(context)
        
        # Adjust based on brand perception and quality
        quality_multiplier = 1.0
        if context.brand and context.supplier_performance > 4.0:
            quality_multiplier = 1.15  # Premium for high-quality brands
        elif context.supplier_performance < 3.0:
            quality_multiplier = 0.9   # Discount for lower quality
        
        # Consider demand trends
        demand_multiplier = 1.0 + (context.demand_trend * 0.1)
        
        return base_price * quality_multiplier * demand_multiplier
    
    def _penetration_pricing(self, context: PricingContext) -> float:
        """Penetration pricing for market entry"""
        competitive_price = self._competitive_pricing(context)
        # Price 10-20% below competition to gain market share
        return competitive_price * 0.85
    
    def _skimming_pricing(self, context: PricingContext) -> float:
        """Price skimming for premium products"""
        competitive_price = self._competitive_pricing(context)
        # Price 15-25% above competition for premium positioning
        return competitive_price * 1.2
    
    def _dynamic_pricing(self, context: PricingContext) -> float:
        """Dynamic pricing based on multiple factors"""
        base_price = self._competitive_pricing(context)
        
        # Inventory adjustment
        inventory_factor = 1.0
        if context.inventory_level < 10:
            inventory_factor = 1.1  # Increase price for low inventory
        elif context.inventory_level > 100:
            inventory_factor = 0.95  # Decrease price for high inventory
        
        # Seasonality adjustment
        seasonal_factor = context.seasonality_factor
        
        # Market condition adjustment
        market_factor = 1.0
        if context.market_condition == MarketCondition.BULL:
            market_factor = 1.05
        elif context.market_condition == MarketCondition.BEAR:
            market_factor = 0.95
        
        return base_price * inventory_factor * seasonal_factor * market_factor
    
    def _psychological_pricing(self, context: PricingContext) -> float:
        """Psychological pricing with charm pricing"""
        base_price = self._competitive_pricing(context)
        
        # Apply charm pricing (ending in .99, .95, etc.)
        if base_price >= 100:
            # For prices over $100, use .99
            return math.floor(base_price) + 0.99
        elif base_price >= 20:
            # For prices $20-$100, use .95
            return math.floor(base_price) + 0.95
        else:
            # For prices under $20, use .99
            return math.floor(base_price) + 0.99
    
    def _demand_based_pricing(self, context: PricingContext) -> float:
        """Demand-based pricing using sales velocity"""
        base_price = self._competitive_pricing(context)
        
        # Calculate sales velocity from history
        if context.sales_history:
            recent_sales = [s for s in context.sales_history if 
                          datetime.fromisoformat(s['date']) > datetime.now() - timedelta(days=30)]
            
            sales_velocity = len(recent_sales) / 30  # Sales per day
            
            # Adjust price based on velocity
            if sales_velocity > 2:  # High demand
                return base_price * 1.1
            elif sales_velocity < 0.5:  # Low demand
                return base_price * 0.9
        
        return base_price
    
    # ===========================================
    # CONTEXT BUILDING & ANALYSIS
    # ===========================================
    
    def _build_pricing_context(self, product: Product, override: Optional[Dict[str, Any]] = None) -> PricingContext:
        """Build comprehensive pricing context"""
        # Get supplier info
        supplier = None
        if product.primary_supplier_id:
            supplier = self.db.query(Supplier).filter(Supplier.id == product.primary_supplier_id).first()
        
        # Get sales history
        sales_history = self._get_sales_history(product.id)
        
        # Get competitor prices (mock for now)
        competitor_prices = self._get_competitor_prices(product)
        
        # Analyze market conditions
        market_condition = self._analyze_market_condition(product.category)
        
        # Calculate seasonality
        seasonality_factor = self._calculate_seasonality_factor(product.category)
        
        # Calculate demand trend
        demand_trend = self._calculate_demand_trend(sales_history)
        
        context = PricingContext(
            product_id=product.id,
            category=product.category or "general",
            brand=product.brand or "",
            cost_price=product.cost_price or 0.0,
            current_price=product.selling_price or 0.0,
            competitor_prices=competitor_prices,
            sales_history=sales_history,
            inventory_level=product.stock_level or 0,
            supplier_performance=supplier.performance_rating if supplier else 3.0,
            market_condition=market_condition,
            seasonality_factor=seasonality_factor,
            demand_trend=demand_trend,
            profit_target=0.3  # Default 30% margin
        )
        
        # Apply any overrides
        if override:
            for key, value in override.items():
                if hasattr(context, key):
                    setattr(context, key, value)
        
        return context
    
    def _determine_optimal_strategy(self, context: PricingContext) -> PricingStrategy:
        """Determine optimal pricing strategy based on context"""
        
        # High competition + low differentiation = Competitive
        if len(context.competitor_prices) > 3 and context.supplier_performance < 3.5:
            return PricingStrategy.COMPETITIVE
        
        # High inventory + low sales = Penetration
        if context.inventory_level > 50 and context.demand_trend < -0.1:
            return PricingStrategy.PENETRATION
        
        # Low inventory + high demand = Skimming
        if context.inventory_level < 20 and context.demand_trend > 0.1:
            return PricingStrategy.SKIMMING
        
        # Premium brand + high performance = Value-based
        if context.supplier_performance > 4.0 and context.brand:
            return PricingStrategy.VALUE_BASED
        
        # High volatility = Dynamic
        if context.market_condition == MarketCondition.VOLATILE:
            return PricingStrategy.DYNAMIC
        
        # Default to competitive pricing
        return PricingStrategy.COMPETITIVE
    
    def _get_sales_history(self, product_id: int, days: int = 60) -> List[Dict[str, Any]]:
        """Get sales history for product"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Mock sales history for now
        # In real implementation, this would query actual sales data
        return [
            {
                "date": (datetime.now() - timedelta(days=i)).isoformat(),
                "quantity": max(1, int(5 * math.sin(i * 0.1) + 3)),
                "price": 29.99,
                "revenue": max(1, int(5 * math.sin(i * 0.1) + 3)) * 29.99
            }
            for i in range(days)
        ]
    
    def _get_competitor_prices(self, product: Product) -> List[float]:
        """Get competitor prices (mock implementation)"""
        base_price = product.selling_price or product.cost_price * 1.3 if product.cost_price else 25.0
        
        # Generate realistic competitor prices
        return [
            base_price * (0.9 + i * 0.05) for i in range(5)
        ]
    
    def _analyze_market_condition(self, category: str) -> MarketCondition:
        """Analyze market condition for category"""
        # Mock implementation - would use real market data
        import random
        conditions = list(MarketCondition)
        return random.choice(conditions)
    
    def _calculate_seasonality_factor(self, category: str) -> float:
        """Calculate seasonality adjustment factor"""
        current_month = datetime.now().month
        
        # Simple seasonality patterns
        seasonal_patterns = {
            "electronics": {12: 1.2, 1: 0.8, 6: 1.1, 7: 1.1},  # Holiday boost
            "clothing": {3: 1.1, 9: 1.1, 12: 1.2},  # Season changes
            "toys": {11: 1.3, 12: 1.5, 1: 0.7},  # Holiday heavy
        }
        
        pattern = seasonal_patterns.get(category.lower(), {})
        return pattern.get(current_month, 1.0)
    
    def _calculate_demand_trend(self, sales_history: List[Dict[str, Any]]) -> float:
        """Calculate demand trend from sales history"""
        if len(sales_history) < 10:
            return 0.0
        
        # Simple linear trend calculation
        recent_sales = sales_history[:15]  # Last 15 days
        older_sales = sales_history[15:30]  # Previous 15 days
        
        recent_avg = sum(s["quantity"] for s in recent_sales) / len(recent_sales)
        older_avg = sum(s["quantity"] for s in older_sales) / len(older_sales)
        
        if older_avg == 0:
            return 0.0
        
        return (recent_avg - older_avg) / older_avg
    
    # ===========================================
    # ADVANCED ANALYTICS
    # ===========================================
    
    def _calculate_price_elasticity(self, sales_history: List[Dict[str, Any]]) -> float:
        """Calculate price elasticity of demand"""
        if len(sales_history) < 10:
            return 1.0  # Default moderate elasticity
        
        # Calculate elasticity using simple regression
        price_changes = []
        quantity_changes = []
        
        for i in range(1, len(sales_history)):
            current = sales_history[i]
            previous = sales_history[i-1]
            
            if previous["price"] > 0 and previous["quantity"] > 0:
                price_change = (current["price"] - previous["price"]) / previous["price"]
                quantity_change = (current["quantity"] - previous["quantity"]) / previous["quantity"]
                
                if abs(price_change) > 0.001:  # Avoid division by very small numbers
                    price_changes.append(price_change)
                    quantity_changes.append(quantity_change)
        
        if len(price_changes) < 5:
            return 1.0
        
        # Simple elasticity calculation
        avg_price_change = sum(price_changes) / len(price_changes)
        avg_quantity_change = sum(quantity_changes) / len(quantity_changes)
        
        if abs(avg_price_change) < 0.001:
            return 1.0
        
        elasticity = abs(avg_quantity_change / avg_price_change)
        return min(elasticity, 5.0)  # Cap at 5.0 to avoid extreme values
    
    def _generate_demand_curve(self, product: Product, elasticity: float, price_range: Tuple[float, float] = None) -> List[Dict[str, Any]]:
        """Generate price-demand curve"""
        current_price = product.selling_price or product.cost_price * 1.3 if product.cost_price else 25.0
        current_demand = self._estimate_current_demand(product.id)
        
        if price_range is None:
            min_price = current_price * 0.7
            max_price = current_price * 1.5
        else:
            min_price, max_price = price_range
        
        price_points = []
        price_step = (max_price - min_price) / 20
        
        for i in range(21):
            price = min_price + (i * price_step)
            price_change_percent = (price - current_price) / current_price
            
            # Calculate demand using elasticity
            demand_change_percent = -elasticity * price_change_percent
            estimated_demand = current_demand * (1 + demand_change_percent)
            
            # Calculate profit
            cost = product.cost_price or 0.0
            profit_per_unit = max(0, price - cost)
            total_profit = profit_per_unit * max(0, estimated_demand)
            
            price_points.append({
                "price": round(price, 2),
                "estimated_demand": max(0, round(estimated_demand)),
                "profit_per_unit": round(profit_per_unit, 2),
                "total_profit": round(total_profit, 2),
                "revenue": round(price * max(0, estimated_demand), 2)
            })
        
        return price_points
    
    def _estimate_current_demand(self, product_id: int) -> float:
        """Estimate current demand level"""
        sales_history = self._get_sales_history(product_id, days=30)
        if not sales_history:
            return 1.0
        
        total_quantity = sum(s["quantity"] for s in sales_history)
        return total_quantity / 30  # Average daily demand
    
    def _estimate_current_sales_volume(self, product_id: int, days: int) -> int:
        """Estimate sales volume for given period"""
        daily_demand = self._estimate_current_demand(product_id)
        return int(daily_demand * days)
    
    # ===========================================
    # VALIDATION & ENHANCEMENT
    # ===========================================
    
    def _enhance_with_market_intelligence(self, context: PricingContext, recommendation: PricingRecommendation) -> PricingRecommendation:
        """Enhance recommendation with market intelligence"""
        
        # Add alternative pricing options
        alternatives = []
        
        # Cost-plus alternative
        cost_plus_price = self._cost_plus_pricing(context)
        alternatives.append({
            "strategy": "cost_plus",
            "price": round(cost_plus_price, 2),
            "margin": round((cost_plus_price - context.cost_price) / cost_plus_price * 100, 1),
            "description": "Safe cost-plus pricing"
        })
        
        # Competitive alternative
        competitive_price = self._competitive_pricing(context)
        alternatives.append({
            "strategy": "competitive",
            "price": round(competitive_price, 2),
            "margin": round((competitive_price - context.cost_price) / competitive_price * 100, 1),
            "description": "Match competition"
        })
        
        # Psychological alternative
        psychological_price = self._psychological_pricing(context)
        alternatives.append({
            "strategy": "psychological",
            "price": round(psychological_price, 2),
            "margin": round((psychological_price - context.cost_price) / psychological_price * 100, 1),
            "description": "Psychological pricing"
        })
        
        recommendation.alternative_prices = alternatives
        
        return recommendation
    
    def _validate_pricing_recommendation(self, context: PricingContext, recommendation: PricingRecommendation) -> PricingRecommendation:
        """Validate and adjust pricing recommendation"""
        
        # Ensure minimum margin
        min_margin = 0.1  # 10% minimum
        min_price = context.cost_price * (1 + min_margin)
        
        if recommendation.recommended_price < min_price:
            recommendation.recommended_price = min_price
            recommendation.risk_assessment = "high"
            recommendation.reasoning += " (Adjusted to maintain minimum margin)"
        
        # Ensure price is reasonable vs current price
        max_change = 0.3  # Maximum 30% change
        max_increase = context.current_price * (1 + max_change)
        max_decrease = context.current_price * (1 - max_change)
        
        if recommendation.recommended_price > max_increase:
            recommendation.recommended_price = max_increase
            recommendation.reasoning += " (Limited to 30% increase)"
        elif recommendation.recommended_price < max_decrease:
            recommendation.recommended_price = max_decrease
            recommendation.reasoning += " (Limited to 30% decrease)"
        
        # Recalculate profit margin
        recommendation.expected_profit_margin = (
            (recommendation.recommended_price - context.cost_price) / 
            recommendation.recommended_price * 100
        )
        
        return recommendation
    
    def _apply_pricing_strategy(self, context: PricingContext, strategy: PricingStrategy) -> PricingRecommendation:
        """Apply specific pricing strategy"""
        strategy_func = self.pricing_strategies.get(strategy)
        if not strategy_func:
            strategy = PricingStrategy.COMPETITIVE
            strategy_func = self._competitive_pricing
        
        recommended_price = strategy_func(context)
        
        # Calculate metrics
        profit_margin = (recommended_price - context.cost_price) / recommended_price * 100
        
        # Estimate sales volume impact
        price_change = (recommended_price - context.current_price) / context.current_price
        elasticity = self._calculate_price_elasticity(context.sales_history)
        volume_change = -elasticity * price_change
        current_volume = self._estimate_current_demand(context.product_id) * 30
        expected_volume = int(current_volume * (1 + volume_change))
        
        # Calculate confidence
        confidence = self._calculate_strategy_confidence(context, strategy)
        
        # Generate reasoning
        reasoning = self._generate_pricing_reasoning(context, strategy, recommended_price)
        
        return PricingRecommendation(
            recommended_price=round(recommended_price, 2),
            strategy_used=strategy,
            confidence_score=confidence,
            expected_profit_margin=round(profit_margin, 2),
            expected_sales_volume=max(0, expected_volume),
            risk_assessment=self._assess_pricing_risk(context, recommended_price),
            reasoning=reasoning,
            alternative_prices=[]  # Will be filled later
        )
    
    def _calculate_strategy_confidence(self, context: PricingContext, strategy: PricingStrategy) -> float:
        """Calculate confidence score for pricing strategy"""
        base_confidence = 0.7
        
        # Data quality factors
        if len(context.sales_history) > 30:
            base_confidence += 0.1
        if len(context.competitor_prices) > 2:
            base_confidence += 0.1
        if context.supplier_performance > 3.5:
            base_confidence += 0.1
        
        # Strategy-specific adjustments
        if strategy == PricingStrategy.COMPETITIVE and context.competitor_prices:
            base_confidence += 0.1
        elif strategy == PricingStrategy.COST_PLUS:
            base_confidence += 0.05  # Always reliable but not optimal
        
        return min(base_confidence, 0.95)
    
    def _generate_pricing_reasoning(self, context: PricingContext, strategy: PricingStrategy, price: float) -> str:
        """Generate human-readable reasoning for pricing decision"""
        reasons = []
        
        if strategy == PricingStrategy.COMPETITIVE:
            avg_competitor = sum(context.competitor_prices) / len(context.competitor_prices) if context.competitor_prices else 0
            if abs(price - avg_competitor) < 0.5:
                reasons.append("Matched competitor average to maintain market position")
            elif price > avg_competitor:
                reasons.append("Priced above competitors due to superior supplier performance")
            else:
                reasons.append("Priced below competitors to gain market share")
        
        elif strategy == PricingStrategy.DYNAMIC:
            if context.inventory_level < 20:
                reasons.append("Low inventory drives price premium")
            if context.demand_trend > 0.1:
                reasons.append("Strong demand trend supports higher pricing")
            if context.seasonality_factor > 1.05:
                reasons.append("Seasonal demand peak allows premium pricing")
        
        elif strategy == PricingStrategy.VALUE_BASED:
            if context.supplier_performance > 4.0:
                reasons.append("Premium pricing justified by superior quality")
            if context.brand:
                reasons.append("Brand value supports higher price point")
        
        if not reasons:
            reasons.append(f"Applied {strategy.value} pricing strategy based on market analysis")
        
        return ". ".join(reasons) + "."
    
    def _assess_pricing_risk(self, context: PricingContext, price: float) -> str:
        """Assess risk level of pricing decision"""
        price_change = abs(price - context.current_price) / context.current_price
        
        if price_change > 0.2:
            return "high"
        elif price_change > 0.1:
            return "medium"
        else:
            return "low"
    
    def _fallback_recommendation(self, product: Product, error: str) -> PricingRecommendation:
        """Generate safe fallback recommendation"""
        cost = product.cost_price or 0.0
        current = product.selling_price or cost * 1.3
        
        return PricingRecommendation(
            recommended_price=current,
            strategy_used=PricingStrategy.COST_PLUS,
            confidence_score=0.5,
            expected_profit_margin=20.0,
            expected_sales_volume=1,
            risk_assessment="low",
            reasoning=f"Fallback recommendation due to error: {error}",
            alternative_prices=[]
        )
    
    # ===========================================
    # ADDITIONAL HELPER METHODS
    # ===========================================
    
    def _find_optimal_price_range(self, price_points: List[Dict[str, Any]]) -> Dict[str, float]:
        """Find optimal price range from demand curve"""
        if not price_points:
            return {"min": 0.0, "max": 0.0, "optimal": 0.0}
        
        # Find price with maximum total profit
        max_profit_point = max(price_points, key=lambda x: x["total_profit"])
        
        return {
            "min": min(p["price"] for p in price_points),
            "max": max(p["price"] for p in price_points),
            "optimal": max_profit_point["price"]
        }
    
    def _generate_elasticity_recommendations(self, elasticity: float, product: Product) -> List[str]:
        """Generate recommendations based on price elasticity"""
        recommendations = []
        
        if elasticity < 0.5:  # Inelastic
            recommendations.append("Consider premium pricing strategy")
            recommendations.append("Focus on quality and brand positioning")
            recommendations.append("Price increases will have minimal impact on demand")
        elif elasticity < 1.5:  # Moderate
            recommendations.append("Use competitive pricing strategy")
            recommendations.append("Monitor competitor prices closely")
            recommendations.append("Test small price changes to optimize")
        else:  # Elastic
            recommendations.append("Use penetration pricing for market share")
            recommendations.append("Avoid sudden price increases")
            recommendations.append("Focus on cost reduction to improve margins")
        
        return recommendations
    
    def _assess_price_change_risks(self, context: PricingContext, price_change_percent: float) -> List[str]:
        """Assess risks of price change"""
        risks = []
        
        if abs(price_change_percent) > 15:
            risks.append("Large price change may shock customers")
        
        if price_change_percent > 10 and len(context.competitor_prices) > 2:
            risks.append("Price increase may lose customers to competitors")
        
        if price_change_percent < -10:
            risks.append("Price decrease may erode brand perception")
        
        if context.inventory_level < 10 and price_change_percent < 0:
            risks.append("Price decrease with low inventory may create shortage")
        
        if not risks:
            risks.append("Low risk - price change is within acceptable range")
        
        return risks
    
    def _calculate_prediction_confidence(self, context: PricingContext) -> float:
        """Calculate confidence in market response prediction"""
        confidence = 0.6  # Base confidence
        
        # More sales history = higher confidence
        if len(context.sales_history) > 30:
            confidence += 0.2
        elif len(context.sales_history) > 15:
            confidence += 0.1
        
        # Market stability = higher confidence
        if context.market_condition == MarketCondition.STABLE:
            confidence += 0.1
        elif context.market_condition == MarketCondition.VOLATILE:
            confidence -= 0.1
        
        # Competitor data = higher confidence
        if len(context.competitor_prices) > 3:
            confidence += 0.1
        
        return min(confidence, 0.9)
    
    def _generate_response_recommendations(self, context: PricingContext, price_change_percent: float) -> List[str]:
        """Generate recommendations based on predicted market response"""
        recommendations = []
        
        if price_change_percent > 10:
            recommendations.append("Implement price increase gradually over 2-3 weeks")
            recommendations.append("Communicate value improvements to justify increase")
            recommendations.append("Monitor competitor response closely")
        elif price_change_percent < -10:
            recommendations.append("Consider limited-time promotion instead of permanent decrease")
            recommendations.append("Ensure sufficient inventory for increased demand")
            recommendations.append("Monitor profit margins carefully")
        else:
            recommendations.append("Price change is within normal range")
            recommendations.append("Implement immediately")
        
        return recommendations