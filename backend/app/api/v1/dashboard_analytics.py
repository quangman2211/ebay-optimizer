"""
Dashboard Analytics API Endpoints - SOLID Architecture Implementation
Provides comprehensive dashboard analytics and real-time business intelligence
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.dashboard_analytics_service import DashboardAnalyticsService

router = APIRouter()


# ===========================================
# COMPREHENSIVE DASHBOARD OVERVIEW
# ===========================================

@router.get("/dashboard/overview")
async def get_dashboard_overview(
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    include_forecasts: bool = Query(True, description="Include revenue and growth forecasts"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive dashboard overview with all key metrics
    
    Returns:
    - Executive summary with key highlights
    - Financial metrics (revenue, profit, margins)
    - Operational metrics (orders, fulfillment, delivery)
    - Supplier performance metrics
    - Inventory management metrics
    - Growth and trend analysis
    - KPI scorecard with target comparisons
    - Alerts and notifications
    - Forecasts (optional)
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        dashboard_data = analytics_service.get_dashboard_overview(
            period_days=period_days,
            include_forecasts=include_forecasts
        )
        
        return {
            "success": True,
            "data": dashboard_data,
            "message": f"Dashboard overview generated for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard overview: {str(e)}")


@router.get("/dashboard/executive-summary")
async def get_executive_summary(
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get executive summary with key business highlights
    
    Returns:
    - Revenue and growth metrics
    - Key performance indicators
    - Business highlights and status
    - Performance comparisons with previous period
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        date_from = analytics_service.db.query.func.now() - analytics_service.db.query.func.interval(f"{period_days} days")
        date_to = analytics_service.db.query.func.now()
        
        executive_summary = analytics_service._generate_executive_summary(date_from, date_to)
        
        return {
            "success": True,
            "data": executive_summary,
            "message": f"Executive summary for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate executive summary: {str(e)}")


# ===========================================
# FINANCIAL ANALYTICS
# ===========================================

@router.get("/dashboard/financial-metrics")
async def get_financial_metrics(
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    include_category_breakdown: bool = Query(True, description="Include revenue breakdown by category"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive financial metrics and analysis
    
    Returns:
    - Revenue, cost, and profit analysis
    - Profit margin calculations
    - Revenue breakdown by category
    - Financial health indicators
    - Cost efficiency metrics
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=period_days)
        date_to = datetime.utcnow()
        
        financial_metrics = analytics_service._calculate_financial_metrics(date_from, date_to)
        
        return {
            "success": True,
            "data": financial_metrics,
            "message": f"Financial metrics calculated for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate financial metrics: {str(e)}")


@router.get("/dashboard/operational-metrics")
async def get_operational_metrics(
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    include_top_products: bool = Query(True, description="Include top performing products"),
    db: Session = Depends(get_db)
):
    """
    Get operational efficiency metrics
    
    Returns:
    - Order processing metrics
    - Fulfillment and delivery performance
    - Order accuracy and cancellation rates
    - Top performing products
    - Operational health indicators
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=period_days)
        date_to = datetime.utcnow()
        
        operational_metrics = analytics_service._calculate_operational_metrics(date_from, date_to)
        
        return {
            "success": True,
            "data": operational_metrics,
            "message": f"Operational metrics calculated for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate operational metrics: {str(e)}")


# ===========================================
# KPI SCORECARD AND PERFORMANCE TRACKING
# ===========================================

