"""
Inventory Management API Endpoints - SOLID Architecture Implementation
Provides automated reorder point calculations and inventory optimization endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.inventory_management_service import InventoryManagementService

router = APIRouter()


# ===========================================
# AUTOMATED REORDER POINT CALCULATIONS
# ===========================================

@router.get("/inventory/reorder-points")
async def calculate_reorder_points(
    product_ids: Optional[List[int]] = Query(None, description="Specific product IDs (optional)"),
    service_level: int = Query(95, description="Target service level percentage", ge=85, le=99),
    include_seasonality: bool = Query(True, description="Include seasonality adjustments"),
    db: Session = Depends(get_db)
):
    """
    Calculate automated reorder points for products
    
    Returns:
    - Reorder points for each product
    - Safety stock calculations
    - Demand analysis and trends
    - Supplier lead time analysis
    - Economic order quantities (EOQ)
    """
    try:
        inventory_service = InventoryManagementService(db)
        reorder_data = inventory_service.calculate_reorder_points(
            product_ids=product_ids,
            service_level=service_level,
            include_seasonality=include_seasonality
        )
        
        return {
            "success": True,
            "data": reorder_data,
            "message": f"Reorder points calculated for {reorder_data['summary']['calculated']} products"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate reorder points: {str(e)}")


@router.get("/inventory/reorder-points/{product_id}")
async def get_product_reorder_point(
    product_id: int,
    service_level: int = Query(95, description="Target service level percentage", ge=85, le=99),
    include_seasonality: bool = Query(True, description="Include seasonality adjustments"),
    db: Session = Depends(get_db)
):
    """
    Get detailed reorder point calculation for a specific product
    
    Returns:
    - Detailed reorder point analysis
    - Demand patterns and seasonality
    - Supplier lead time breakdown
    - Cost impact analysis
    """
    try:
        inventory_service = InventoryManagementService(db)
        
        # Get the product
        from app.models.database_models import Product
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {product_id} not found")
        
        # Calculate reorder point
        z_score = inventory_service.service_level_z_scores.get(service_level, 1.65)
        reorder_data = inventory_service._calculate_product_reorder_point(
            product, z_score, include_seasonality
        )
        
        if not reorder_data:
            raise HTTPException(
                status_code=400, 
                detail="Insufficient data to calculate reorder point for this product"
            )
        
        return {
            "success": True,
            "data": reorder_data,
            "message": f"Reorder point calculated for product {product_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate reorder point: {str(e)}")


# ===========================================
# INVENTORY OPTIMIZATION
# ===========================================

@router.post("/inventory/optimize")
async def optimize_inventory_levels(
    target_service_level: int = Query(95, description="Target service level percentage", ge=85, le=99),
    max_inventory_investment: Optional[float] = Query(None, description="Maximum inventory investment limit"),
    db: Session = Depends(get_db)
):
    """
    Optimize inventory levels across all products
    
    Returns:
    - Current vs optimized inventory levels
    - Investment requirements and savings
    - Optimization recommendations
    - Product-specific adjustments
    """
    try:
        inventory_service = InventoryManagementService(db)
        optimization_data = inventory_service.optimize_inventory_levels(
            target_service_level=target_service_level,
            max_inventory_investment=max_inventory_investment
        )
        
        return {
            "success": True,
            "data": optimization_data,
            "message": f"Inventory optimization completed for {optimization_data['summary']['total_products']} products"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to optimize inventory: {str(e)}")


@router.get("/inventory/analytics/demand-forecast")
async def get_demand_forecast(
    product_ids: Optional[List[int]] = Query(None, description="Specific product IDs (optional)"),
    forecast_days: int = Query(30, description="Forecast period in days", ge=7, le=365),
    include_seasonality: bool = Query(True, description="Include seasonality in forecast"),
    db: Session = Depends(get_db)
):
    """
    Generate demand forecasts for products
    
    Returns:
    - Demand forecasts for specified period
    - Confidence intervals
    - Seasonal adjustments
    - Trend analysis
    """
    try:
        inventory_service = InventoryManagementService(db)
        
        # Get products
        from app.models.database_models import Product
        if product_ids:
            products = db.query(Product).filter(Product.id.in_(product_ids)).all()
        else:
            products = db.query(Product).filter(Product.status == "active").limit(50).all()
        
        forecast_data = {
            "forecast_date": inventory_service.db.query.func.now(),
            "forecast_days": forecast_days,
            "include_seasonality": include_seasonality,
            "products_analyzed": len(products),
            "forecasts": []
        }
        
        for product in products:
            # Analyze demand
            demand_data = inventory_service._analyze_product_demand(product.id)
            if not demand_data:
                continue
            
            avg_daily_demand = demand_data["avg_daily_demand"]
            demand_std_dev = demand_data["demand_std_dev"]
            
            # Apply seasonality if requested
            if include_seasonality:
                seasonality_factor = inventory_service._calculate_seasonality_factor(product.id)
                avg_daily_demand *= seasonality_factor
            
            # Generate forecast
            forecast_total = avg_daily_demand * forecast_days
            
            # Calculate confidence intervals (assuming normal distribution)
            forecast_std_dev = demand_std_dev * (forecast_days ** 0.5)
            confidence_95_lower = forecast_total - (1.96 * forecast_std_dev)
            confidence_95_upper = forecast_total + (1.96 * forecast_std_dev)
            
            forecast_data["forecasts"].append({
                "product_id": product.id,
                "sku": product.sku,
                "product_name": product.name,
                "avg_daily_demand": round(avg_daily_demand, 2),
                "forecast_total": round(forecast_total, 0),
                "confidence_intervals": {
                    "lower_95": max(0, round(confidence_95_lower, 0)),
                    "upper_95": round(confidence_95_upper, 0)
                },
                "demand_trend": demand_data["demand_trend"],
                "seasonality_applied": include_seasonality
            })
        
        return {
            "success": True,
            "data": forecast_data,
            "message": f"Demand forecast generated for {len(forecast_data['forecasts'])} products"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate demand forecast: {str(e)}")


# ===========================================
# PURCHASE ORDER GENERATION
# ===========================================

@router.post("/inventory/purchase-orders/generate")
async def generate_purchase_orders(
    urgency_levels: List[str] = Query(["critical", "urgent"], description="Urgency levels to include"),
    auto_generate: bool = Query(False, description="Automatically generate orders"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Generate purchase orders based on reorder points
    
    Returns:
    - Purchase orders grouped by supplier
    - Order quantities and values
    - Product priorities and urgency levels
    - Supplier contact information
    """
    try:
        inventory_service = InventoryManagementService(db)
        purchase_orders = inventory_service.generate_purchase_orders(
            urgency_levels=urgency_levels,
            auto_generate=auto_generate
        )
        
        if auto_generate and purchase_orders["purchase_orders"]:
            # In a real implementation, this would trigger automated order creation
            background_tasks.add_task(
                _process_automated_orders, 
                purchase_orders["purchase_orders"]
            )
        
        return {
            "success": True,
            "data": purchase_orders,
            "message": f"Generated {len(purchase_orders['purchase_orders'])} purchase orders for {purchase_orders['products_to_reorder']} products"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate purchase orders: {str(e)}")


async def _process_automated_orders(purchase_orders: List[Dict[str, Any]]):
    """Background task to process automated purchase orders"""
    # This would integrate with supplier systems, send emails, etc.
    # For now, it's a placeholder for the automation logic
    pass


@router.get("/inventory/stock-alerts")
async def get_stock_alerts(
    urgency_level: Optional[str] = Query(None, description="Filter by urgency level"),
    days_of_supply_threshold: int = Query(7, description="Days of supply threshold for alerts"),
    db: Session = Depends(get_db)
):
    """
    Get stock alerts for products requiring attention
    
    Returns:
    - Products with low stock levels
    - Urgency classifications
    - Days of supply remaining
    - Recommended actions
    """
    try:
        inventory_service = InventoryManagementService(db)
        
        # Calculate reorder points to identify alerts
        reorder_data = inventory_service.calculate_reorder_points()
        
        # Filter products that need attention
        stock_alerts = []
        
        for product_data in reorder_data["reorder_points"]:
            days_of_supply = product_data["inventory_metrics"]["days_of_supply"]
            urgency = product_data["urgency_level"]
            
            # Apply filters
            if urgency_level and urgency != urgency_level:
                continue
            
            if days_of_supply <= days_of_supply_threshold or product_data["reorder_needed"]:
                alert = {
                    "product_id": product_data["product_id"],
                    "sku": product_data["sku"],
                    "product_name": product_data["product_name"],
                    "current_stock": product_data["current_stock"],
                    "reorder_point": product_data["reorder_point"],
                    "days_of_supply": days_of_supply,
                    "urgency_level": urgency,
                    "reorder_needed": product_data["reorder_needed"],
                    "recommended_order_qty": product_data["eoq"],
                    "supplier_info": product_data.get("supplier_analysis", {}),
                    "cost_impact": product_data.get("cost_impact", {})
                }
                
                # Add recommended action
                if urgency == "critical":
                    alert["recommended_action"] = "Immediate reorder required - stock depleted"
                elif urgency == "urgent":
                    alert["recommended_action"] = "Urgent reorder - will stock out soon"
                elif urgency == "normal":
                    alert["recommended_action"] = "Schedule reorder within lead time"
                else:
                    alert["recommended_action"] = "Monitor stock levels"
                
                stock_alerts.append(alert)
        
        # Sort by urgency and days of supply
        urgency_order = {"critical": 0, "urgent": 1, "normal": 2, "low": 3}
        stock_alerts.sort(key=lambda x: (urgency_order.get(x["urgency_level"], 4), x["days_of_supply"]))
        
        alert_summary = {
            "alert_date": inventory_service.db.query.func.now(),
            "total_alerts": len(stock_alerts),
            "urgency_breakdown": {
                "critical": len([a for a in stock_alerts if a["urgency_level"] == "critical"]),
                "urgent": len([a for a in stock_alerts if a["urgency_level"] == "urgent"]),
                "normal": len([a for a in stock_alerts if a["urgency_level"] == "normal"]),
                "low": len([a for a in stock_alerts if a["urgency_level"] == "low"])
            },
            "alerts": stock_alerts
        }
        
        return {
            "success": True,
            "data": alert_summary,
            "message": f"Found {len(stock_alerts)} stock alerts requiring attention"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stock alerts: {str(e)}")


# ===========================================
# INVENTORY REPORTS
# ===========================================

@router.get("/inventory/reports/turnover-analysis")
async def get_inventory_turnover_analysis(
    period_days: int = Query(365, description="Analysis period in days", ge=30, le=730),
    category: Optional[str] = Query(None, description="Product category filter"),
    db: Session = Depends(get_db)
):
    """
    Generate inventory turnover analysis report
    
    Returns:
    - Inventory turnover rates by product
    - Fast and slow moving items
    - Optimization recommendations
    - Category performance breakdown
    """
    try:
        inventory_service = InventoryManagementService(db)
        
        # Get reorder data with turnover calculations
        reorder_data = inventory_service.calculate_reorder_points()
        
        turnover_analysis = {
            "analysis_date": inventory_service.db.query.func.now(),
            "period_days": period_days,
            "category_filter": category,
            "products_analyzed": len(reorder_data["reorder_points"]),
            "turnover_summary": {
                "avg_turnover": 0.0,
                "fast_movers": 0,  # >12x per year
                "medium_movers": 0,  # 4-12x per year
                "slow_movers": 0  # <4x per year
            },
            "product_analysis": [],
            "recommendations": []
        }
        
        turnover_rates = []
        
        for product_data in reorder_data["reorder_points"]:
            turnover_rate = product_data["inventory_metrics"]["inventory_turnover"]
            turnover_rates.append(turnover_rate)
            
            # Categorize turnover
            if turnover_rate > 12:
                turnover_category = "fast"
                turnover_analysis["turnover_summary"]["fast_movers"] += 1
            elif turnover_rate >= 4:
                turnover_category = "medium"
                turnover_analysis["turnover_summary"]["medium_movers"] += 1
            else:
                turnover_category = "slow"
                turnover_analysis["turnover_summary"]["slow_movers"] += 1
            
            turnover_analysis["product_analysis"].append({
                "product_id": product_data["product_id"],
                "sku": product_data["sku"],
                "product_name": product_data["product_name"],
                "turnover_rate": round(turnover_rate, 2),
                "turnover_category": turnover_category,
                "current_stock": product_data["current_stock"],
                "days_of_supply": product_data["inventory_metrics"]["days_of_supply"],
                "inventory_value": product_data["cost_impact"]["inventory_value"]
            })
        
        # Calculate average turnover
        if turnover_rates:
            turnover_analysis["turnover_summary"]["avg_turnover"] = round(
                sum(turnover_rates) / len(turnover_rates), 2
            )
        
        # Generate recommendations
        slow_movers = turnover_analysis["turnover_summary"]["slow_movers"]
        if slow_movers > 0:
            turnover_analysis["recommendations"].append(
                f"Review {slow_movers} slow-moving products - consider reducing stock levels or discontinuing"
            )
        
        fast_movers = turnover_analysis["turnover_summary"]["fast_movers"]
        if fast_movers > 0:
            turnover_analysis["recommendations"].append(
                f"Optimize stock levels for {fast_movers} fast-moving products to prevent stockouts"
            )
        
        # Sort by turnover rate
        turnover_analysis["product_analysis"].sort(
            key=lambda x: x["turnover_rate"], reverse=True
        )
        
        return {
            "success": True,
            "data": turnover_analysis,
            "message": f"Inventory turnover analysis completed for {len(reorder_data['reorder_points'])} products"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate turnover analysis: {str(e)}")


@router.get("/inventory/reports/abc-analysis")
async def get_abc_analysis(
    period_days: int = Query(365, description="Analysis period in days", ge=30, le=730),
    db: Session = Depends(get_db)
):
    """
    Generate ABC analysis for inventory classification
    
    Returns:
    - Products classified into A, B, C categories
    - Revenue contribution analysis
    - Inventory management recommendations
    - Optimal stock level suggestions by category
    """
    try:
        from app.models.database_models import Product, OrderItem
        from datetime import datetime, timedelta
        
        date_from = datetime.utcnow() - timedelta(days=period_days)
        
        # Get product sales data
        product_sales = db.query(
            Product.id,
            Product.sku,
            Product.name,
            Product.cost_price,
            Product.selling_price,
            Product.stock_level,
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.sum(OrderItem.quantity).label('total_quantity')
        ).join(OrderItem, Product.id == OrderItem.product_id) \
         .filter(OrderItem.created_at >= date_from) \
         .group_by(Product.id) \
         .all()
        
        if not product_sales:
            return {
                "success": True,
                "data": {
                    "analysis_date": datetime.utcnow().isoformat(),
                    "period_days": period_days,
                    "products_analyzed": 0,
                    "abc_classification": {"A": [], "B": [], "C": []},
                    "summary": {"A": 0, "B": 0, "C": 0},
                    "recommendations": ["No sales data available for ABC analysis"]
                },
                "message": "No sales data available for ABC analysis"
            }
        
        # Calculate cumulative revenue percentages
        products_with_revenue = [
            {
                "product_id": ps.id,
                "sku": ps.sku,
                "product_name": ps.name,
                "total_revenue": float(ps.total_revenue or 0),
                "total_quantity": int(ps.total_quantity or 0),
                "unit_cost": float(ps.cost_price or 0),
                "unit_price": float(ps.selling_price or 0),
                "current_stock": ps.stock_level or 0
            }
            for ps in product_sales
        ]
        
        # Sort by revenue descending
        products_with_revenue.sort(key=lambda x: x["total_revenue"], reverse=True)
        
        # Calculate total revenue
        total_revenue = sum(p["total_revenue"] for p in products_with_revenue)
        
        # Classify products
        abc_classification = {"A": [], "B": [], "C": []}
        cumulative_revenue = 0.0
        
        for product in products_with_revenue:
            cumulative_revenue += product["total_revenue"]
            cumulative_percentage = (cumulative_revenue / total_revenue * 100) if total_revenue > 0 else 0
            
            product["cumulative_percentage"] = round(cumulative_percentage, 2)
            product["revenue_percentage"] = round((product["total_revenue"] / total_revenue * 100), 2) if total_revenue > 0 else 0
            
            # ABC classification rules:
            # A items: Top 20% of products contributing to 80% of revenue
            # B items: Next 30% of products contributing to 15% of revenue  
            # C items: Remaining 50% of products contributing to 5% of revenue
            
            if cumulative_percentage <= 80:
                category = "A"
            elif cumulative_percentage <= 95:
                category = "B"
            else:
                category = "C"
            
            product["abc_category"] = category
            abc_classification[category].append(product)
        
        # Generate recommendations by category
        recommendations = []
        
        if abc_classification["A"]:
            recommendations.append(f"A-category ({len(abc_classification['A'])} products): Maintain high service levels, frequent monitoring, tight inventory control")
        
        if abc_classification["B"]:
            recommendations.append(f"B-category ({len(abc_classification['B'])} products): Moderate service levels, periodic review, balanced inventory")
        
        if abc_classification["C"]:
            recommendations.append(f"C-category ({len(abc_classification['C'])} products): Lower service levels, bulk ordering, minimal inventory")
        
        abc_analysis = {
            "analysis_date": datetime.utcnow().isoformat(),
            "period_days": period_days,
            "total_revenue": round(total_revenue, 2),
            "products_analyzed": len(products_with_revenue),
            "abc_classification": abc_classification,
            "summary": {
                "A": len(abc_classification["A"]),
                "B": len(abc_classification["B"]),
                "C": len(abc_classification["C"])
            },
            "revenue_distribution": {
                "A": round(sum(p["total_revenue"] for p in abc_classification["A"]) / total_revenue * 100, 1) if total_revenue > 0 else 0,
                "B": round(sum(p["total_revenue"] for p in abc_classification["B"]) / total_revenue * 100, 1) if total_revenue > 0 else 0,
                "C": round(sum(p["total_revenue"] for p in abc_classification["C"]) / total_revenue * 100, 1) if total_revenue > 0 else 0
            },
            "recommendations": recommendations
        }
        
        return {
            "success": True,
            "data": abc_analysis,
            "message": f"ABC analysis completed for {len(products_with_revenue)} products"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate ABC analysis: {str(e)}")