"""
Dashboard API Endpoints - Comprehensive dashboard data với SQLite aggregations
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.schemas.schemas import DashboardStats, APIResponse
from app.repositories import listing_repo, order_repo, source_repo, account_repo
from app.db.database import get_db
from app.core.deps import get_current_user
from app.models.database_models import User

router = APIRouter()


@router.get("", response_model=APIResponse)
async def get_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete dashboard data (alias for /summary)
    """
    return await get_dashboard_summary(db, current_user)


@router.get("/stats", response_model=APIResponse)
async def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive dashboard statistics
    """
    try:
        # Get stats from all repositories
        listing_stats = listing_repo.get_statistics(db, user_id=current_user.id)
        order_stats = order_repo.get_statistics(db, user_id=current_user.id)
        source_stats = source_repo.get_statistics(db, user_id=current_user.id)
        account_stats = account_repo.get_statistics(db, user_id=current_user.id)
        
        # Combine into dashboard stats
        dashboard_stats = {
            # Listings
            "total_listings": listing_stats.get("total_listings", 0),
            "active_listings": listing_stats.get("active_count", 0),
            "draft_listings": listing_stats.get("draft_count", 0),
            "optimized_listings": listing_stats.get("optimized_count", 0),
            "avg_performance_score": listing_stats.get("avg_performance_score", 0.0),
            
            # Orders
            "total_orders": order_stats.get("total_orders", 0),
            "pending_orders": order_stats.get("pending_count", 0),
            "processing_orders": order_stats.get("processing_count", 0),
            "shipped_orders": order_stats.get("shipped_count", 0),
            "total_revenue": order_stats.get("total_revenue", 0.0),
            "monthly_revenue": order_stats.get("monthly_revenue", 0.0),
            "avg_order_value": order_stats.get("avg_order_value", 0.0),
            "orders_with_tracking": order_stats.get("orders_with_tracking", 0),
            
            # Sources
            "total_sources": source_stats.get("total_sources", 0),
            "connected_sources": source_stats.get("connected_count", 0),
            "total_products": source_stats.get("total_products", 0),
            "avg_roi": source_stats.get("avg_roi", 0.0),
            
            # Accounts
            "total_accounts": account_stats.get("total_accounts", 0),
            "active_accounts": account_stats.get("active_count", 0),
            "avg_health_score": account_stats.get("avg_health_score", 0.0),
            "listing_usage_percentage": account_stats.get("listing_usage_percentage", 0.0),
            "revenue_usage_percentage": account_stats.get("revenue_usage_percentage", 0.0),
            
            # Calculate profit margin
            "profit_margin": (order_stats.get("total_profit", 0.0) / order_stats.get("total_revenue", 1.0)) * 100 if order_stats.get("total_revenue", 0.0) > 0 else 0.0
        }
        
        return APIResponse(
            success=True,
            message="Dashboard statistics retrieved successfully",
            data=dashboard_stats
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard stats: {str(e)}")


@router.get("/recent-orders", response_model=APIResponse)
async def get_recent_orders(
    limit: int = Query(10, ge=1, le=50, description="Number of recent orders"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get recent orders for dashboard
    """
    try:
        orders = order_repo.get_recent_orders(
            db,
            user_id=current_user.id,
            days=7,
            limit=limit
        )
        
        # Format for dashboard display - properly serialize SQLAlchemy objects
        formatted_orders = []
        for order in orders:
            formatted_orders.append({
                "id": order.id,
                "order_number": order.order_number or f"ORD-{order.id}",
                "customer_name": order.customer_name or "Unknown Customer",
                "product_name": order.product_name or "Unknown Product",
                "price_ebay": float(order.price_ebay) if order.price_ebay else 0.0,
                "status": order.status.value if hasattr(order.status, 'value') else str(order.status),
                "order_date": order.order_date.isoformat() if order.order_date else None,
                "tracking_number": order.tracking_number,
                "alerts": list(order.alerts) if order.alerts else []
            })
        
        return APIResponse(
            success=True,
            message="Recent orders retrieved successfully",
            data=formatted_orders
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recent orders: {str(e)}")


@router.get("/top-products", response_model=APIResponse)
async def get_top_products(
    limit: int = Query(5, ge=1, le=20, description="Number of top products"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get top performing products/listings
    """
    try:
        listings = listing_repo.get_top_performing_listings(
            db,
            user_id=current_user.id,
            limit=limit
        )
        
        # Format for dashboard display - properly serialize SQLAlchemy objects
        formatted_products = []
        for listing in listings:
            formatted_products.append({
                "id": listing.id,
                "title": listing.title or "Unknown Product",
                "category": listing.category or "Uncategorized",
                "price": float(listing.price) if listing.price else 0.0,
                "sold": int(listing.sold) if listing.sold else 0,
                "views": int(listing.views) if listing.views else 0,
                "watchers": int(listing.watchers) if listing.watchers else 0,
                "performance_score": float(listing.performance_score) if listing.performance_score else 0.0,
                "revenue": float((listing.price or 0) * (listing.sold or 0))
            })
        
        return APIResponse(
            success=True,
            message="Top products retrieved successfully",
            data=formatted_products
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting top products: {str(e)}")


@router.get("/revenue-chart", response_model=APIResponse)
async def get_revenue_chart(
    period_days: int = Query(30, ge=7, le=365, description="Period in days"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get revenue chart data for specified period
    """
    try:
        revenue_data = order_repo.get_revenue_by_period(
            db,
            user_id=current_user.id,
            period_days=period_days
        )
        
        return APIResponse(
            success=True,
            message="Revenue chart data retrieved successfully",
            data=revenue_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting revenue chart: {str(e)}")


@router.get("/category-chart", response_model=APIResponse)
async def get_category_chart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get category distribution chart data
    """
    try:
        # Get listing statistics which includes categories
        listing_stats = listing_repo.get_statistics(db, user_id=current_user.id)
        categories = listing_stats.get("categories", {})
        
        # Format for chart
        chart_data = []
        colors = [
            "#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", 
            "#9966FF", "#FF9F40", "#FF6384", "#C9CBCF"
        ]
        
        for i, (category, count) in enumerate(categories.items()):
            chart_data.append({
                "label": category or "Uncategorized",
                "value": count,
                "color": colors[i % len(colors)]
            })
        
        return APIResponse(
            success=True,
            message="Category chart data retrieved successfully",
            data=chart_data
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting category chart: {str(e)}")


@router.get("/activity-timeline", response_model=APIResponse)
async def get_activity_timeline(
    limit: int = Query(10, ge=1, le=50, description="Number of activities"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get activity timeline for dashboard
    """
    try:
        try:
            from app.models.database_models import ActivityLog
            from sqlalchemy import desc
            
            # Get recent activities
            activities = db.query(ActivityLog).filter(
                ActivityLog.user_id == current_user.id
            ).order_by(desc(ActivityLog.created_at)).limit(limit).all()
        except Exception as db_error:
            # If ActivityLog table doesn't exist or has issues, use mock data
            print(f"ActivityLog table issue: {db_error}")
            activities = []
        
        # Format activities
        formatted_activities = []
        for activity in activities:
            # Determine icon and color based on action
            if activity.action == "create":
                icon = "+"
                color = "success"
            elif activity.action == "update":
                icon = "✏️"
                color = "info"
            elif activity.action == "delete":
                icon = "🗑️"
                color = "error"
            elif activity.action == "sync":
                icon = "🔄"
                color = "warning"
            else:
                icon = "📝"
                color = "primary"
            
            # Handle entity_id conversion safely
            try:
                entity_id = int(activity.entity_id) if activity.entity_id and str(activity.entity_id).isdigit() else 0
            except (ValueError, TypeError):
                entity_id = 0
            
            formatted_activities.append({
                "id": int(activity.id),
                "action": str(activity.action),
                "entity_type": str(activity.entity_type) if activity.entity_type else "unknown",
                "entity_id": entity_id,
                "description": str(activity.description) if activity.description else f"{activity.action} operation",
                "icon": str(icon),
                "color": str(color),
                "timestamp": activity.created_at.isoformat() if activity.created_at else datetime.now().isoformat(),
                "success": bool(activity.success) if hasattr(activity, 'success') else True
            })
        
        # Return empty list if no activities found - no mock data
        
        return APIResponse(
            success=True,
            message="Activity timeline retrieved successfully",
            data=formatted_activities
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting activity timeline: {str(e)}")


@router.get("/alerts", response_model=APIResponse)
async def get_dashboard_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get dashboard alerts and warnings
    """
    try:
        alerts = []
        
        # Check for overdue orders
        overdue_orders = order_repo.get_overdue_orders(
            db,
            user_id=current_user.id,
            limit=5
        )
        
        if overdue_orders:
            alerts.append({
                "type": "warning",
                "title": "Overdue Orders",
                "message": f"You have {len(overdue_orders)} orders past expected ship date",
                "count": len(overdue_orders),
                "action": "View Orders",
                "link": "/orders?status=pending"
            })
        
        # Check accounts near limits
        accounts_near_limits = account_repo.get_accounts_near_limits(
            db,
            user_id=current_user.id,
            threshold_percentage=80.0
        )
        
        if accounts_near_limits:
            alerts.append({
                "type": "error",
                "title": "Account Limits Warning",
                "message": f"{len(accounts_near_limits)} accounts are near their limits",
                "count": len(accounts_near_limits),
                "action": "View Accounts",
                "link": "/accounts"
            })
        
        # Check sources needing sync
        sources_need_sync = source_repo.get_sources_need_sync(
            db,
            user_id=current_user.id,
            hours_threshold=24
        )
        
        if sources_need_sync:
            alerts.append({
                "type": "info",
                "title": "Sources Need Sync",
                "message": f"{len(sources_need_sync)} sources haven't been synced recently",
                "count": len(sources_need_sync),
                "action": "Sync Sources",
                "link": "/sources"
            })
        
        # Check low performance listings
        low_performance = listing_repo.get_low_performance_listings(
            db,
            user_id=current_user.id,
            threshold=50.0,
            limit=5
        )
        
        if low_performance:
            alerts.append({
                "type": "warning",
                "title": "Low Performance Listings",
                "message": f"{len(low_performance)} listings have low performance scores",
                "count": len(low_performance),
                "action": "Optimize Listings",
                "link": "/listings?sort_by=performance_score&sort_order=asc"
            })
        
        return APIResponse(
            success=True,
            message="Dashboard alerts retrieved successfully",
            data=alerts
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard alerts: {str(e)}")


@router.get("/summary", response_model=APIResponse)
async def get_dashboard_summary(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get complete dashboard summary with all data
    """
    try:
        # Get all dashboard data in parallel-style calls
        stats_response = await get_dashboard_stats(db, current_user)
        recent_orders_response = await get_recent_orders(10, db, current_user)
        top_products_response = await get_top_products(5, db, current_user)
        revenue_chart_response = await get_revenue_chart(30, db, current_user)
        category_chart_response = await get_category_chart(db, current_user)
        activity_response = await get_activity_timeline(10, db, current_user)
        alerts_response = await get_dashboard_alerts(db, current_user)
        
        # Combine all data
        summary = {
            "stats": stats_response.data,
            "recent_orders": recent_orders_response.data,
            "top_products": top_products_response.data,
            "revenue_chart": revenue_chart_response.data,
            "category_chart": category_chart_response.data,
            "activity_timeline": activity_response.data,
            "alerts": alerts_response.data
        }
        
        return APIResponse(
            success=True,
            message="Dashboard summary retrieved successfully",
            data=summary
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting dashboard summary: {str(e)}")