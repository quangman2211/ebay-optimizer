"""
Inventory Management Service - SOLID Architecture Implementation
Handles automated reorder point calculations, inventory optimization, and stock forecasting
Single Responsibility: Manages all inventory-related calculations and automation
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
import statistics
import math

from app.models.database_models import (
    Product, Supplier, SupplierProduct, OrderItem, Order, PriceHistory
)
from app.schemas.schemas import (
    ProductPerformanceStats
)


class InventoryManagementService:
    """
    SOLID Principle: Single Responsibility
    Manages inventory optimization, reorder point calculations, and stock forecasting
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.safety_stock_multiplier = 1.5  # 50% safety buffer
        self.lead_time_buffer_days = 3  # Additional buffer for lead time variation
        self.demand_analysis_period = 90  # Days for demand analysis
        self.seasonal_adjustment_factor = 1.2  # 20% seasonal adjustment
        
        # Service level targets (99% = 2.33, 95% = 1.65, 90% = 1.28)
        self.service_level_z_scores = {
            99: 2.33,
            95: 1.65,
            90: 1.28,
            85: 1.04
        }
    
    # ===========================================
    # AUTOMATED REORDER POINT CALCULATIONS
    # ===========================================
    
    def calculate_reorder_points(
        self,
        product_ids: Optional[List[int]] = None,
        service_level: int = 95,
        include_seasonality: bool = True
    ) -> Dict[str, Any]:
        """Calculate reorder points for products using advanced algorithms"""
        
        if product_ids:
            products = self.db.query(Product).filter(Product.id.in_(product_ids)).all()
        else:
            products = self.db.query(Product).filter(Product.status == "active").all()
        
        calculation_results = {
            "calculation_date": datetime.utcnow().isoformat(),
            "service_level": service_level,
            "products_analyzed": len(products),
            "include_seasonality": include_seasonality,
            "reorder_points": [],
            "summary": {
                "total_products": len(products),
                "calculated": 0,
                "failed": 0,
                "avg_reorder_point": 0.0,
                "total_safety_stock": 0.0
            },
            "recommendations": []
        }
        
        z_score = self.service_level_z_scores.get(service_level, 1.65)
        total_reorder_points = 0
        total_safety_stock = 0
        
        for product in products:
            try:
                reorder_data = self._calculate_product_reorder_point(
                    product, z_score, include_seasonality
                )
                
                if reorder_data:
                    calculation_results["reorder_points"].append(reorder_data)
                    calculation_results["summary"]["calculated"] += 1
                    total_reorder_points += reorder_data["reorder_point"]
                    total_safety_stock += reorder_data["safety_stock"]
                else:
                    calculation_results["summary"]["failed"] += 1
                    
            except Exception:
                calculation_results["summary"]["failed"] += 1
                continue
        
        # Calculate summary statistics
        if calculation_results["summary"]["calculated"] > 0:
            calculation_results["summary"]["avg_reorder_point"] = round(
                total_reorder_points / calculation_results["summary"]["calculated"], 2
            )
            calculation_results["summary"]["total_safety_stock"] = round(total_safety_stock, 2)
        
        # Generate recommendations
        calculation_results["recommendations"] = self._generate_reorder_recommendations(
            calculation_results["reorder_points"]
        )
        
        return calculation_results
    
    def _calculate_product_reorder_point(
        self, 
        product: Product, 
        z_score: float, 
        include_seasonality: bool
    ) -> Optional[Dict[str, Any]]:
        """Calculate reorder point for individual product"""
        
        # Get demand history
        demand_data = self._analyze_product_demand(product.id)
        if not demand_data or demand_data["avg_daily_demand"] == 0:
            return None
        
        # Get supplier information
        supplier_data = self._get_supplier_lead_times(product.id)
        if not supplier_data:
            return None
        
        avg_daily_demand = demand_data["avg_daily_demand"]
        demand_std_dev = demand_data["demand_std_dev"]
        avg_lead_time = supplier_data["avg_lead_time"]
        lead_time_std_dev = supplier_data["lead_time_std_dev"]
        
        # Apply seasonality adjustment if requested
        if include_seasonality:
            seasonality_factor = self._calculate_seasonality_factor(product.id)
            avg_daily_demand *= seasonality_factor
        
        # Calculate reorder point components
        # Reorder Point = (Average Daily Demand × Lead Time) + Safety Stock
        
        # Expected demand during lead time
        expected_demand_lead_time = avg_daily_demand * avg_lead_time
        
        # Safety stock calculation using statistical approach
        # SS = z × √(LT × σ²demand + μ²demand × σ²LT)
        demand_variance = demand_std_dev ** 2
        lead_time_variance = lead_time_std_dev ** 2
        
        safety_stock = z_score * math.sqrt(
            avg_lead_time * demand_variance + 
            (avg_daily_demand ** 2) * lead_time_variance
        )
        
        # Add buffer for uncertainty
        safety_stock *= self.safety_stock_multiplier
        
        reorder_point = expected_demand_lead_time + safety_stock
        
        # Calculate economic order quantity (EOQ) for comparison
        eoq = self._calculate_eoq(product, demand_data)
        
        # Calculate inventory turnover
        annual_demand = avg_daily_demand * 365
        avg_inventory = (reorder_point + eoq) / 2
        inventory_turnover = annual_demand / avg_inventory if avg_inventory > 0 else 0
        
        return {
            "product_id": product.id,
            "sku": product.sku,
            "product_name": product.name,
            "current_stock": product.stock_level or 0,
            "reorder_point": round(reorder_point, 0),
            "safety_stock": round(safety_stock, 0),
            "eoq": round(eoq, 0),
            "demand_analysis": {
                "avg_daily_demand": round(avg_daily_demand, 2),
                "demand_std_dev": round(demand_std_dev, 2),
                "seasonality_applied": include_seasonality
            },
            "supplier_analysis": supplier_data,
            "inventory_metrics": {
                "expected_demand_lead_time": round(expected_demand_lead_time, 0),
                "inventory_turnover": round(inventory_turnover, 2),
                "days_of_supply": round(reorder_point / avg_daily_demand, 1) if avg_daily_demand > 0 else 0
            },
            "reorder_needed": (product.stock_level or 0) <= reorder_point,
            "urgency_level": self._calculate_urgency_level(product.stock_level or 0, reorder_point, avg_daily_demand),
            "cost_impact": self._calculate_cost_impact(product, eoq, safety_stock)
        }
    
    def _analyze_product_demand(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Analyze historical demand patterns for a product"""
        
        date_from = datetime.utcnow() - timedelta(days=self.demand_analysis_period)
        
        # Get daily sales data
        daily_sales = self.db.query(
            func.date(OrderItem.created_at).label('sale_date'),
            func.sum(OrderItem.quantity).label('daily_quantity')
        ).filter(
            and_(
                OrderItem.product_id == product_id,
                OrderItem.created_at >= date_from,
                OrderItem.status.in_(['delivered', 'shipped'])
            )
        ).group_by(func.date(OrderItem.created_at)).all()
        
        if len(daily_sales) < 7:  # Need at least a week of data
            return None
        
        # Calculate demand statistics
        daily_quantities = [float(sale.daily_quantity) for sale in daily_sales]
        
        avg_daily_demand = statistics.mean(daily_quantities)
        demand_std_dev = statistics.stdev(daily_quantities) if len(daily_quantities) > 1 else 0
        
        # Fill in zero-demand days
        total_days = self.demand_analysis_period
        zero_demand_days = total_days - len(daily_sales)
        
        if zero_demand_days > 0:
            # Adjust for days with no sales
            adjusted_daily_quantities = daily_quantities + [0] * zero_demand_days
            avg_daily_demand = statistics.mean(adjusted_daily_quantities)
            demand_std_dev = statistics.stdev(adjusted_daily_quantities) if len(adjusted_daily_quantities) > 1 else 0
        
        return {
            "avg_daily_demand": avg_daily_demand,
            "demand_std_dev": demand_std_dev,
            "data_points": len(daily_sales),
            "analysis_period": self.demand_analysis_period,
            "demand_trend": self._calculate_demand_trend(daily_quantities)
        }
    
    def _get_supplier_lead_times(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get supplier lead time information for a product"""
        
        # Get supplier products with lead times
        supplier_products = self.db.query(
            SupplierProduct.supplier_id,
            SupplierProduct.lead_time_days,
            Supplier.company_name
        ).join(Supplier, SupplierProduct.supplier_id == Supplier.id) \
         .filter(SupplierProduct.product_id == product_id).all()
        
        if not supplier_products:
            return None
        
        # Calculate lead time statistics
        lead_times = [sp.lead_time_days for sp in supplier_products if sp.lead_time_days]
        
        if not lead_times:
            # Use default lead time
            return {
                "avg_lead_time": 14,  # Default 2 weeks
                "lead_time_std_dev": 3,  # Default variation
                "suppliers_count": len(supplier_products),
                "lead_time_range": {"min": 14, "max": 14}
            }
        
        avg_lead_time = statistics.mean(lead_times)
        lead_time_std_dev = statistics.stdev(lead_times) if len(lead_times) > 1 else 2
        
        # Add buffer for lead time uncertainty
        avg_lead_time += self.lead_time_buffer_days
        
        return {
            "avg_lead_time": avg_lead_time,
            "lead_time_std_dev": lead_time_std_dev,
            "suppliers_count": len(supplier_products),
            "lead_time_range": {"min": min(lead_times), "max": max(lead_times)},
            "suppliers": [
                {
                    "supplier_id": sp.supplier_id,
                    "company_name": sp.company_name,
                    "lead_time": sp.lead_time_days
                }
                for sp in supplier_products
            ]
        }
    
    def _calculate_seasonality_factor(self, product_id: int) -> float:
        """Calculate seasonality adjustment factor"""
        
        # Get sales data for the past year to identify seasonal patterns
        date_from = datetime.utcnow() - timedelta(days=365)
        current_month = datetime.utcnow().month
        
        monthly_sales = self.db.query(
            func.extract('month', OrderItem.created_at).label('month'),
            func.sum(OrderItem.quantity).label('monthly_quantity')
        ).filter(
            and_(
                OrderItem.product_id == product_id,
                OrderItem.created_at >= date_from,
                OrderItem.status.in_(['delivered', 'shipped'])
            )
        ).group_by(func.extract('month', OrderItem.created_at)).all()
        
        if len(monthly_sales) < 6:  # Need at least 6 months of data
            return 1.0  # No seasonality adjustment
        
        # Calculate seasonal index for current month
        monthly_quantities = [float(ms.monthly_quantity) for ms in monthly_sales]
        avg_monthly = statistics.mean(monthly_quantities)
        
        current_month_sales = next(
            (ms.monthly_quantity for ms in monthly_sales if ms.month == current_month),
            avg_monthly
        )
        
        seasonality_factor = float(current_month_sales) / avg_monthly if avg_monthly > 0 else 1.0
        
        # Cap seasonality adjustment
        seasonality_factor = max(0.5, min(2.0, seasonality_factor))
        
        return seasonality_factor
    
    def _calculate_eoq(self, product: Product, demand_data: Dict[str, Any]) -> float:
        """Calculate Economic Order Quantity"""
        
        annual_demand = demand_data["avg_daily_demand"] * 365
        
        # Estimate ordering cost (could be made configurable)
        ordering_cost = 50.0  # Default ordering cost per order
        
        # Calculate holding cost (percentage of product cost)
        holding_cost_rate = 0.25  # 25% annual holding cost
        unit_cost = float(product.cost_price) if product.cost_price else 10.0
        holding_cost = unit_cost * holding_cost_rate
        
        if annual_demand == 0 or holding_cost == 0:
            return 100  # Default EOQ
        
        # EOQ = √(2 × Annual Demand × Ordering Cost / Holding Cost)
        eoq = math.sqrt((2 * annual_demand * ordering_cost) / holding_cost)
        
        return max(1, eoq)  # Minimum EOQ of 1
    
    def _calculate_demand_trend(self, daily_quantities: List[float]) -> str:
        """Calculate demand trend (increasing, decreasing, stable)"""
        
        if len(daily_quantities) < 14:  # Need at least 2 weeks of data
            return "insufficient_data"
        
        # Split data into first and second half
        mid_point = len(daily_quantities) // 2
        first_half = daily_quantities[:mid_point]
        second_half = daily_quantities[mid_point:]
        
        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)
        
        change_percent = ((avg_second - avg_first) / avg_first * 100) if avg_first > 0 else 0
        
        if change_percent > 15:
            return "increasing"
        elif change_percent < -15:
            return "decreasing"
        else:
            return "stable"
    
    def _calculate_urgency_level(
        self, 
        current_stock: int, 
        reorder_point: float, 
        avg_daily_demand: float
    ) -> str:
        """Calculate urgency level for reordering"""
        
        if current_stock <= 0:
            return "critical"
        
        days_of_supply = current_stock / avg_daily_demand if avg_daily_demand > 0 else 999
        
        if current_stock <= reorder_point * 0.5:
            return "urgent"
        elif current_stock <= reorder_point:
            return "normal"
        else:
            return "low"
    
    def _calculate_cost_impact(
        self, 
        product: Product, 
        eoq: float, 
        safety_stock: float
    ) -> Dict[str, Any]:
        """Calculate cost impact of inventory decisions"""
        
        unit_cost = float(product.cost_price) if product.cost_price else 0
        
        # Inventory holding cost
        avg_inventory = (eoq / 2) + safety_stock
        annual_holding_cost = avg_inventory * unit_cost * 0.25  # 25% holding cost rate
        
        # Stockout cost (estimated)
        unit_price = float(product.selling_price) if product.selling_price else unit_cost * 1.5
        stockout_cost_per_unit = (unit_price - unit_cost) * 2  # Lost profit + customer cost
        
        return {
            "inventory_value": round(avg_inventory * unit_cost, 2),
            "annual_holding_cost": round(annual_holding_cost, 2),
            "safety_stock_value": round(safety_stock * unit_cost, 2),
            "stockout_cost_per_unit": round(stockout_cost_per_unit, 2)
        }
    
    def _generate_reorder_recommendations(
        self, 
        reorder_points: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on reorder point analysis"""
        
        recommendations = []
        
        # Find products needing immediate reorder
        urgent_reorders = [rp for rp in reorder_points if rp["urgency_level"] in ["critical", "urgent"]]
        if urgent_reorders:
            recommendations.append(f"{len(urgent_reorders)} products need immediate reordering")
        
        # Find products with high inventory turnover
        high_turnover = [rp for rp in reorder_points if rp["inventory_metrics"]["inventory_turnover"] > 12]
        if high_turnover:
            recommendations.append(f"{len(high_turnover)} products have excellent turnover (>12x annually)")
        
        # Find products with low turnover
        low_turnover = [rp for rp in reorder_points if rp["inventory_metrics"]["inventory_turnover"] < 4]
        if low_turnover:
            recommendations.append(f"{len(low_turnover)} products have slow turnover (<4x annually) - consider reducing safety stock")
        
        # Find high-cost inventory items
        high_cost_items = [rp for rp in reorder_points if rp["cost_impact"]["inventory_value"] > 5000]
        if high_cost_items:
            recommendations.append(f"{len(high_cost_items)} products have high inventory value (>$5,000) - optimize carefully")
        
        return recommendations
    
    # ===========================================
    # INVENTORY OPTIMIZATION
    # ===========================================
    
    def optimize_inventory_levels(
        self,
        target_service_level: int = 95,
        max_inventory_investment: Optional[float] = None
    ) -> Dict[str, Any]:
        """Optimize inventory levels across all products"""
        
        # Calculate reorder points for all products
        reorder_data = self.calculate_reorder_points(service_level=target_service_level)
        
        optimization_results = {
            "optimization_date": datetime.utcnow().isoformat(),
            "target_service_level": target_service_level,
            "max_investment": max_inventory_investment,
            "current_inventory_value": 0.0,
            "optimized_inventory_value": 0.0,
            "optimization_savings": 0.0,
            "products_optimized": [],
            "summary": {
                "total_products": len(reorder_data["reorder_points"]),
                "investment_reduced": 0,
                "investment_increased": 0,
                "no_change": 0
            },
            "recommendations": []
        }
        
        current_total_value = 0.0
        optimized_total_value = 0.0
        
        for product_data in reorder_data["reorder_points"]:
            # Get current product
            product = self.db.query(Product).filter(Product.id == product_data["product_id"]).first()
            if not product:
                continue
            
            unit_cost = float(product.cost_price) if product.cost_price else 0
            current_stock = product.stock_level or 0
            optimized_stock = product_data["reorder_point"] + product_data["eoq"]
            
            current_value = current_stock * unit_cost
            optimized_value = optimized_stock * unit_cost
            
            current_total_value += current_value
            optimized_total_value += optimized_value
            
            # Determine change type
            if optimized_value < current_value * 0.9:  # 10% reduction
                change_type = "reduce"
                optimization_results["summary"]["investment_reduced"] += 1
            elif optimized_value > current_value * 1.1:  # 10% increase
                change_type = "increase"
                optimization_results["summary"]["investment_increased"] += 1
            else:
                change_type = "maintain"
                optimization_results["summary"]["no_change"] += 1
            
            optimization_results["products_optimized"].append({
                "product_id": product.id,
                "sku": product.sku,
                "current_stock": current_stock,
                "optimized_stock": round(optimized_stock, 0),
                "current_value": round(current_value, 2),
                "optimized_value": round(optimized_value, 2),
                "value_change": round(optimized_value - current_value, 2),
                "change_type": change_type,
                "priority": product_data["urgency_level"]
            })
        
        optimization_results["current_inventory_value"] = round(current_total_value, 2)
        optimization_results["optimized_inventory_value"] = round(optimized_total_value, 2)
        optimization_results["optimization_savings"] = round(current_total_value - optimized_total_value, 2)
        
        # Generate optimization recommendations
        if optimization_results["optimization_savings"] > 0:
            optimization_results["recommendations"].append(
                f"Potential inventory investment reduction of ${optimization_results['optimization_savings']:,.2f}"
            )
        elif optimization_results["optimization_savings"] < 0:
            optimization_results["recommendations"].append(
                f"Recommended inventory investment increase of ${abs(optimization_results['optimization_savings']):,.2f} for better service level"
            )
        
        if optimization_results["summary"]["investment_reduced"] > 0:
            optimization_results["recommendations"].append(
                f"Reduce inventory for {optimization_results['summary']['investment_reduced']} products"
            )
        
        if optimization_results["summary"]["investment_increased"] > 0:
            optimization_results["recommendations"].append(
                f"Increase inventory for {optimization_results['summary']['investment_increased']} products to avoid stockouts"
            )
        
        return optimization_results
    
    # ===========================================
    # AUTOMATED REORDER EXECUTION
    # ===========================================
    
    def generate_purchase_orders(
        self,
        urgency_levels: List[str] = ["critical", "urgent"],
        auto_generate: bool = False
    ) -> Dict[str, Any]:
        """Generate purchase orders based on reorder points"""
        
        # Get reorder points for products needing reorder
        reorder_data = self.calculate_reorder_points()
        
        # Filter products that need reordering
        products_to_reorder = [
            rp for rp in reorder_data["reorder_points"]
            if rp["reorder_needed"] and rp["urgency_level"] in urgency_levels
        ]
        
        purchase_orders = {
            "generation_date": datetime.utcnow().isoformat(),
            "urgency_levels": urgency_levels,
            "auto_generate": auto_generate,
            "products_to_reorder": len(products_to_reorder),
            "purchase_orders": [],
            "total_order_value": 0.0,
            "suppliers_involved": set()
        }
        
        # Group by supplier
        supplier_orders = {}
        
        for product_data in products_to_reorder:
            product = self.db.query(Product).filter(Product.id == product_data["product_id"]).first()
            if not product:
                continue
            
            # Get primary supplier
            primary_supplier_id = product.primary_supplier_id
            if not primary_supplier_id:
                continue
            
            if primary_supplier_id not in supplier_orders:
                supplier = self.db.query(Supplier).filter(Supplier.id == primary_supplier_id).first()
                supplier_orders[primary_supplier_id] = {
                    "supplier_id": primary_supplier_id,
                    "supplier_name": supplier.company_name if supplier else "Unknown",
                    "contact_person": supplier.contact_person if supplier else "",
                    "email": supplier.email if supplier else "",
                    "products": [],
                    "total_value": 0.0
                }
            
            # Calculate order quantity
            order_quantity = product_data["eoq"]
            unit_cost = float(product.cost_price) if product.cost_price else 0
            line_total = order_quantity * unit_cost
            
            supplier_orders[primary_supplier_id]["products"].append({
                "product_id": product.id,
                "sku": product.sku,
                "product_name": product.name,
                "current_stock": product.stock_level or 0,
                "reorder_point": product_data["reorder_point"],
                "order_quantity": round(order_quantity, 0),
                "unit_cost": unit_cost,
                "line_total": round(line_total, 2),
                "urgency": product_data["urgency_level"]
            })
            
            supplier_orders[primary_supplier_id]["total_value"] += line_total
            purchase_orders["total_order_value"] += line_total
            purchase_orders["suppliers_involved"].add(primary_supplier_id)
        
        # Convert supplier orders to list
        purchase_orders["purchase_orders"] = list(supplier_orders.values())
        purchase_orders["suppliers_involved"] = len(purchase_orders["suppliers_involved"])
        
        # Sort by urgency and value
        for po in purchase_orders["purchase_orders"]:
            po["products"].sort(key=lambda x: (x["urgency"] == "critical", x["line_total"]), reverse=True)
            po["total_value"] = round(po["total_value"], 2)
        
        purchase_orders["purchase_orders"].sort(key=lambda x: x["total_value"], reverse=True)
        
        return purchase_orders