"""
Export Service - Generate reports và export to various formats
Specialized functions cho business reporting và analytics
"""

import json
import csv
import io
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, desc

from app.repositories import listing_repo, order_repo, source_repo, account_repo
from app.models.database_models import Listing, Order, Source, Account


class ExportService:
    """
    Service để generate reports và export data
    """
    
    def __init__(self):
        self.export_formats = ["csv", "json", "excel", "google_sheets"]
    
    def generate_listings_report(
        self, 
        db: Session, 
        user_id: int,
        format: str = "csv",
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate comprehensive listings report
        """
        try:
            # Get listings với filters
            result = listing_repo.get_multi(
                db,
                skip=0,
                limit=10000,  # Large limit for reports
                filters=filters or {},
                user_id=user_id,
                sort_by="created_at",
                sort_order="desc"
            )
            
            listings = result["items"]
            
            # Prepare report data
            report_data = []
            for listing in listings:
                row = {
                    "ID": listing.id,
                    "Title": listing.title,
                    "Category": listing.category or "",
                    "Price": listing.price or 0,
                    "Quantity": listing.quantity or 0,
                    "Status": listing.status.value,
                    "Views": listing.views or 0,
                    "Watchers": listing.watchers or 0,
                    "Sold": listing.sold or 0,
                    "Performance Score": listing.performance_score or 0,
                    "SEO Score": listing.seo_score or 0,
                    "Item ID": listing.item_id or "",
                    "SKU": listing.sku or "",
                    "Condition": listing.condition or "",
                    "Keywords": ",".join(listing.keywords) if listing.keywords else "",
                    "Created Date": listing.created_at.strftime("%Y-%m-%d %H:%M:%S") if listing.created_at else "",
                    "Updated Date": listing.updated_at.strftime("%Y-%m-%d %H:%M:%S") if listing.updated_at else "",
                    "Last Synced": listing.last_synced.strftime("%Y-%m-%d %H:%M:%S") if listing.last_synced else ""
                }
                report_data.append(row)
            
            # Generate export
            if format == "csv":
                return self._export_to_csv(report_data, "listings_report")
            elif format == "json":
                return self._export_to_json(report_data, "listings_report")
            else:
                return {"success": False, "message": f"Format {format} not supported yet"}
            
        except Exception as e:
            return {"success": False, "message": f"Error generating listings report: {str(e)}"}
    
    def generate_orders_report(
        self, 
        db: Session, 
        user_id: int,
        format: str = "csv",
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate orders report for specified period
        """
        try:
            # Default to last 30 days if no dates provided
            if not date_from:
                date_from = datetime.now() - timedelta(days=30)
            if not date_to:
                date_to = datetime.now()
            
            # Get orders in date range
            orders = db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.order_date >= date_from,
                    Order.order_date <= date_to
                )
            ).order_by(desc(Order.order_date)).all()
            
            # Prepare report data
            report_data = []
            for order in orders:
                row = {
                    "Order ID": order.id,
                    "Order Number": order.order_number,
                    "Item ID": order.item_id or "",
                    "Customer Name": order.customer_name or "",
                    "Customer Email": order.customer_email or "",
                    "Customer Phone": order.customer_phone or "",
                    "Customer Type": order.customer_type or "",
                    "eBay Username": order.username_ebay or "",
                    "Product Name": order.product_name,
                    "Product Option": order.product_option or "",
                    "Price (eBay)": order.price_ebay or 0,
                    "Cost Price": order.price_cost or 0,
                    "Net Profit": order.net_profit or 0,
                    "Fees": order.fees or 0,
                    "Status": order.status.value,
                    "Order Date": order.order_date.strftime("%Y-%m-%d %H:%M:%S") if order.order_date else "",
                    "Expected Ship": order.expected_ship_date.strftime("%Y-%m-%d") if order.expected_ship_date else "",
                    "Actual Ship": order.actual_ship_date.strftime("%Y-%m-%d") if order.actual_ship_date else "",
                    "Delivery Date": order.delivery_date.strftime("%Y-%m-%d") if order.delivery_date else "",
                    "Tracking Number": order.tracking_number or "",
                    "Carrier": order.carrier or "",
                    "Shipping Address": order.shipping_address or "",
                    "City": order.city or "",
                    "State": order.state or "",
                    "Postal Code": order.postal_code or "",
                    "Country": order.country or "",
                    "Alerts": ",".join(order.alerts) if order.alerts else "",
                    "Notes": order.notes or "",
                    "Machine": order.machine or "",
                    "Created": order.created_at.strftime("%Y-%m-%d %H:%M:%S") if order.created_at else ""
                }
                report_data.append(row)
            
            # Generate export
            if format == "csv":
                return self._export_to_csv(report_data, f"orders_report_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}")
            elif format == "json":
                return self._export_to_json(report_data, f"orders_report_{date_from.strftime('%Y%m%d')}_{date_to.strftime('%Y%m%d')}")
            else:
                return {"success": False, "message": f"Format {format} not supported yet"}
                
        except Exception as e:
            return {"success": False, "message": f"Error generating orders report: {str(e)}"}
    
    def generate_financial_report(
        self, 
        db: Session, 
        user_id: int,
        format: str = "csv",
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate financial performance report
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period_days)
            
            # Get orders for financial calculation
            orders = db.query(Order).filter(
                and_(
                    Order.user_id == user_id,
                    Order.order_date >= start_date,
                    Order.order_date <= end_date
                )
            ).all()
            
            # Calculate daily financial metrics
            daily_metrics = {}
            for order in orders:
                if not order.order_date:
                    continue
                    
                date_key = order.order_date.strftime("%Y-%m-%d")
                
                if date_key not in daily_metrics:
                    daily_metrics[date_key] = {
                        "date": date_key,
                        "orders_count": 0,
                        "total_revenue": 0.0,
                        "total_cost": 0.0,
                        "total_profit": 0.0,
                        "total_fees": 0.0,
                        "avg_order_value": 0.0
                    }
                
                daily_metrics[date_key]["orders_count"] += 1
                daily_metrics[date_key]["total_revenue"] += order.price_ebay or 0
                daily_metrics[date_key]["total_cost"] += order.price_cost or 0
                daily_metrics[date_key]["total_profit"] += order.net_profit or 0
                daily_metrics[date_key]["total_fees"] += order.fees or 0
            
            # Calculate averages
            for date_key in daily_metrics:
                metrics = daily_metrics[date_key]
                if metrics["orders_count"] > 0:
                    metrics["avg_order_value"] = metrics["total_revenue"] / metrics["orders_count"]
                    metrics["profit_margin"] = (metrics["total_profit"] / metrics["total_revenue"]) * 100 if metrics["total_revenue"] > 0 else 0
                    metrics["fee_percentage"] = (metrics["total_fees"] / metrics["total_revenue"]) * 100 if metrics["total_revenue"] > 0 else 0
            
            # Convert to report format
            report_data = list(daily_metrics.values())
            report_data.sort(key=lambda x: x["date"])
            
            # Add summary row
            if report_data:
                summary = {
                    "date": "TOTAL",
                    "orders_count": sum(row["orders_count"] for row in report_data),
                    "total_revenue": sum(row["total_revenue"] for row in report_data),
                    "total_cost": sum(row["total_cost"] for row in report_data),
                    "total_profit": sum(row["total_profit"] for row in report_data),
                    "total_fees": sum(row["total_fees"] for row in report_data),
                    "avg_order_value": sum(row["total_revenue"] for row in report_data) / sum(row["orders_count"] for row in report_data) if sum(row["orders_count"] for row in report_data) > 0 else 0,
                    "profit_margin": (sum(row["total_profit"] for row in report_data) / sum(row["total_revenue"] for row in report_data)) * 100 if sum(row["total_revenue"] for row in report_data) > 0 else 0,
                    "fee_percentage": (sum(row["total_fees"] for row in report_data) / sum(row["total_revenue"] for row in report_data)) * 100 if sum(row["total_revenue"] for row in report_data) > 0 else 0
                }
                report_data.append(summary)
            
            # Generate export
            if format == "csv":
                return self._export_to_csv(report_data, f"financial_report_{period_days}days")
            elif format == "json":
                return self._export_to_json(report_data, f"financial_report_{period_days}days")
            else:
                return {"success": False, "message": f"Format {format} not supported yet"}
                
        except Exception as e:
            return {"success": False, "message": f"Error generating financial report: {str(e)}"}
    
    def generate_performance_report(
        self, 
        db: Session, 
        user_id: int,
        format: str = "csv"
    ) -> Dict[str, Any]:
        """
        Generate performance analysis report
        """
        try:
            # Get performance statistics
            listing_stats = listing_repo.get_statistics(db, user_id=user_id)
            order_stats = order_repo.get_statistics(db, user_id=user_id)
            source_stats = source_repo.get_statistics(db, user_id=user_id)
            account_stats = account_repo.get_statistics(db, user_id=user_id)
            
            # Get top performers
            top_listings = listing_repo.get_top_performing_listings(db, user_id=user_id, limit=10)
            low_listings = listing_repo.get_low_performance_listings(db, user_id=user_id, threshold=50.0, limit=10)
            
            # Compile performance data
            report_data = [
                {"Metric": "Total Listings", "Value": listing_stats.get("total_listings", 0)},
                {"Metric": "Active Listings", "Value": listing_stats.get("active_count", 0)},
                {"Metric": "Average Performance Score", "Value": round(listing_stats.get("avg_performance_score", 0), 2)},
                {"Metric": "Total Views", "Value": listing_stats.get("total_views", 0)},
                {"Metric": "Total Watchers", "Value": listing_stats.get("total_watchers", 0)},
                {"Metric": "Total Sold", "Value": listing_stats.get("total_sold", 0)},
                {"Metric": "", "Value": ""},  # Separator
                {"Metric": "Total Orders", "Value": order_stats.get("total_orders", 0)},
                {"Metric": "Total Revenue", "Value": f"${order_stats.get('total_revenue', 0):,.2f}"},
                {"Metric": "Average Order Value", "Value": f"${order_stats.get('avg_order_value', 0):,.2f}"},
                {"Metric": "Orders with Tracking", "Value": order_stats.get("orders_with_tracking", 0)},
                {"Metric": "", "Value": ""},  # Separator
                {"Metric": "Total Sources", "Value": source_stats.get("total_sources", 0)},
                {"Metric": "Connected Sources", "Value": source_stats.get("connected_count", 0)},
                {"Metric": "Average ROI", "Value": f"{source_stats.get('avg_roi', 0):.1f}%"},
                {"Metric": "", "Value": ""},  # Separator
                {"Metric": "Total Accounts", "Value": account_stats.get("total_accounts", 0)},
                {"Metric": "Average Health Score", "Value": f"{account_stats.get('avg_health_score', 0):.1f}"},
                {"Metric": "Listing Usage", "Value": f"{account_stats.get('listing_usage_percentage', 0):.1f}%"},
                {"Metric": "Revenue Usage", "Value": f"{account_stats.get('revenue_usage_percentage', 0):.1f}%"},
            ]
            
            # Add top performers
            report_data.append({"Metric": "", "Value": ""})
            report_data.append({"Metric": "TOP PERFORMING LISTINGS", "Value": ""})
            for i, listing in enumerate(top_listings, 1):
                report_data.append({
                    "Metric": f"#{i} {listing.title[:50]}...",
                    "Value": f"Score: {listing.performance_score}, Sold: {listing.sold}"
                })
            
            # Add low performers
            if low_listings:
                report_data.append({"Metric": "", "Value": ""})
                report_data.append({"Metric": "LOW PERFORMING LISTINGS", "Value": ""})
                for i, listing in enumerate(low_listings, 1):
                    report_data.append({
                        "Metric": f"#{i} {listing.title[:50]}...",
                        "Value": f"Score: {listing.performance_score}, Views: {listing.views}"
                    })
            
            # Generate export
            if format == "csv":
                return self._export_to_csv(report_data, "performance_report")
            elif format == "json":
                return self._export_to_json(report_data, "performance_report")
            else:
                return {"success": False, "message": f"Format {format} not supported yet"}
                
        except Exception as e:
            return {"success": False, "message": f"Error generating performance report: {str(e)}"}
    
    def _export_to_csv(self, data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Export data to CSV format
        """
        try:
            if not data:
                return {"success": False, "message": "No data to export"}
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
            
            csv_content = output.getvalue()
            output.close()
            
            return {
                "success": True,
                "message": f"CSV export generated successfully",
                "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "content": csv_content,
                "content_type": "text/csv",
                "size": len(csv_content),
                "records": len(data)
            }
            
        except Exception as e:
            return {"success": False, "message": f"CSV export failed: {str(e)}"}
    
    def _export_to_json(self, data: List[Dict[str, Any]], filename: str) -> Dict[str, Any]:
        """
        Export data to JSON format
        """
        try:
            if not data:
                return {"success": False, "message": "No data to export"}
            
            # Create JSON content
            json_content = json.dumps(data, indent=2, default=str)
            
            return {
                "success": True,
                "message": f"JSON export generated successfully",
                "filename": f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                "content": json_content,
                "content_type": "application/json",
                "size": len(json_content),
                "records": len(data)
            }
            
        except Exception as e:
            return {"success": False, "message": f"JSON export failed: {str(e)}"}
    
    def get_available_reports(self) -> List[Dict[str, Any]]:
        """
        Get list of available report types
        """
        return [
            {
                "id": "listings",
                "name": "Listings Report",
                "description": "Comprehensive listing data with performance metrics",
                "formats": ["csv", "json"],
                "filters": ["status", "category", "performance_threshold"]
            },
            {
                "id": "orders",
                "name": "Orders Report",
                "description": "Order data with customer and financial information",
                "formats": ["csv", "json"],
                "filters": ["date_range", "status", "customer_type"]
            },
            {
                "id": "financial",
                "name": "Financial Report",
                "description": "Daily financial metrics and profitability analysis",
                "formats": ["csv", "json"],
                "filters": ["period_days"]
            },
            {
                "id": "performance",
                "name": "Performance Report",
                "description": "Overall performance metrics and top/low performers",
                "formats": ["csv", "json"],
                "filters": []
            }
        ]


# Create service instance
export_service = ExportService()