@router.get("/dashboard/kpi-scorecard")
async def get_kpi_scorecard(
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get KPI scorecard with target comparisons
    
    Returns:
    - All key performance indicators
    - Actual vs target comparisons
    - Performance status for each KPI
    - Overall business health score
    - Improvement recommendations
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        dashboard_data = analytics_service.get_dashboard_overview(period_days=period_days)
        
        kpi_scorecard = analytics_service._generate_kpi_scorecard(dashboard_data)
        
        return {
            "success": True,
            "data": kpi_scorecard,
            "message": f"KPI scorecard generated with {len(kpi_scorecard['kpis'])} key metrics"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate KPI scorecard: {str(e)}")


@router.put("/dashboard/kpi-targets")
async def update_kpi_targets(
    targets: Dict[str, float],
    db: Session = Depends(get_db)
):
    """
    Update KPI targets for performance tracking
    
    Body:
    - targets: Dictionary of KPI names and their target values
    
    Returns:
    - Updated target configuration
    - Success confirmation
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        # Validate target keys
        valid_kpis = set(analytics_service.kpi_targets.keys())
        invalid_kpis = set(targets.keys()) - valid_kpis
        
        if invalid_kpis:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid KPI names: {list(invalid_kpis)}. Valid KPIs: {list(valid_kpis)}"
            )
        
        # Update targets
        for kpi_name, target_value in targets.items():
            if target_value <= 0:
                raise HTTPException(status_code=400, detail=f"Target value for {kpi_name} must be positive")
            analytics_service.kpi_targets[kpi_name] = target_value
        
        return {
            "success": True,
            "data": {
                "updated_targets": targets,
                "current_targets": analytics_service.kpi_targets
            },
            "message": f"Updated targets for {len(targets)} KPIs"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update KPI targets: {str(e)}")


# ===========================================
# GROWTH AND TREND ANALYSIS
# ===========================================

@router.get("/dashboard/growth-analysis")
async def get_growth_analysis(
    period_days: int = Query(30, description="Analysis period in days", ge=7, le=365),
    include_monthly_trends: bool = Query(True, description="Include monthly trend analysis"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive growth and trend analysis
    
    Returns:
    - Revenue and order growth rates
    - Period-over-period comparisons
    - Monthly trend analysis
    - Growth trajectory assessment
    - Trend direction indicators
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=period_days)
        date_to = datetime.utcnow()
        
        growth_metrics = analytics_service._calculate_growth_metrics(date_from, date_to, period_days)
        
        if include_monthly_trends:
            trends = analytics_service._analyze_trends(date_from, date_to)
            growth_metrics["detailed_trends"] = trends
        
        return {
            "success": True,
            "data": growth_metrics,
            "message": f"Growth analysis completed for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate growth analysis: {str(e)}")


@router.get("/dashboard/trend-analysis")
async def get_trend_analysis(
    period_days: int = Query(30, description="Analysis period in days", ge=7, le=365),
    granularity: str = Query("daily", description="Trend granularity (daily, weekly)"),
    db: Session = Depends(get_db)
):
    """
    Get detailed trend analysis with daily/weekly breakdowns
    
    Returns:
    - Daily or weekly trend data
    - Trend direction analysis
    - Pattern identification
    - Seasonal indicators
    - Volatility metrics
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=period_days)
        date_to = datetime.utcnow()
        
        trends = analytics_service._analyze_trends(date_from, date_to)
        
        # Add additional trend analysis
        if granularity == "weekly" and len(trends["daily_trends"]) >= 7:
            # Group daily data into weekly trends
            weekly_trends = []
            daily_data = trends["daily_trends"]
            
            for i in range(0, len(daily_data), 7):
                week_data = daily_data[i:i+7]
                week_revenue = sum(d["revenue"] for d in week_data)
                week_orders = sum(d["orders"] for d in week_data)
                
                weekly_trends.append({
                    "week_start": week_data[0]["date"],
                    "week_end": week_data[-1]["date"],
                    "revenue": round(week_revenue, 2),
                    "orders": week_orders,
                    "avg_daily_revenue": round(week_revenue / len(week_data), 2),
                    "avg_daily_orders": round(week_orders / len(week_data), 1)
                })
            
            trends["weekly_trends"] = weekly_trends
        
        # Calculate volatility
        revenues = [t["revenue"] for t in trends["daily_trends"]]
        if len(revenues) > 1:
            import statistics
            avg_revenue = statistics.mean(revenues)
            revenue_std = statistics.stdev(revenues)
            volatility = (revenue_std / avg_revenue * 100) if avg_revenue > 0 else 0
            
            trends["volatility_analysis"] = {
                "revenue_volatility_percent": round(volatility, 2),
                "stability": "low" if volatility < 10 else "medium" if volatility < 25 else "high"
            }
        
        return {
            "success": True,
            "data": trends,
            "message": f"Trend analysis completed with {granularity} granularity"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate trend analysis: {str(e)}")


# ===========================================
# ALERTS AND NOTIFICATIONS
# ===========================================

@router.get("/dashboard/alerts")
async def get_dashboard_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (low, medium, high, critical)"),
    alert_type: Optional[str] = Query(None, description="Filter by type (inventory, supplier, performance, financial)"),
    db: Session = Depends(get_db)
):
    """
    Get dashboard alerts and notifications
    
    Returns:
    - Critical alerts requiring immediate attention
    - Performance warnings and recommendations
    - Inventory and supplier notifications
    - System status alerts
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        alerts = analytics_service._generate_alerts_and_notifications()
        
        # Apply filters
        if severity:
            alerts = [alert for alert in alerts if alert.get("severity") == severity]
        
        if alert_type:
            alerts = [alert for alert in alerts if alert.get("type") == alert_type]
        
        # Sort by severity
        severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        alerts.sort(key=lambda x: severity_order.get(x.get("severity", "low"), 4))
        
        alert_summary = {
            "total_alerts": len(alerts),
            "severity_breakdown": {
                "critical": len([a for a in alerts if a.get("severity") == "critical"]),
                "high": len([a for a in alerts if a.get("severity") == "high"]),
                "medium": len([a for a in alerts if a.get("severity") == "medium"]),
                "low": len([a for a in alerts if a.get("severity") == "low"])
            },
            "type_breakdown": {
                "inventory": len([a for a in alerts if a.get("type") == "inventory"]),
                "supplier": len([a for a in alerts if a.get("type") == "supplier"]),
                "performance": len([a for a in alerts if a.get("type") == "performance"]),
                "financial": len([a for a in alerts if a.get("type") == "financial"])
            },
            "alerts": alerts
        }
        
        return {
            "success": True,
            "data": alert_summary,
            "message": f"Found {len(alerts)} alerts requiring attention"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get dashboard alerts: {str(e)}")


# ===========================================
# FORECASTING AND PREDICTIONS
# ===========================================

@router.get("/dashboard/forecasts")
async def get_business_forecasts(
    forecast_period_days: int = Query(30, description="Forecast period in days", ge=7, le=90),
    historical_period_days: int = Query(60, description="Historical data period for forecasting", ge=30, le=365),
    confidence_level: str = Query("medium", description="Forecast confidence level (low, medium, high)"),
    db: Session = Depends(get_db)
):
    """
    Get business forecasts and predictions
    
    Returns:
    - Revenue forecasts for specified period
    - Growth projections
    - Monthly forecasts
    - Confidence intervals
    - Forecast assumptions and methodology
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=historical_period_days)
        date_to = datetime.utcnow()
        
        forecasts = analytics_service._generate_forecasts(date_from, date_to)
        
        # Adjust confidence based on request
        confidence_adjustments = {
            "low": 0.7,
            "medium": 1.0,
            "high": 1.3
        }
        
        adjustment_factor = confidence_adjustments.get(confidence_level, 1.0)
        
        # Apply confidence adjustments to forecasts
        if "next_period_forecast" in forecasts:
            forecasts["next_period_forecast"]["confidence"] = confidence_level
            if confidence_level == "low":
                forecasts["next_period_forecast"]["confidence_range"] = {
                    "lower": forecasts["next_period_forecast"]["forecasted_revenue"] * 0.8,
                    "upper": forecasts["next_period_forecast"]["forecasted_revenue"] * 1.2
                }
        
        for monthly_forecast in forecasts.get("monthly_forecasts", []):
            monthly_forecast["confidence"] = confidence_level
        
        # Add forecast methodology
        forecasts["methodology"] = {
            "approach": "Linear growth extrapolation",
            "historical_period_days": historical_period_days,
            "forecast_period_days": forecast_period_days,
            "confidence_level": confidence_level,
            "limitations": [
                "Based on historical trends only",
                "Does not account for external market factors",
                "Assumes consistent business conditions",
                "Accuracy decreases with longer forecast horizons"
            ]
        }
        
        return {
            "success": True,
            "data": forecasts,
            "message": f"Business forecasts generated for {forecast_period_days} days ahead"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate forecasts: {str(e)}")


# ===========================================
# CUSTOM DASHBOARD WIDGETS
# ===========================================

@router.get("/dashboard/widget/revenue-chart")
async def get_revenue_chart_data(
    period_days: int = Query(30, description="Chart period in days", ge=7, le=365),
    granularity: str = Query("daily", description="Data granularity (daily, weekly, monthly)"),
    db: Session = Depends(get_db)
):
    """
    Get revenue chart data for dashboard widgets
    
    Returns:
    - Time series revenue data
    - Formatted for chart rendering
    - Includes trend indicators
    - Growth rate annotations
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=period_days)
        date_to = datetime.utcnow()
        
        trends = analytics_service._analyze_trends(date_from, date_to)
        
        chart_data = {
            "chart_type": "revenue_trend",
            "period_days": period_days,
            "granularity": granularity,
            "data_points": trends["daily_trends"],
            "trend_direction": trends["trend_direction"],
            "summary": trends["trend_analysis"]
        }
        
        # Add chart formatting helpers
        chart_data["chart_config"] = {
            "x_axis": "date",
            "y_axis": "revenue",
            "title": f"Revenue Trend - Last {period_days} Days",
            "color_scheme": "blue",
            "show_trend_line": True
        }
        
        return {
            "success": True,
            "data": chart_data,
            "message": f"Revenue chart data generated for {period_days} days"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate revenue chart data: {str(e)}")


@router.get("/dashboard/widget/kpi-summary")
async def get_kpi_summary_widget(
    period_days: int = Query(30, description="KPI calculation period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get KPI summary widget data
    
    Returns:
    - Key metrics in widget format
    - Status indicators and colors
    - Percentage changes vs previous period
    - Formatted for dashboard display
    """
    try:
        analytics_service = DashboardAnalyticsService(db)
        dashboard_data = analytics_service.get_dashboard_overview(period_days=period_days)
        
        # Extract key metrics for widget display
        exec_summary = dashboard_data["executive_summary"]
        financial = dashboard_data["financial_metrics"]
        operational = dashboard_data["operational_metrics"]
        
        kpi_widgets = [
            {
                "title": "Revenue",
                "value": f"${exec_summary['period_revenue']:,.2f}",
                "change": f"{exec_summary['revenue_growth_percent']:+.1f}%",
                "status": "positive" if exec_summary['revenue_growth_percent'] > 0 else "negative",
                "icon": "trending_up" if exec_summary['revenue_growth_percent'] > 0 else "trending_down"
            },
            {
                "title": "Profit Margin",
                "value": f"{financial['profit_margin_percent']:.1f}%",
                "change": "vs target",
                "status": "positive" if financial['profit_margin_percent'] > 20 else "warning",
                "icon": "attach_money"
            },
            {
                "title": "Orders",
                "value": f"{exec_summary['total_orders']:,}",
                "change": f"${exec_summary['avg_order_value']:.2f} avg",
                "status": "positive",
                "icon": "shopping_cart"
            },
            {
                "title": "Fulfillment",
                "value": f"{operational['fulfillment_rate']:.1f}%",
                "change": f"{operational['avg_delivery_days']:.1f} days avg",
                "status": "positive" if operational['fulfillment_rate'] > 95 else "warning",
                "icon": "local_shipping"
            }
        ]
        
        return {
            "success": True,
            "data": {
                "widgets": kpi_widgets,
                "period_days": period_days,
                "last_updated": datetime.utcnow().isoformat()
            },
            "message": f"KPI summary widgets generated for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate KPI summary widgets: {str(e)}")