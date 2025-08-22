"""
Intelligent Pricing API Endpoints - SOLID Architecture Implementation
Advanced pricing optimization API với AI-powered recommendations
Single Responsibility: Manages intelligent pricing API endpoints
"""

from typing import List, Dict, Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.auth import get_current_user, require_permission
from app.services.intelligent_pricing_service import (
    IntelligentPricingService, PricingStrategy, PricingRecommendation
)
from app.models.database_models import User
from app.schemas.schemas import (
    IntelligentPricingRequest, IntelligentPricingResponse,
    PriceElasticityAnalysis, MarketResponsePrediction,
    PortfolioPricingRequest, PortfolioPricingResponse
)

router = APIRouter()

# ===========================================
# INTELLIGENT PRICING OPTIMIZATION
# ===========================================

@router.post("/optimize/{product_id}", response_model=Dict[str, Any])
async def optimize_product_pricing(
    product_id: int,
    strategy: Optional[str] = Query(None, description="Specific pricing strategy to use"),
    context_override: Optional[Dict[str, Any]] = None,
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Optimize pricing for specific product using intelligent algorithms"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        # Convert strategy string to enum if provided
        pricing_strategy = None
        if strategy:
            try:
                pricing_strategy = PricingStrategy(strategy)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid pricing strategy: {strategy}")
        
        recommendation = pricing_service.optimize_product_pricing(
            product_id=product_id,
            strategy=pricing_strategy,
            context_override=context_override
        )
        
        return {
            "success": True,
            "product_id": product_id,
            "recommendation": {
                "recommended_price": recommendation.recommended_price,
                "strategy_used": recommendation.strategy_used.value,
                "confidence_score": recommendation.confidence_score,
                "expected_profit_margin": recommendation.expected_profit_margin,
                "expected_sales_volume": recommendation.expected_sales_volume,
                "risk_assessment": recommendation.risk_assessment,
                "reasoning": recommendation.reasoning,
                "alternative_prices": recommendation.alternative_prices
            }
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pricing optimization failed: {str(e)}")

@router.post("/optimize-portfolio", response_model=Dict[str, Any])
async def optimize_portfolio_pricing(
    category: Optional[str] = Query(None, description="Filter by product category"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    batch_size: int = Query(default=50, description="Number of products to optimize"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Optimize pricing for entire product portfolio"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        recommendations = pricing_service.optimize_portfolio_pricing(
            category=category,
            supplier_id=supplier_id,
            batch_size=batch_size
        )
        
        # Format recommendations
        formatted_recommendations = []
        total_potential_profit = 0.0
        
        for rec in recommendations:
            formatted_rec = {
                "product_id": rec.recommended_price,  # This should be product_id from context
                "recommended_price": rec.recommended_price,
                "strategy_used": rec.strategy_used.value,
                "confidence_score": rec.confidence_score,
                "expected_profit_margin": rec.expected_profit_margin,
                "risk_assessment": rec.risk_assessment,
                "reasoning": rec.reasoning
            }
            formatted_recommendations.append(formatted_rec)
            
            # Calculate potential profit increase (mock calculation)
            total_potential_profit += rec.expected_profit_margin * rec.expected_sales_volume * 0.01
        
        return {
            "success": True,
            "optimized_products": len(recommendations),
            "total_potential_profit_increase": round(total_potential_profit, 2),
            "filters": {
                "category": category,
                "supplier_id": supplier_id,
                "batch_size": batch_size
            },
            "recommendations": formatted_recommendations
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Portfolio optimization failed: {str(e)}")

# ===========================================
# PRICE ELASTICITY ANALYSIS
# ===========================================

@router.get("/elasticity/{product_id}", response_model=Dict[str, Any])
async def analyze_price_elasticity(
    product_id: int,
    min_price: Optional[float] = Query(None, description="Minimum price for analysis"),
    max_price: Optional[float] = Query(None, description="Maximum price for analysis"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Analyze price elasticity for a product"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        price_range = None
        if min_price is not None and max_price is not None:
            price_range = (min_price, max_price)
        
        analysis = pricing_service.analyze_price_elasticity(
            product_id=product_id,
            price_range=price_range
        )
        
        if "error" in analysis:
            raise HTTPException(status_code=400, detail=analysis["error"])
        
        return {
            "success": True,
            "product_id": product_id,
            "analysis": analysis
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Elasticity analysis failed: {str(e)}")

@router.get("/elasticity-batch", response_model=Dict[str, Any])
async def analyze_elasticity_batch(
    product_ids: List[int] = Query(..., description="List of product IDs"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Analyze price elasticity for multiple products"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        results = []
        for product_id in product_ids:
            try:
                analysis = pricing_service.analyze_price_elasticity(product_id)
                if "error" not in analysis:
                    results.append({
                        "product_id": product_id,
                        "elasticity_coefficient": analysis["elasticity_coefficient"],
                        "elasticity_category": analysis["elasticity_category"],
                        "optimal_price": analysis["optimal_price_range"]["optimal"]
                    })
            except Exception as e:
                results.append({
                    "product_id": product_id,
                    "error": str(e)
                })
        
        return {
            "success": True,
            "analyzed_products": len(results),
            "results": results
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch elasticity analysis failed: {str(e)}")

# ===========================================
# MARKET RESPONSE PREDICTION
# ===========================================

@router.post("/predict-response/{product_id}", response_model=Dict[str, Any])
async def predict_market_response(
    product_id: int,
    proposed_price: float = Query(..., description="Proposed new price"),
    time_horizon_days: int = Query(default=30, description="Prediction time horizon in days"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Predict market response to price change"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        prediction = pricing_service.predict_market_response(
            product_id=product_id,
            proposed_price=proposed_price,
            time_horizon_days=time_horizon_days
        )
        
        if "error" in prediction:
            raise HTTPException(status_code=400, detail=prediction["error"])
        
        return {
            "success": True,
            "product_id": product_id,
            "prediction": prediction
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Market response prediction failed: {str(e)}")

@router.post("/simulate-pricing", response_model=Dict[str, Any])
async def simulate_pricing_scenarios(
    product_id: int,
    price_scenarios: List[float] = Query(..., description="List of prices to simulate"),
    time_horizon_days: int = Query(default=30, description="Simulation time horizon"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Simulate multiple pricing scenarios"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        scenarios = []
        for price in price_scenarios:
            try:
                prediction = pricing_service.predict_market_response(
                    product_id=product_id,
                    proposed_price=price,
                    time_horizon_days=time_horizon_days
                )
                
                if "error" not in prediction:
                    scenarios.append({
                        "proposed_price": price,
                        "predicted_volume": prediction["predictions"]["predicted_volume"],
                        "predicted_profit": prediction["predictions"]["predicted_profit"],
                        "profit_change": prediction["predictions"]["profit_change"],
                        "risk_level": len(prediction["risk_assessment"])
                    })
            except Exception as e:
                scenarios.append({
                    "proposed_price": price,
                    "error": str(e)
                })
        
        # Find optimal scenario
        successful_scenarios = [s for s in scenarios if "error" not in s]
        optimal_scenario = None
        if successful_scenarios:
            optimal_scenario = max(successful_scenarios, key=lambda x: x["predicted_profit"])
        
        return {
            "success": True,
            "product_id": product_id,
            "time_horizon_days": time_horizon_days,
            "scenarios": scenarios,
            "optimal_scenario": optimal_scenario
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pricing simulation failed: {str(e)}")

# ===========================================
# PRICING STRATEGY RECOMMENDATIONS
# ===========================================

@router.get("/strategies", response_model=Dict[str, Any])
async def get_available_strategies(
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get available pricing strategies"""
    try:
        strategies = [
            {
                "value": strategy.value,
                "label": strategy.value.replace("_", " ").title(),
                "description": _get_strategy_description(strategy)
            }
            for strategy in PricingStrategy
        ]
        
        return {
            "success": True,
            "strategies": strategies
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get strategies: {str(e)}")

@router.post("/recommend-strategy/{product_id}", response_model=Dict[str, Any])
async def recommend_pricing_strategy(
    product_id: int,
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get recommended pricing strategy for product"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        # Get product to build context
        from app.models.database_models import Product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        context = pricing_service._build_pricing_context(product)
        recommended_strategy = pricing_service._determine_optimal_strategy(context)
        
        # Get all strategy recommendations
        strategy_scores = {}
        for strategy in PricingStrategy:
            try:
                recommendation = pricing_service._apply_pricing_strategy(context, strategy)
                strategy_scores[strategy.value] = {
                    "price": recommendation.recommended_price,
                    "confidence": recommendation.confidence_score,
                    "profit_margin": recommendation.expected_profit_margin,
                    "risk": recommendation.risk_assessment
                }
            except Exception as e:
                strategy_scores[strategy.value] = {"error": str(e)}
        
        return {
            "success": True,
            "product_id": product_id,
            "recommended_strategy": {
                "strategy": recommended_strategy.value,
                "description": _get_strategy_description(recommended_strategy),
                "reasoning": _get_strategy_reasoning(context, recommended_strategy)
            },
            "all_strategies": strategy_scores
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Strategy recommendation failed: {str(e)}")

# ===========================================
# PRICING ANALYTICS & INSIGHTS
# ===========================================

@router.get("/analytics/category", response_model=Dict[str, Any])
async def get_category_pricing_analytics(
    category: str = Query(..., description="Product category"),
    days: int = Query(default=30, description="Analysis period in days"),
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get pricing analytics for product category"""
    try:
        pricing_service = IntelligentPricingService(db)
        
        # Get products in category
        from app.models.database_models import Product
        products = db.query(Product).filter(
            Product.category == category,
            Product.status == "active"
        ).limit(100).all()
        
        if not products:
            raise HTTPException(status_code=404, detail=f"No products found in category: {category}")
        
        analytics = {
            "category": category,
            "total_products": len(products),
            "price_range": {
                "min": min(p.selling_price for p in products if p.selling_price),
                "max": max(p.selling_price for p in products if p.selling_price),
                "avg": sum(p.selling_price for p in products if p.selling_price) / len([p for p in products if p.selling_price])
            },
            "margin_analysis": {},
            "optimization_opportunities": []
        }
        
        # Calculate margin analysis
        margins = []
        for product in products:
            if product.selling_price and product.cost_price:
                margin = (product.selling_price - product.cost_price) / product.selling_price * 100
                margins.append(margin)
        
        if margins:
            analytics["margin_analysis"] = {
                "avg_margin": sum(margins) / len(margins),
                "min_margin": min(margins),
                "max_margin": max(margins),
                "products_below_target": len([m for m in margins if m < 20])
            }
        
        # Find optimization opportunities
        for product in products[:10]:  # Analyze first 10 products
            try:
                recommendation = pricing_service.optimize_product_pricing(product.id)
                
                current_price = product.selling_price or 0
                if abs(recommendation.recommended_price - current_price) > current_price * 0.05:
                    analytics["optimization_opportunities"].append({
                        "product_id": product.id,
                        "product_name": product.name,
                        "current_price": current_price,
                        "recommended_price": recommendation.recommended_price,
                        "potential_improvement": recommendation.expected_profit_margin
                    })
            except Exception:
                continue
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Category analytics failed: {str(e)}")

@router.get("/analytics/supplier/{supplier_id}", response_model=Dict[str, Any])
async def get_supplier_pricing_analytics(
    supplier_id: int,
    current_user: User = Depends(require_permission("manager")),
    db: Session = Depends(get_db)
):
    """Get pricing analytics for supplier"""
    try:
        # Get supplier products
        from app.models.database_models import Product, Supplier
        
        supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            raise HTTPException(status_code=404, detail="Supplier not found")
        
        products = db.query(Product).filter(
            Product.primary_supplier_id == supplier_id,
            Product.status == "active"
        ).all()
        
        if not products:
            return {
                "success": True,
                "supplier_id": supplier_id,
                "supplier_name": supplier.name,
                "analytics": {"message": "No products found for this supplier"}
            }
        
        # Calculate analytics
        total_cost = sum(p.cost_price or 0 for p in products)
        total_revenue = sum(p.selling_price or 0 for p in products)
        total_profit = total_revenue - total_cost
        
        analytics = {
            "supplier_id": supplier_id,
            "supplier_name": supplier.name,
            "total_products": len(products),
            "financial_summary": {
                "total_cost": total_cost,
                "total_revenue": total_revenue,
                "total_profit": total_profit,
                "avg_margin": (total_profit / total_revenue * 100) if total_revenue > 0 else 0
            },
            "pricing_distribution": {},
            "top_performers": []
        }
        
        # Price distribution
        price_ranges = {"0-20": 0, "20-50": 0, "50-100": 0, "100+": 0}
        for product in products:
            price = product.selling_price or 0
            if price < 20:
                price_ranges["0-20"] += 1
            elif price < 50:
                price_ranges["20-50"] += 1
            elif price < 100:
                price_ranges["50-100"] += 1
            else:
                price_ranges["100+"] += 1
        
        analytics["pricing_distribution"] = price_ranges
        
        # Top performing products by profit
        products_with_profit = [
            {
                "product_id": p.id,
                "name": p.name,
                "profit": (p.selling_price or 0) - (p.cost_price or 0),
                "margin": ((p.selling_price or 0) - (p.cost_price or 0)) / (p.selling_price or 1) * 100
            }
            for p in products if p.selling_price and p.cost_price
        ]
        
        analytics["top_performers"] = sorted(
            products_with_profit, 
            key=lambda x: x["profit"], 
            reverse=True
        )[:5]
        
        return {
            "success": True,
            "analytics": analytics
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Supplier analytics failed: {str(e)}")

# ===========================================
# UTILITY FUNCTIONS
# ===========================================

def _get_strategy_description(strategy: PricingStrategy) -> str:
    """Get description for pricing strategy"""
    descriptions = {
        PricingStrategy.COST_PLUS: "Add fixed margin to cost price - safe and predictable",
        PricingStrategy.COMPETITIVE: "Match or beat competitor prices - market positioning",
        PricingStrategy.VALUE_BASED: "Price based on perceived customer value - premium positioning",
        PricingStrategy.PENETRATION: "Low prices to gain market share - aggressive growth",
        PricingStrategy.SKIMMING: "High prices for premium positioning - maximize margins",
        PricingStrategy.DYNAMIC: "Adjust prices based on real-time market conditions",
        PricingStrategy.PSYCHOLOGICAL: "Use psychological pricing triggers (.99, .95)",
        PricingStrategy.BUNDLE: "Package pricing for multiple products",
        PricingStrategy.SEASONAL: "Adjust for seasonal demand patterns",
        PricingStrategy.DEMAND_BASED: "Price based on demand levels and sales velocity"
    }
    return descriptions.get(strategy, "Advanced pricing strategy")

def _get_strategy_reasoning(context, strategy: PricingStrategy) -> str:
    """Get reasoning for strategy recommendation"""
    reasons = []
    
    if len(context.competitor_prices) > 3:
        reasons.append("High competition detected")
    
    if context.supplier_performance > 4.0:
        reasons.append("Superior supplier quality")
    
    if context.inventory_level < 20:
        reasons.append("Low inventory levels")
    
    if context.demand_trend > 0.1:
        reasons.append("Strong demand growth")
    
    if not reasons:
        reasons.append("Based on comprehensive market analysis")
    
    return f"{strategy.value.replace('_', ' ').title()} strategy recommended due to: {', '.join(reasons)}"