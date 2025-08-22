"""
Pricing Analytics API Endpoints - SOLID Architecture
RESTful API for comprehensive pricing optimization and profit analysis
"""

from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.pricing_service import PricingService
from app.schemas.schemas import (
    ProfitAnalysis, APIResponse, PaginationParams
)
from app.core.auth import get_current_user, require_role
from app.models.database_models import User

router = APIRouter(prefix="/pricing", tags=["pricing"])


# ===========================================
# PRICING OPTIMIZATION ENDPOINTS
# ===========================================

@router.post("/optimize/product/{product_id}", response_model=APIResponse)
async def optimize_single_product_price(
    product_id: int,
    target_margin: Optional[float] = Query(None, ge=0, le=100, description="Target profit margin %"),
    market_price: Optional[float] = Query(None, gt=0, description="Current market price"),
    competitive_factor: Optional[float] = Query(None, ge=0, le=1, description="Competitive adjustment factor"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Calculate optimal price for a single product
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Cost-based pricing calculation
    - Performance-based adjustments
    - Competitive positioning
    - Market analysis integration
    """
    try:
        service = PricingService(db)
        optimization = service.calculate_optimal_price(
            product_id=product_id,
            target_margin=target_margin,
            market_price=market_price,
            competitive_factor=competitive_factor
        )
        
        return APIResponse(
            success=True,
            message="Price optimization completed",
            data=optimization
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to optimize product price: {str(e)}"
        )


@router.post("/optimize/bulk", response_model=APIResponse)
async def bulk_price_optimization(
    product_ids: Optional[List[int]] = Body(None, description="Specific product IDs"),
    category: Optional[str] = Body(None, description="Product category to optimize"),
    supplier_id: Optional[int] = Body(None, description="Supplier ID to optimize"),
    target_margin: Optional[float] = Body(None, ge=0, le=100, description="Target profit margin %"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Bulk pricing optimization for multiple products
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Category-wide optimization
    - Supplier-specific optimization
    - Custom product selection
    - Profit impact analysis
    """
    try:
        service = PricingService(db)
        results = service.bulk_price_optimization(
            product_ids=product_ids,
            category=category,
            supplier_id=supplier_id,
            target_margin=target_margin
        )
        
        return APIResponse(
            success=True,
            message=f"Bulk optimization completed: {results['optimized']}/{results['total_products']} products analyzed",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to perform bulk price optimization: {str(e)}"
        )


@router.post("/apply-recommendations", response_model=APIResponse)
async def apply_pricing_recommendations(
    recommendations: List[dict] = Body(..., description="Pricing recommendations to apply"),
    auto_apply_threshold: Optional[float] = Body(10.0, ge=0, description="Auto-apply threshold for margin improvement %"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Apply pricing recommendations to products
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Selective application based on thresholds
    - Batch price updates
    - Price history tracking
    - Safety validation
    """
    try:
        service = PricingService(db)
        results = service.apply_pricing_recommendations(
            recommendations=recommendations,
            auto_apply_threshold=auto_apply_threshold
        )
        
        return APIResponse(
            success=True,
            message=f"Recommendations applied: {results['applied']}/{results['total']} successful",
            data=results
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to apply pricing recommendations: {str(e)}"
        )


# ===========================================
# PROFITABILITY ANALYSIS ENDPOINTS
# ===========================================

@router.get("/profitability/product/{product_id}", response_model=APIResponse)
async def analyze_product_profitability(
    product_id: int,
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Comprehensive profitability analysis for a single product
    
    **Features:**
    - Revenue and cost breakdown
    - Supplier cost comparison
    - Performance metrics
    - Optimization recommendations
    """
    try:
        service = PricingService(db)
        analysis = service.analyze_product_profitability(
            product_id=product_id,
            time_period_days=days
        )
        
        return APIResponse(
            success=True,
            data=analysis
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze product profitability: {str(e)}"
        )


@router.get("/profitability/overview", response_model=APIResponse)
async def get_profit_analysis(
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    category: Optional[str] = Query(None, description="Filter by product category"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive profit analysis across products
    
    **Features:**
    - Portfolio profit overview
    - Top performing products
    - Top performing suppliers
    - Monthly profit trends
    """
    try:
        service = PricingService(db)
        
        date_from = datetime.utcnow() - timedelta(days=days)
        date_to = datetime.utcnow()
        
        analysis = service.get_profit_analysis(
            date_from=date_from,
            date_to=date_to,
            category=category,
            supplier_id=supplier_id
        )
        
        return APIResponse(
            success=True,
            data={
                "analysis_period_days": days,
                "category_filter": category,
                "supplier_filter": supplier_id,
                **analysis.dict()
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profit analysis: {str(e)}"
        )


# ===========================================
# COMPETITIVE PRICING ENDPOINTS
# ===========================================

@router.post("/competitive-analysis/{product_id}", response_model=APIResponse)
async def analyze_competitive_pricing(
    product_id: int,
    competitor_prices: List[float] = Body(..., description="List of competitor prices"),
    market_position: str = Body("competitive", regex="^(premium|competitive|budget)$", description="Desired market position"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["ADMIN", "EBAY_MANAGER"]))
):
    """
    Analyze competitive pricing and suggest positioning
    
    **Required Roles:** ADMIN, EBAY_MANAGER
    
    **Features:**
    - Market position analysis
    - Competitive price benchmarking
    - Positioning recommendations
    - Margin impact assessment
    """
    try:
        if not competitor_prices:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one competitor price is required"
            )
        
        service = PricingService(db)
        analysis = service.analyze_competitive_pricing(
            product_id=product_id,
            competitor_prices=competitor_prices,
            market_position=market_position
        )
        
        return APIResponse(
            success=True,
            message="Competitive analysis completed",
            data=analysis
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze competitive pricing: {str(e)}"
        )


# ===========================================
# COST TRACKING ENDPOINTS
# ===========================================

@router.get("/cost-tracking/product/{product_id}", response_model=APIResponse)
async def track_product_cost_changes(
    product_id: int,
    days: int = Query(90, ge=1, le=365, description="Tracking period in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Track cost changes and supplier performance over time
    
    **Features:**
    - Cost volatility analysis
    - Supplier cost comparison
    - Price trend tracking
    - Optimization recommendations
    """
    try:
        service = PricingService(db)
        analysis = service.track_cost_changes(
            product_id=product_id,
            days=days
        )
        
        return APIResponse(
            success=True,
            data=analysis
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to track cost changes: {str(e)}"
        )


# ===========================================
# PRICING ANALYTICS DASHBOARDS
# ===========================================

@router.get("/analytics/margin-distribution", response_model=APIResponse)
async def get_margin_distribution(
    category: Optional[str] = Query(None, description="Filter by category"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get profit margin distribution across products"""
    try:
        from sqlalchemy import func, case
        from app.models.database_models import Product
        
        query = db.query(
            case(
                (Product.profit_margin_percent < 10, "Low (0-10%)"),
                (Product.profit_margin_percent < 20, "Fair (10-20%)"),
                (Product.profit_margin_percent < 30, "Good (20-30%)"),
                (Product.profit_margin_percent < 40, "Great (30-40%)"),
                else_="Excellent (40%+)"
            ).label('margin_range'),
            func.count(Product.id).label('product_count'),
            func.avg(Product.profit_margin_percent).label('avg_margin'),
            func.sum(Product.selling_price * Product.stock_level).label('total_value')
        ).filter(
            Product.status == "active",
            Product.profit_margin_percent.isnot(None)
        )
        
        if category:
            query = query.filter(Product.category == category)
        
        if supplier_id:
            query = query.filter(
                Product.primary_supplier_id == supplier_id
            )
        
        results = query.group_by(
            case(
                (Product.profit_margin_percent < 10, "Low (0-10%)"),
                (Product.profit_margin_percent < 20, "Fair (10-20%)"),
                (Product.profit_margin_percent < 30, "Good (20-30%)"),
                (Product.profit_margin_percent < 40, "Great (30-40%)"),
                else_="Excellent (40%+)"
            )
        ).all()
        
        distribution = [
            {
                "margin_range": r.margin_range,
                "product_count": r.product_count,
                "avg_margin": round(float(r.avg_margin or 0), 2),
                "total_value": round(float(r.total_value or 0), 2)
            }
            for r in results
        ]
        
        return APIResponse(
            success=True,
            data={
                "category_filter": category,
                "supplier_filter": supplier_id,
                "margin_distribution": distribution
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get margin distribution: {str(e)}"
        )


@router.get("/analytics/price-optimization-opportunities", response_model=APIResponse)
async def get_price_optimization_opportunities(
    min_margin_improvement: float = Query(5.0, ge=0, description="Minimum margin improvement % to include"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of opportunities to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Identify products with significant price optimization opportunities"""
    try:
        from sqlalchemy import func, and_
        from app.models.database_models import Product, SupplierProduct
        
        # Find products with alternative suppliers offering better costs
        opportunities = db.query(
            Product.id,
            Product.sku,
            Product.name,
            Product.cost_price,
            Product.selling_price,
            Product.profit_margin_percent,
            func.min(SupplierProduct.supplier_cost).label('best_cost'),
            (Product.cost_price - func.min(SupplierProduct.supplier_cost)).label('cost_savings'),
            ((Product.selling_price - func.min(SupplierProduct.supplier_cost)) / Product.selling_price * 100).label('potential_margin')
        ).join(
            SupplierProduct, Product.id == SupplierProduct.product_id
        ).filter(
            and_(
                Product.status == "active",
                Product.cost_price.isnot(None),
                Product.selling_price.isnot(None),
                SupplierProduct.status == "active"
            )
        ).group_by(
            Product.id, Product.sku, Product.name, 
            Product.cost_price, Product.selling_price, Product.profit_margin_percent
        ).having(
            func.min(SupplierProduct.supplier_cost) < Product.cost_price * 0.95  # At least 5% cost reduction
        ).order_by(
            (Product.cost_price - func.min(SupplierProduct.supplier_cost)).desc()
        ).limit(limit).all()
        
        optimization_opportunities = [
            {
                "product_id": opp.id,
                "sku": opp.sku,
                "name": opp.name,
                "current_cost": float(opp.cost_price or 0),
                "current_selling_price": float(opp.selling_price or 0),
                "current_margin": float(opp.profit_margin_percent or 0),
                "best_supplier_cost": float(opp.best_cost or 0),
                "cost_savings": float(opp.cost_savings or 0),
                "potential_margin": float(opp.potential_margin or 0),
                "margin_improvement": float(opp.potential_margin or 0) - float(opp.profit_margin_percent or 0)
            }
            for opp in opportunities
            if (float(opp.potential_margin or 0) - float(opp.profit_margin_percent or 0)) >= min_margin_improvement
        ]
        
        return APIResponse(
            success=True,
            data={
                "min_margin_improvement": min_margin_improvement,
                "opportunities_found": len(optimization_opportunities),
                "opportunities": optimization_opportunities
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get price optimization opportunities: {str(e)}"
        )


# ===========================================
# PRICING REPORTS ENDPOINTS
# ===========================================

@router.get("/reports/pricing-summary", response_model=APIResponse)
async def get_pricing_summary_report(
    days: int = Query(30, ge=1, le=365, description="Report period in days"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Generate comprehensive pricing summary report"""
    try:
        from sqlalchemy import func
        from app.models.database_models import Product, PriceHistory
        
        # Get overall pricing metrics
        base_query = db.query(Product).filter(Product.status == "active")
        if category:
            base_query = base_query.filter(Product.category == category)
        
        pricing_stats = base_query.with_entities(
            func.count(Product.id).label('total_products'),
            func.avg(Product.profit_margin_percent).label('avg_margin'),
            func.min(Product.profit_margin_percent).label('min_margin'),
            func.max(Product.profit_margin_percent).label('max_margin'),
            func.sum(Product.selling_price * Product.stock_level).label('total_inventory_value'),
            func.sum((Product.selling_price - Product.cost_price) * Product.stock_level).label('total_potential_profit')
        ).first()
        
        # Get recent price changes
        date_from = datetime.utcnow() - timedelta(days=days)
        recent_changes = db.query(
            func.count(PriceHistory.id).label('price_changes'),
            func.avg(PriceHistory.impact_percent).label('avg_impact'),
            func.count(func.distinct(PriceHistory.product_id)).label('products_changed')
        ).filter(PriceHistory.created_at >= date_from).first()
        
        # Get margin distribution
        margin_dist = base_query.with_entities(
            func.count(case((Product.profit_margin_percent < 20, 1))).label('low_margin'),
            func.count(case(((Product.profit_margin_percent >= 20) & (Product.profit_margin_percent < 30), 1))).label('medium_margin'),
            func.count(case((Product.profit_margin_percent >= 30, 1))).label('high_margin')
        ).first()
        
        report = {
            "report_period_days": days,
            "category_filter": category,
            "pricing_overview": {
                "total_products": pricing_stats.total_products or 0,
                "average_margin": round(float(pricing_stats.avg_margin or 0), 2),
                "min_margin": round(float(pricing_stats.min_margin or 0), 2),
                "max_margin": round(float(pricing_stats.max_margin or 0), 2),
                "total_inventory_value": round(float(pricing_stats.total_inventory_value or 0), 2),
                "total_potential_profit": round(float(pricing_stats.total_potential_profit or 0), 2)
            },
            "recent_activity": {
                "price_changes": recent_changes.price_changes or 0,
                "products_changed": recent_changes.products_changed or 0,
                "avg_price_impact": round(float(recent_changes.avg_impact or 0), 2)
            },
            "margin_distribution": {
                "low_margin_products": margin_dist.low_margin or 0,
                "medium_margin_products": margin_dist.medium_margin or 0,
                "high_margin_products": margin_dist.high_margin or 0
            }
        }
        
        return APIResponse(
            success=True,
            data=report
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate pricing summary report: {str(e)}"
        )