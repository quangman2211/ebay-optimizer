"""
Dashboard Analytics Service - SOLID Architecture Implementation
Handles comprehensive dashboard analytics, real-time metrics, and business intelligence
Single Responsibility: Manages all dashboard-related analytics and KPI calculations
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text
import json

from app.models.database_models import (
    Product, Supplier, SupplierProduct, OrderItem, Order, PriceHistory, User
)
from app.schemas.schemas import (
    SupplierPerformanceStats, ProductPerformanceStats
)


class DashboardAnalyticsService:
    """
    SOLID Principle: Single Responsibility
    Manages comprehensive dashboard analytics, KPIs, and business intelligence
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.default_period_days = 30
        self.kpi_targets = {
            "revenue_growth": 10.0,  # 10% monthly growth target
            "profit_margin": 25.0,   # 25% target profit margin
            "inventory_turnover": 8.0,  # 8x annual turnover target
            "supplier_performance": 4.0,  # 4.0/5.0 average rating target
            "order_fulfillment": 95.0  # 95% on-time delivery target
        }
    
    # ===========================================
    # COMPREHENSIVE DASHBOARD OVERVIEW
    # ===========================================
    
    def get_dashboard_overview(
        self,
        period_days: int = 30,
        include_forecasts: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive dashboard overview with all key metrics"""
        
        date_from = datetime.utcnow() - timedelta(days=period_days)
        date_to = datetime.utcnow()
        
        dashboard_data = {
            "dashboard_date": date_to.isoformat(),
            "period_days": period_days,
            "include_forecasts": include_forecasts,
            "executive_summary": {},
            "financial_metrics": {},
            "operational_metrics": {},
            "supplier_metrics": {},
            "inventory_metrics": {},
            "growth_metrics": {},
            "alerts_and_notifications": [],
            "kpi_scorecard": {},
            "trends": {},
            "forecasts": {} if include_forecasts else None
        }
        
        # Generate all dashboard components
        dashboard_data["executive_summary"] = self._generate_executive_summary(date_from, date_to)
        dashboard_data["financial_metrics"] = self._calculate_financial_metrics(date_from, date_to)
        dashboard_data["operational_metrics"] = self._calculate_operational_metrics(date_from, date_to)
        dashboard_data["supplier_metrics"] = self._calculate_supplier_metrics(date_from, date_to)
        dashboard_data["inventory_metrics"] = self._calculate_inventory_metrics(date_from, date_to)
        dashboard_data["growth_metrics"] = self._calculate_growth_metrics(date_from, date_to, period_days)
        dashboard_data["alerts_and_notifications"] = self._generate_alerts_and_notifications()
        dashboard_data["kpi_scorecard"] = self._generate_kpi_scorecard(dashboard_data)
        dashboard_data["trends"] = self._analyze_trends(date_from, date_to)
        
        if include_forecasts:
            dashboard_data["forecasts"] = self._generate_forecasts(date_from, date_to)
        
        return dashboard_data
    
    def _generate_executive_summary(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Generate executive summary with key highlights"""
        
        # Calculate key metrics
        total_revenue = self._get_total_revenue(date_from, date_to)
        total_orders = self._get_total_orders(date_from, date_to)
        total_products = self._get_active_products_count()
        total_suppliers = self._get_active_suppliers_count()
        
        # Previous period comparison
        period_days = (date_to - date_from).days
        prev_date_from = date_from - timedelta(days=period_days)
        prev_total_revenue = self._get_total_revenue(prev_date_from, date_from)
        
        revenue_growth = ((total_revenue - prev_total_revenue) / prev_total_revenue * 100) if prev_total_revenue > 0 else 0
        
        return {
            "period_revenue": round(total_revenue, 2),
            "revenue_growth_percent": round(revenue_growth, 1),
            "total_orders": total_orders,
            "active_products": total_products,
            "active_suppliers": total_suppliers,
            "avg_order_value": round(total_revenue / total_orders, 2) if total_orders > 0 else 0,
            "key_highlights": [
                f"${total_revenue:,.2f} revenue generated",
                f"{total_orders} orders processed",
                f"{revenue_growth:+.1f}% revenue change vs previous period",
                f"{total_products} active products in catalog"
            ],
            "performance_status": "excellent" if revenue_growth > 15 else "good" if revenue_growth > 5 else "fair" if revenue_growth > -5 else "poor"
        }
    
    def _calculate_financial_metrics(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Calculate comprehensive financial metrics"""
        
        # Revenue and profit analysis
        financial_data = self.db.query(
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.sum(OrderItem.total_cost).label('total_cost'),
            func.count(OrderItem.id).label('total_order_items'),
            func.avg(OrderItem.unit_price).label('avg_unit_price')
        ).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).first()
        
        total_revenue = float(financial_data.total_revenue or 0)
        total_cost = float(financial_data.total_cost or 0)
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Category breakdown
        category_revenue = self.db.query(
            Product.category,
            func.sum(OrderItem.total_price).label('category_revenue')
        ).join(OrderItem, Product.id == OrderItem.product_id) \
         .filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).group_by(Product.category) \
         .order_by(desc(func.sum(OrderItem.total_price))) \
         .limit(10).all()
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "profit_margin_percent": round(profit_margin, 2),
            "avg_unit_price": round(float(financial_data.avg_unit_price or 0), 2),
            "revenue_by_category": [
                {
                    "category": cr.category or "Uncategorized",
                    "revenue": round(float(cr.category_revenue), 2),
                    "percentage": round(float(cr.category_revenue) / total_revenue * 100, 1) if total_revenue > 0 else 0
                }
                for cr in category_revenue
            ],
            "financial_health": {
                "profit_margin_status": "excellent" if profit_margin > 30 else "good" if profit_margin > 20 else "fair" if profit_margin > 10 else "poor",
                "revenue_diversification": len(category_revenue),
                "cost_efficiency": round((1 - total_cost/total_revenue) * 100, 1) if total_revenue > 0 else 0
            }
        }
    
    def _calculate_operational_metrics(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Calculate operational efficiency metrics"""
        
        # Order processing metrics
        order_data = self.db.query(
            func.count(Order.id).label('total_orders'),
            func.count(func.case((Order.status == 'delivered', 1))).label('delivered_orders'),
            func.count(func.case((Order.status == 'cancelled', 1))).label('cancelled_orders'),
            func.avg(
                func.extract('day', Order.delivered_date - Order.created_at)
            ).label('avg_delivery_days')
        ).filter(
            and_(
                Order.created_at >= date_from,
                Order.created_at <= date_to
            )
        ).first()
        
        total_orders = order_data.total_orders or 0
        delivered_orders = order_data.delivered_orders or 0
        cancelled_orders = order_data.cancelled_orders or 0
        
        fulfillment_rate = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
        cancellation_rate = (cancelled_orders / total_orders * 100) if total_orders > 0 else 0
        
        # Product performance
        top_products = self.db.query(
            Product.sku,
            Product.name,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.total_price).label('product_revenue')
        ).join(OrderItem, Product.id == OrderItem.product_id) \
         .filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).group_by(Product.id) \
         .order_by(desc(func.sum(OrderItem.total_price))) \
         .limit(5).all()
        
        return {
            "total_orders": total_orders,
            "fulfillment_rate": round(fulfillment_rate, 1),
            "cancellation_rate": round(cancellation_rate, 1),
            "avg_delivery_days": round(float(order_data.avg_delivery_days or 0), 1),
            "order_processing_efficiency": round((100 - cancellation_rate), 1),
            "top_products": [
                {
                    "sku": tp.sku,
                    "name": tp.name,
                    "units_sold": int(tp.total_sold),
                    "revenue": round(float(tp.product_revenue), 2)
                }
                for tp in top_products
            ],
            "operational_health": {
                "fulfillment_status": "excellent" if fulfillment_rate > 95 else "good" if fulfillment_rate > 90 else "fair" if fulfillment_rate > 85 else "poor",
                "delivery_performance": "excellent" if order_data.avg_delivery_days < 7 else "good" if order_data.avg_delivery_days < 14 else "fair",
                "order_accuracy": round(100 - cancellation_rate, 1)
            }
        }
    
    def _calculate_supplier_metrics(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Calculate supplier performance metrics"""
        
        # Supplier performance
        supplier_data = self.db.query(
            Supplier.id,
            Supplier.company_name,
            func.count(OrderItem.id).label('supplier_orders'),
            func.sum(OrderItem.total_price).label('supplier_revenue'),
            func.avg(Supplier.performance_rating).label('avg_rating')
        ).join(OrderItem, Supplier.id == OrderItem.supplier_id) \
         .filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).group_by(Supplier.id) \
         .order_by(desc(func.sum(OrderItem.total_price))) \
         .limit(10).all()
        
        # Calculate supplier diversity
        total_suppliers_used = len(supplier_data)
        total_active_suppliers = self._get_active_suppliers_count()
        supplier_utilization = (total_suppliers_used / total_active_suppliers * 100) if total_active_suppliers > 0 else 0
        
        # Average supplier performance
        avg_supplier_rating = sum(float(sd.avg_rating or 0) for sd in supplier_data) / len(supplier_data) if supplier_data else 0
        
        return {
            "total_suppliers_used": total_suppliers_used,
            "total_active_suppliers": total_active_suppliers,
            "supplier_utilization_percent": round(supplier_utilization, 1),
            "avg_supplier_rating": round(avg_supplier_rating, 2),
            "top_suppliers": [
                {
                    "supplier_id": sd.id,
                    "company_name": sd.company_name,
                    "orders": sd.supplier_orders,
                    "revenue": round(float(sd.supplier_revenue), 2),
                    "rating": round(float(sd.avg_rating or 0), 2)
                }
                for sd in supplier_data
            ],
            "supplier_health": {
                "diversification": "excellent" if total_suppliers_used > 10 else "good" if total_suppliers_used > 5 else "fair",
                "avg_performance": "excellent" if avg_supplier_rating > 4.5 else "good" if avg_supplier_rating > 4.0 else "fair",
                "utilization_efficiency": round(supplier_utilization, 1)
            }
        }
    
    def _calculate_inventory_metrics(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Calculate inventory management metrics"""
        
        # Inventory levels and turnover
        inventory_data = self.db.query(
            func.count(Product.id).label('total_products'),
            func.sum(Product.stock_level).label('total_stock'),
            func.sum(Product.stock_level * Product.cost_price).label('inventory_value'),
            func.avg(Product.stock_level).label('avg_stock_per_product')
        ).filter(Product.status == "active").first()
        
        # Products needing reorder (simple calculation)
        low_stock_products = self.db.query(func.count(Product.id)).filter(
            and_(
                Product.status == "active",
                Product.stock_level < 10  # Simple low stock threshold
            )
        ).scalar()
        
        # Calculate inventory turnover (simplified)
        total_units_sold = self.db.query(func.sum(OrderItem.quantity)).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).scalar() or 0
        
        avg_inventory = float(inventory_data.avg_stock_per_product or 0)
        inventory_turnover = (total_units_sold / avg_inventory) if avg_inventory > 0 else 0
        
        # Annualized turnover
        period_days = (datetime.utcnow() - date_from).days
        annual_turnover = inventory_turnover * (365 / period_days) if period_days > 0 else 0
        
        return {
            "total_products": inventory_data.total_products or 0,
            "total_stock_units": int(inventory_data.total_stock or 0),
            "inventory_value": round(float(inventory_data.inventory_value or 0), 2),
            "low_stock_products": low_stock_products,
            "inventory_turnover": round(annual_turnover, 2),
            "avg_stock_per_product": round(float(inventory_data.avg_stock_per_product or 0), 1),
            "inventory_health": {
                "turnover_status": "excellent" if annual_turnover > 12 else "good" if annual_turnover > 8 else "fair" if annual_turnover > 4 else "poor",
                "stock_level_status": "attention_needed" if low_stock_products > inventory_data.total_products * 0.1 else "healthy",
                "value_efficiency": round(float(inventory_data.inventory_value or 0) / max(1, inventory_data.total_products or 1), 2)
            }
        }
    
    def _calculate_growth_metrics(
        self, 
        date_from: datetime, 
        date_to: datetime, 
        period_days: int
    ) -> Dict[str, Any]:
        """Calculate growth and trend metrics"""
        
        # Current period metrics
        current_revenue = self._get_total_revenue(date_from, date_to)
        current_orders = self._get_total_orders(date_from, date_to)
        
        # Previous period metrics
        prev_date_from = date_from - timedelta(days=period_days)
        prev_revenue = self._get_total_revenue(prev_date_from, date_from)
        prev_orders = self._get_total_orders(prev_date_from, date_from)
        
        # Calculate growth rates
        revenue_growth = ((current_revenue - prev_revenue) / prev_revenue * 100) if prev_revenue > 0 else 0
        order_growth = ((current_orders - prev_orders) / prev_orders * 100) if prev_orders > 0 else 0
        
        # Month-over-month growth (last 6 months)
        monthly_growth = []
        for i in range(6):
            month_start = datetime.utcnow() - timedelta(days=30 * (i + 1))
            month_end = datetime.utcnow() - timedelta(days=30 * i)
            month_revenue = self._get_total_revenue(month_start, month_end)
            
            monthly_growth.append({
                "month": month_start.strftime("%Y-%m"),
                "revenue": round(month_revenue, 2)
            })
        
        monthly_growth.reverse()  # Chronological order
        
        return {
            "revenue_growth_percent": round(revenue_growth, 1),
            "order_growth_percent": round(order_growth, 1),
            "current_period": {
                "revenue": round(current_revenue, 2),
                "orders": current_orders
            },
            "previous_period": {
                "revenue": round(prev_revenue, 2),
                "orders": prev_orders
            },
            "monthly_trend": monthly_growth,
            "growth_health": {
                "revenue_trend": "strong" if revenue_growth > 10 else "moderate" if revenue_growth > 0 else "declining",
                "order_trend": "growing" if order_growth > 5 else "stable" if order_growth > -5 else "declining",
                "overall_trajectory": "positive" if revenue_growth > 0 and order_growth > 0 else "mixed"
            }
        }
    
    def _generate_alerts_and_notifications(self) -> List[Dict[str, Any]]:
        """Generate critical alerts and notifications"""
        
        alerts = []
        current_time = datetime.utcnow()
        
        # Low stock alerts
        low_stock_products = self.db.query(Product).filter(
            and_(
                Product.status == "active",
                Product.stock_level < 5
            )
        ).limit(10).all()
        
        if low_stock_products:
            alerts.append({
                "type": "inventory",
                "severity": "high",
                "title": "Low Stock Alert",
                "message": f"{len(low_stock_products)} products have critically low stock",
                "action_required": "Review inventory and reorder",
                "products_affected": [p.sku for p in low_stock_products[:5]]
            })
        
        # Poor performing suppliers (simplified check)
        poor_suppliers = self.db.query(Supplier).filter(
            Supplier.performance_rating < 3.0
        ).limit(5).all()
        
        if poor_suppliers:
            alerts.append({
                "type": "supplier",
                "severity": "medium",
                "title": "Supplier Performance Issues",
                "message": f"{len(poor_suppliers)} suppliers have low performance ratings",
                "action_required": "Review supplier performance and consider alternatives",
                "suppliers_affected": [s.company_name for s in poor_suppliers]
            })
        
        # Recent order growth check
        last_week = current_time - timedelta(days=7)
        last_two_weeks = current_time - timedelta(days=14)
        
        recent_orders = self._get_total_orders(last_week, current_time)
        previous_week_orders = self._get_total_orders(last_two_weeks, last_week)
        
        if recent_orders < previous_week_orders * 0.8:  # 20% decline
            alerts.append({
                "type": "performance",
                "severity": "medium",
                "title": "Order Volume Decline",
                "message": f"Order volume down {((previous_week_orders - recent_orders) / previous_week_orders * 100):.1f}% this week",
                "action_required": "Investigate cause of order decline",
                "metrics": {
                    "current_week": recent_orders,
                    "previous_week": previous_week_orders
                }
            })
        
        return alerts
    
    def _generate_kpi_scorecard(self, dashboard_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate KPI scorecard with target comparisons"""
        
        financial = dashboard_data.get("financial_metrics", {})
        operational = dashboard_data.get("operational_metrics", {})
        supplier = dashboard_data.get("supplier_metrics", {})
        inventory = dashboard_data.get("inventory_metrics", {})
        growth = dashboard_data.get("growth_metrics", {})
        
        kpis = {
            "revenue_growth": {
                "actual": growth.get("revenue_growth_percent", 0),
                "target": self.kpi_targets["revenue_growth"],
                "status": "on_track",
                "unit": "%"
            },
            "profit_margin": {
                "actual": financial.get("profit_margin_percent", 0),
                "target": self.kpi_targets["profit_margin"],
                "status": "on_track",
                "unit": "%"
            },
            "inventory_turnover": {
                "actual": inventory.get("inventory_turnover", 0),
                "target": self.kpi_targets["inventory_turnover"],
                "status": "on_track",
                "unit": "x"
            },
            "supplier_performance": {
                "actual": supplier.get("avg_supplier_rating", 0),
                "target": self.kpi_targets["supplier_performance"],
                "status": "on_track",
                "unit": "/5.0"
            },
            "order_fulfillment": {
                "actual": operational.get("fulfillment_rate", 0),
                "target": self.kpi_targets["order_fulfillment"],
                "status": "on_track",
                "unit": "%"
            }
        }
        
        # Determine status for each KPI
        for kpi_name, kpi_data in kpis.items():
            actual = kpi_data["actual"]
            target = kpi_data["target"]
            
            if actual >= target:
                kpi_data["status"] = "exceeding"
            elif actual >= target * 0.9:  # Within 90% of target
                kpi_data["status"] = "on_track"
            elif actual >= target * 0.8:  # Within 80% of target
                kpi_data["status"] = "at_risk"
            else:
                kpi_data["status"] = "below_target"
            
            kpi_data["percentage_of_target"] = round((actual / target * 100), 1) if target > 0 else 0
        
        # Overall scorecard health
        exceeding = sum(1 for kpi in kpis.values() if kpi["status"] == "exceeding")
        on_track = sum(1 for kpi in kpis.values() if kpi["status"] == "on_track")
        total_kpis = len(kpis)
        
        overall_health = "excellent" if (exceeding + on_track) / total_kpis > 0.8 else "good" if (exceeding + on_track) / total_kpis > 0.6 else "needs_attention"
        
        return {
            "kpis": kpis,
            "overall_health": overall_health,
            "summary": {
                "exceeding_target": exceeding,
                "on_track": on_track,
                "at_risk": sum(1 for kpi in kpis.values() if kpi["status"] == "at_risk"),
                "below_target": sum(1 for kpi in kpis.values() if kpi["status"] == "below_target")
            }
        }
    
    def _analyze_trends(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Analyze trends across different time periods"""
        
        # Daily trends for the period
        daily_trends = self.db.query(
            func.date(OrderItem.created_at).label('order_date'),
            func.sum(OrderItem.total_price).label('daily_revenue'),
            func.count(OrderItem.id).label('daily_orders')
        ).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).group_by(func.date(OrderItem.created_at)) \
         .order_by(func.date(OrderItem.created_at)).all()
        
        trend_data = [
            {
                "date": trend.order_date.strftime("%Y-%m-%d"),
                "revenue": round(float(trend.daily_revenue), 2),
                "orders": trend.daily_orders
            }
            for trend in daily_trends
        ]
        
        # Calculate trend direction
        if len(trend_data) >= 7:
            recent_avg = sum(t["revenue"] for t in trend_data[-7:]) / 7
            earlier_avg = sum(t["revenue"] for t in trend_data[:7]) / 7
            trend_direction = "increasing" if recent_avg > earlier_avg * 1.05 else "decreasing" if recent_avg < earlier_avg * 0.95 else "stable"
        else:
            trend_direction = "insufficient_data"
        
        return {
            "daily_trends": trend_data,
            "trend_direction": trend_direction,
            "trend_analysis": {
                "data_points": len(trend_data),
                "avg_daily_revenue": round(sum(t["revenue"] for t in trend_data) / len(trend_data), 2) if trend_data else 0,
                "avg_daily_orders": round(sum(t["orders"] for t in trend_data) / len(trend_data), 1) if trend_data else 0
            }
        }
    
    def _generate_forecasts(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> Dict[str, Any]:
        """Generate simple forecasts based on trends"""
        
        # Get historical data for forecasting
        period_days = (date_to - date_from).days
        
        # Simple linear projection based on recent growth
        current_revenue = self._get_total_revenue(date_from, date_to)
        prev_date_from = date_from - timedelta(days=period_days)
        prev_revenue = self._get_total_revenue(prev_date_from, date_from)
        
        growth_rate = ((current_revenue - prev_revenue) / prev_revenue) if prev_revenue > 0 else 0
        
        # Forecast next period (same length)
        next_period_forecast = current_revenue * (1 + growth_rate)
        
        # Monthly forecasts (next 3 months)
        monthly_forecasts = []
        base_monthly_revenue = current_revenue * (30 / period_days)  # Normalize to monthly
        
        for i in range(3):
            month_forecast = base_monthly_revenue * ((1 + growth_rate) ** (i + 1))
            monthly_forecasts.append({
                "month": (datetime.utcnow() + timedelta(days=30 * (i + 1))).strftime("%Y-%m"),
                "forecasted_revenue": round(month_forecast, 2),
                "confidence": "medium" if abs(growth_rate) < 0.5 else "low"
            })
        
        return {
            "next_period_forecast": {
                "forecasted_revenue": round(next_period_forecast, 2),
                "growth_rate_applied": round(growth_rate * 100, 1),
                "confidence": "medium"
            },
            "monthly_forecasts": monthly_forecasts,
            "forecast_assumptions": [
                "Based on linear growth extrapolation",
                "Assumes current market conditions continue",
                "Does not account for seasonal variations",
                "Confidence decreases with forecast horizon"
            ]
        }
    
    # ===========================================
    # HELPER METHODS
    # ===========================================
    
    def _get_total_revenue(self, date_from: datetime, date_to: datetime) -> float:
        """Get total revenue for period"""
        result = self.db.query(func.sum(OrderItem.total_price)).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).scalar()
        return float(result or 0)
    
    def _get_total_orders(self, date_from: datetime, date_to: datetime) -> int:
        """Get total order count for period"""
        result = self.db.query(func.count(func.distinct(Order.id))).join(
            OrderItem, Order.id == OrderItem.order_id
        ).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).scalar()
        return int(result or 0)
    
    def _get_active_products_count(self) -> int:
        """Get count of active products"""
        result = self.db.query(func.count(Product.id)).filter(
            Product.status == "active"
        ).scalar()
        return int(result or 0)
    
    def _get_active_suppliers_count(self) -> int:
        """Get count of active suppliers"""
        result = self.db.query(func.count(Supplier.id)).filter(
            Supplier.status == "active"
        ).scalar()
        return int(result or 0)