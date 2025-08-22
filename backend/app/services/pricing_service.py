"""
Pricing Service - SOLID Architecture Implementation
Handles comprehensive pricing optimization, cost analysis, and profit calculations
Single Responsibility: Manages all pricing-related business logic and optimization algorithms
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.models.database_models import (
    Product, Supplier, SupplierProduct, PriceHistory, OrderItem, Order
)
from app.schemas.schemas import (
    PriceHistoryCreate, ProductPerformanceStats, SupplierPerformanceStats,
    ProfitAnalysis
)


class PricingService:
    """
    SOLID Principle: Single Responsibility
    Manages pricing optimization, cost analysis, profit calculations,
    and competitive pricing strategies
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.default_margin_target = 30.0  # 30% minimum margin
        self.competitive_adjustment = 0.05  # 5% competitive adjustment factor
    
    # ===========================================
    # PRICING OPTIMIZATION ALGORITHMS
    # ===========================================
    
    def calculate_optimal_price(
        self,
        product_id: int,
        target_margin: Optional[float] = None,
        market_price: Optional[float] = None,
        competitive_factor: Optional[float] = None
    ) -> Dict[str, Any]:
        """Calculate optimal selling price using multiple factors"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product or not product.cost_price:
            raise ValueError("Product not found or cost price not available")
        
        target_margin = target_margin or self.default_margin_target
        competitive_factor = competitive_factor or self.competitive_adjustment
        
        cost_price = float(product.cost_price)
        current_price = float(product.selling_price) if product.selling_price else None
        
        # 1. Cost-based pricing (minimum price for target margin)
        cost_based_price = cost_price / (1 - target_margin / 100)
        
        # 2. Market-based pricing
        market_based_price = market_price
        
        # 3. Performance-based pricing (adjust based on sales performance)
        performance_multiplier = self._calculate_performance_multiplier(product_id)
        performance_based_price = cost_based_price * performance_multiplier
        
        # 4. Competitive pricing (if market price available)
        competitive_price = None
        if market_price:
            competitive_price = market_price * (1 - competitive_factor)
        
        # 5. Calculate recommended price
        price_options = [cost_based_price, performance_based_price]
        if competitive_price:
            price_options.append(competitive_price)
        
        # Use the maximum of cost-based and average of other factors
        recommended_price = max(
            cost_based_price,
            sum(price_options) / len(price_options)
        )
        
        # Round to 2 decimal places
        recommended_price = float(Decimal(str(recommended_price)).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))
        
        # Calculate margins for each price option
        recommendations = {
            "product_id": product_id,
            "sku": product.sku,
            "current_price": current_price,
            "cost_price": cost_price,
            "recommended_price": recommended_price,
            "target_margin": target_margin,
            "pricing_analysis": {
                "cost_based": {
                    "price": round(cost_based_price, 2),
                    "margin": target_margin,
                    "profit": round(cost_based_price - cost_price, 2)
                },
                "performance_based": {
                    "price": round(performance_based_price, 2),
                    "margin": round((performance_based_price - cost_price) / performance_based_price * 100, 2),
                    "profit": round(performance_based_price - cost_price, 2)
                }
            },
            "recommended_analysis": {
                "margin": round((recommended_price - cost_price) / recommended_price * 100, 2),
                "profit": round(recommended_price - cost_price, 2),
                "markup": round((recommended_price - cost_price) / cost_price * 100, 2)
            }
        }
        
        # Add competitive analysis if market price available
        if competitive_price:
            recommendations["pricing_analysis"]["competitive"] = {
                "price": round(competitive_price, 2),
                "margin": round((competitive_price - cost_price) / competitive_price * 100, 2),
                "profit": round(competitive_price - cost_price, 2)
            }
            recommendations["market_price"] = market_price
            recommendations["competitive_advantage"] = round((market_price - recommended_price) / market_price * 100, 2)
        
        return recommendations
    
    def bulk_price_optimization(
        self,
        product_ids: Optional[List[int]] = None,
        category: Optional[str] = None,
        supplier_id: Optional[int] = None,
        target_margin: Optional[float] = None
    ) -> Dict[str, Any]:
        """Optimize prices for multiple products"""
        
        query = self.db.query(Product).filter(Product.status == "active")
        
        if product_ids:
            query = query.filter(Product.id.in_(product_ids))
        elif category:
            query = query.filter(Product.category == category)
        elif supplier_id:
            query = query.filter(
                or_(
                    Product.primary_supplier_id == supplier_id,
                    Product.backup_supplier_id == supplier_id
                )
            )
        
        products = query.all()
        
        results = {
            "total_products": len(products),
            "optimized": 0,
            "failed": 0,
            "total_profit_increase": 0.0,
            "recommendations": []
        }
        
        for product in products:
            try:
                if not product.cost_price:
                    results["failed"] += 1
                    continue
                
                optimization = self.calculate_optimal_price(
                    product.id, 
                    target_margin=target_margin
                )
                
                # Calculate potential profit increase
                current_profit = 0.0
                if product.selling_price:
                    current_profit = float(product.selling_price) - float(product.cost_price)
                
                new_profit = optimization["recommended_analysis"]["profit"]
                profit_increase = new_profit - current_profit
                
                optimization["profit_increase"] = round(profit_increase, 2)
                results["recommendations"].append(optimization)
                results["total_profit_increase"] += profit_increase
                results["optimized"] += 1
                
            except Exception:
                results["failed"] += 1
                continue
        
        results["total_profit_increase"] = round(results["total_profit_increase"], 2)
        
        # Sort by profit increase potential
        results["recommendations"].sort(
            key=lambda x: x.get("profit_increase", 0), 
            reverse=True
        )
        
        return results
    
    def apply_pricing_recommendations(
        self, 
        recommendations: List[Dict[str, Any]], 
        auto_apply_threshold: Optional[float] = None
    ) -> Dict[str, Any]:
        """Apply pricing recommendations to products"""
        
        auto_apply_threshold = auto_apply_threshold or 10.0  # 10% margin improvement
        
        results = {
            "total": len(recommendations),
            "applied": 0,
            "skipped": 0,
            "failed": 0,
            "applied_products": []
        }
        
        try:
            for rec in recommendations:
                product_id = rec["product_id"]
                recommended_price = rec["recommended_price"]
                current_price = rec.get("current_price")
                
                # Check if auto-apply threshold is met
                should_apply = False
                if current_price:
                    improvement = ((recommended_price - current_price) / current_price) * 100
                    should_apply = improvement >= auto_apply_threshold
                else:
                    should_apply = True  # Apply if no current price
                
                if should_apply:
                    product = self.db.query(Product).filter(Product.id == product_id).first()
                    if product:
                        old_price = product.selling_price
                        product.selling_price = recommended_price
                        
                        # Recalculate profit margin
                        if product.cost_price:
                            margin = ((recommended_price - float(product.cost_price)) / recommended_price) * 100
                            product.profit_margin_percent = margin
                        
                        product.updated_at = datetime.utcnow()
                        
                        # Create price history
                        self._create_price_history(
                            product_id=product_id,
                            old_selling_price=float(old_price) if old_price else None,
                            new_selling_price=recommended_price,
                            change_reason="Automated pricing optimization",
                            change_type="price_update"
                        )
                        
                        results["applied"] += 1
                        results["applied_products"].append({
                            "product_id": product_id,
                            "sku": product.sku,
                            "old_price": float(old_price) if old_price else None,
                            "new_price": recommended_price
                        })
                    else:
                        results["failed"] += 1
                else:
                    results["skipped"] += 1
            
            self.db.commit()
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to apply pricing recommendations: {str(e)}")
        
        return results
    
    # ===========================================
    # COST ANALYSIS & PROFIT OPTIMIZATION
    # ===========================================
    
    def analyze_product_profitability(
        self,
        product_id: int,
        time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Comprehensive profitability analysis for a product"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        date_from = datetime.utcnow() - timedelta(days=time_period_days)
        
        # Get sales data for the period
        sales_data = self.db.query(
            func.count(OrderItem.id).label('orders'),
            func.sum(OrderItem.quantity).label('units_sold'),
            func.sum(OrderItem.total_price).label('revenue'),
            func.sum(OrderItem.total_cost).label('total_cost'),
            func.avg(OrderItem.unit_price).label('avg_selling_price'),
            func.avg(OrderItem.customer_rating).label('avg_rating')
        ).filter(
            and_(
                OrderItem.product_id == product_id,
                OrderItem.created_at >= date_from
            )
        ).first()
        
        # Get supplier cost variations
        supplier_costs = self.db.query(
            SupplierProduct.supplier_id,
            SupplierProduct.supplier_cost,
            SupplierProduct.lead_time_days,
            Supplier.name.label('supplier_name')
        ).join(Supplier, SupplierProduct.supplier_id == Supplier.id) \
         .filter(SupplierProduct.product_id == product_id) \
         .order_by(SupplierProduct.supplier_cost) \
         .all()
        
        # Calculate profitability metrics
        revenue = float(sales_data.revenue or 0)
        cost = float(sales_data.total_cost or 0)
        profit = revenue - cost
        margin = (profit / revenue * 100) if revenue > 0 else 0
        
        # Calculate ROI
        current_inventory_value = float(product.stock_level * (product.cost_price or 0))
        roi = (profit / current_inventory_value * 100) if current_inventory_value > 0 else 0
        
        analysis = {
            "product_id": product_id,
            "sku": product.sku,
            "name": product.name,
            "analysis_period_days": time_period_days,
            "current_metrics": {
                "selling_price": float(product.selling_price or 0),
                "cost_price": float(product.cost_price or 0),
                "current_margin": float(product.profit_margin_percent or 0),
                "stock_level": product.stock_level,
                "inventory_value": current_inventory_value
            },
            "period_performance": {
                "orders": sales_data.orders or 0,
                "units_sold": int(sales_data.units_sold or 0),
                "revenue": revenue,
                "total_cost": cost,
                "profit": profit,
                "margin_percent": round(margin, 2),
                "roi_percent": round(roi, 2),
                "avg_selling_price": float(sales_data.avg_selling_price or 0),
                "avg_rating": float(sales_data.avg_rating or 0)
            },
            "supplier_cost_analysis": [
                {
                    "supplier_id": sc.supplier_id,
                    "supplier_name": sc.supplier_name,
                    "cost": float(sc.supplier_cost or 0),
                    "lead_time_days": sc.lead_time_days,
                    "potential_margin": round(((float(product.selling_price or 0) - float(sc.supplier_cost or 0)) / float(product.selling_price or 1)) * 100, 2) if product.selling_price else 0,
                    "cost_savings": round(float(product.cost_price or 0) - float(sc.supplier_cost or 0), 2) if product.cost_price else 0
                }
                for sc in supplier_costs
            ]
        }
        
        # Add optimization recommendations
        analysis["optimization_recommendations"] = self._generate_profitability_recommendations(analysis)
        
        return analysis

    def get_profit_analysis(
        self, 
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        category: Optional[str] = None,
        supplier_id: Optional[int] = None
    ) -> ProfitAnalysis:
        """Get comprehensive profit analysis across products"""
        
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Base query for order items
        query = self.db.query(
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.sum(OrderItem.total_cost).label('total_cost')
        ).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        )
        
        # Apply filters
        if category:
            query = query.join(Product, OrderItem.product_id == Product.id) \
                         .filter(Product.category == category)
        
        if supplier_id:
            query = query.filter(OrderItem.supplier_id == supplier_id)
        
        totals = query.first()
        
        total_revenue = float(totals.total_revenue or 0)
        total_cost = float(totals.total_cost or 0)
        total_profit = total_revenue - total_cost
        profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        # Get top profitable products
        top_products = self._get_top_profitable_products(date_from, date_to, category, supplier_id)
        
        # Get top profitable suppliers
        top_suppliers = self._get_top_profitable_suppliers(date_from, date_to)
        
        # Get monthly trend
        monthly_trend = self._get_profit_trend(date_from, date_to)
        
        return ProfitAnalysis(
            total_revenue=total_revenue,
            total_cost=total_cost,
            total_profit=total_profit,
            profit_margin=round(profit_margin, 2),
            top_profitable_products=top_products,
            top_profitable_suppliers=top_suppliers,
            monthly_trend=monthly_trend
        )
    
    # ===========================================
    # COMPETITIVE PRICING ANALYSIS
    # ===========================================
    
    def analyze_competitive_pricing(
        self,
        product_id: int,
        competitor_prices: List[float],
        market_position: str = "competitive"  # "premium", "competitive", "budget"
    ) -> Dict[str, Any]:
        """Analyze competitive pricing and suggest positioning"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise ValueError("Product not found")
        
        if not competitor_prices:
            raise ValueError("Competitor prices required for analysis")
        
        # Calculate market statistics
        market_min = min(competitor_prices)
        market_max = max(competitor_prices)
        market_avg = sum(competitor_prices) / len(competitor_prices)
        market_median = sorted(competitor_prices)[len(competitor_prices) // 2]
        
        current_price = float(product.selling_price or 0)
        cost_price = float(product.cost_price or 0)
        
        # Calculate positioning prices
        premium_price = market_max * 0.95  # 5% below highest competitor
        competitive_price = market_avg
        budget_price = market_min * 1.05  # 5% above lowest competitor
        
        # Ensure minimum margin is met
        min_price = cost_price / (1 - self.default_margin_target / 100)
        
        positioning_options = {
            "premium": max(premium_price, min_price),
            "competitive": max(competitive_price, min_price),
            "budget": max(budget_price, min_price)
        }
        
        # Calculate margins for each position
        position_analysis = {}
        for position, price in positioning_options.items():
            margin = ((price - cost_price) / price * 100) if price > 0 else 0
            profit = price - cost_price
            
            position_analysis[position] = {
                "price": round(price, 2),
                "margin_percent": round(margin, 2),
                "profit_per_unit": round(profit, 2),
                "vs_market_avg": round(((price - market_avg) / market_avg * 100), 2),
                "rank_position": self._calculate_market_rank(price, competitor_prices)
            }
        
        # Recommend best position based on target
        recommended_position = market_position
        recommended_price = positioning_options[recommended_position]
        
        analysis = {
            "product_id": product_id,
            "sku": product.sku,
            "current_price": current_price,
            "cost_price": cost_price,
            "market_analysis": {
                "competitor_count": len(competitor_prices),
                "market_min": round(market_min, 2),
                "market_max": round(market_max, 2),
                "market_avg": round(market_avg, 2),
                "market_median": round(market_median, 2)
            },
            "positioning_options": position_analysis,
            "recommendation": {
                "position": recommended_position,
                "price": round(recommended_price, 2),
                "reasoning": self._generate_pricing_reasoning(
                    recommended_position, 
                    recommended_price, 
                    cost_price, 
                    market_avg
                )
            },
            "current_position_analysis": {
                "rank": self._calculate_market_rank(current_price, competitor_prices),
                "vs_market": round(((current_price - market_avg) / market_avg * 100), 2) if current_price > 0 else 0
            }
        }
        
        return analysis
    
    # ===========================================
    # COST TRACKING & SUPPLIER OPTIMIZATION
    # ===========================================
    
    def track_cost_changes(self, product_id: int, days: int = 90) -> Dict[str, Any]:
        """Track cost changes and supplier performance over time"""
        
        date_from = datetime.utcnow() - timedelta(days=days)
        
        # Get price history
        price_history = self.db.query(PriceHistory) \
            .filter(
                and_(
                    PriceHistory.product_id == product_id,
                    PriceHistory.created_at >= date_from
                )
            ) \
            .order_by(PriceHistory.created_at) \
            .all()
        
        # Get supplier cost variations
        supplier_costs = self.db.query(
            SupplierProduct,
            Supplier.name.label('supplier_name')
        ).join(Supplier, SupplierProduct.supplier_id == Supplier.id) \
         .filter(SupplierProduct.product_id == product_id) \
         .all()
        
        # Analyze cost trends
        cost_trend = []
        price_trend = []
        
        for record in price_history:
            if record.new_cost:
                cost_trend.append({
                    "date": record.created_at.strftime("%Y-%m-%d"),
                    "cost": float(record.new_cost),
                    "change_type": record.change_type,
                    "reason": record.change_reason
                })
            
            if record.new_selling_price:
                price_trend.append({
                    "date": record.created_at.strftime("%Y-%m-%d"),
                    "price": float(record.new_selling_price),
                    "change_type": record.change_type,
                    "impact_percent": float(record.impact_percent or 0)
                })
        
        # Calculate cost volatility
        cost_values = [item["cost"] for item in cost_trend]
        cost_volatility = 0.0
        if len(cost_values) > 1:
            avg_cost = sum(cost_values) / len(cost_values)
            variance = sum((x - avg_cost) ** 2 for x in cost_values) / len(cost_values)
            cost_volatility = (variance ** 0.5) / avg_cost * 100
        
        analysis = {
            "product_id": product_id,
            "analysis_period_days": days,
            "cost_trend": cost_trend,
            "price_trend": price_trend,
            "cost_volatility_percent": round(cost_volatility, 2),
            "supplier_cost_comparison": [
                {
                    "supplier_id": sp.SupplierProduct.supplier_id,
                    "supplier_name": sp.supplier_name,
                    "current_cost": float(sp.SupplierProduct.supplier_cost or 0),
                    "lead_time": sp.SupplierProduct.lead_time_days,
                    "quality_rating": sp.SupplierProduct.quality_rating,
                    "is_preferred": sp.SupplierProduct.is_preferred
                }
                for sp in supplier_costs
            ]
        }
        
        # Add optimization recommendations
        analysis["cost_optimization_recommendations"] = self._generate_cost_optimization_recommendations(analysis)
        
        return analysis
    
    # ===========================================
    # HELPER METHODS
    # ===========================================
    
    def _calculate_performance_multiplier(self, product_id: int) -> float:
        """Calculate performance-based pricing multiplier"""
        
        product = self.db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return 1.0
        
        # Factors: sales velocity, rating, return rate
        sales_factor = min(1.2, 1.0 + (product.total_sales / 100 * 0.1))  # Max 20% increase
        rating_factor = 1.0 + ((product.average_rating - 3.0) * 0.05)  # ±10% based on rating
        return_factor = 1.0 - (product.return_rate_percent / 100 * 0.5)  # Penalize high returns
        
        multiplier = sales_factor * rating_factor * return_factor
        return max(0.8, min(1.3, multiplier))  # Clamp between 80% and 130%
    
    def _create_price_history(
        self,
        product_id: int,
        old_cost: Optional[float] = None,
        new_cost: Optional[float] = None,
        old_selling_price: Optional[float] = None,
        new_selling_price: Optional[float] = None,
        change_reason: str = "",
        change_type: str = "price_update",
        supplier_id: Optional[int] = None
    ) -> None:
        """Create price history record"""
        
        impact_percent = None
        if old_selling_price and new_selling_price and old_selling_price > 0:
            impact_percent = ((new_selling_price - old_selling_price) / old_selling_price) * 100
        
        price_history = PriceHistory(
            product_id=product_id,
            supplier_id=supplier_id,
            old_cost=old_cost,
            new_cost=new_cost,
            old_selling_price=old_selling_price,
            new_selling_price=new_selling_price,
            change_reason=change_reason,
            change_type=change_type,
            impact_percent=impact_percent,
            changed_by="pricing_service"
        )
        
        self.db.add(price_history)
    
    def _calculate_market_rank(self, price: float, competitor_prices: List[float]) -> int:
        """Calculate market rank position (1 = cheapest)"""
        all_prices = competitor_prices + [price]
        sorted_prices = sorted(all_prices)
        return sorted_prices.index(price) + 1
    
    def _generate_pricing_reasoning(
        self, 
        position: str, 
        price: float, 
        cost: float, 
        market_avg: float
    ) -> str:
        """Generate reasoning for pricing recommendation"""
        
        margin = ((price - cost) / price * 100) if price > 0 else 0
        
        if position == "premium":
            return f"Premium positioning recommended. Price {round((price/market_avg-1)*100, 1)}% above market average with {round(margin, 1)}% margin."
        elif position == "competitive":
            return f"Competitive positioning at market average. Balanced approach with {round(margin, 1)}% margin."
        else:
            return f"Budget positioning {round((1-price/market_avg)*100, 1)}% below market average. Volume-focused with {round(margin, 1)}% margin."
    
    def _generate_profitability_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate profitability improvement recommendations"""
        
        recommendations = []
        current_margin = analysis["current_metrics"]["current_margin"]
        
        if current_margin < 20:
            recommendations.append("Consider increasing selling price - current margin below 20%")
        
        # Supplier cost analysis
        supplier_costs = analysis["supplier_cost_analysis"]
        if supplier_costs:
            cheapest = min(supplier_costs, key=lambda x: x["cost"])
            current_cost = analysis["current_metrics"]["cost_price"]
            
            if cheapest["cost"] < current_cost * 0.9:  # 10% savings available
                savings = current_cost - cheapest["cost"]
                recommendations.append(f"Switch to {cheapest['supplier_name']} for ${round(savings, 2)} cost savings per unit")
        
        # Performance-based recommendations
        period_perf = analysis["period_performance"]
        if period_perf["avg_rating"] > 4.0 and current_margin < 30:
            recommendations.append("High customer rating supports premium pricing - consider 10-15% price increase")
        
        return recommendations
    
    def _generate_cost_optimization_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate cost optimization recommendations"""
        
        recommendations = []
        
        # Cost volatility check
        if analysis["cost_volatility_percent"] > 15:
            recommendations.append("High cost volatility detected - consider locking in supplier contracts")
        
        # Supplier comparison
        suppliers = analysis["supplier_cost_comparison"]
        if len(suppliers) > 1:
            sorted_suppliers = sorted(suppliers, key=lambda x: x["current_cost"])
            cheapest = sorted_suppliers[0]
            most_expensive = sorted_suppliers[-1]
            
            cost_diff = most_expensive["current_cost"] - cheapest["current_cost"]
            if cost_diff > cheapest["current_cost"] * 0.2:  # 20% difference
                recommendations.append(f"Significant cost variance between suppliers - consider consolidating with {cheapest['supplier_name']}")
        
        return recommendations
    
    def _get_top_profitable_products(
        self, 
        date_from: datetime, 
        date_to: datetime,
        category: Optional[str] = None,
        supplier_id: Optional[int] = None
    ) -> List[ProductPerformanceStats]:
        """Get top profitable products for period"""
        
        query = self.db.query(
            Product.id,
            Product.sku,
            Product.name,
            func.sum(OrderItem.quantity).label('total_sales'),
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.avg(Product.profit_margin_percent).label('profit_margin'),
            func.avg(Product.return_rate_percent).label('return_rate')
        ).join(OrderItem, Product.id == OrderItem.product_id) \
         .filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        )
        
        if category:
            query = query.filter(Product.category == category)
        
        if supplier_id:
            query = query.filter(OrderItem.supplier_id == supplier_id)
        
        results = query.group_by(Product.id) \
                      .order_by(desc(func.sum(OrderItem.total_price))) \
                      .limit(10) \
                      .all()
        
        return [
            ProductPerformanceStats(
                product_id=r.id,
                sku=r.sku,
                name=r.name,
                total_sales=int(r.total_sales or 0),
                total_revenue=float(r.total_revenue or 0),
                profit_margin=float(r.profit_margin or 0),
                inventory_turnover=0.0,  # Would need additional calculation
                return_rate=float(r.return_rate or 0)
            )
            for r in results
        ]
    
    def _get_top_profitable_suppliers(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> List[SupplierPerformanceStats]:
        """Get top profitable suppliers for period"""
        
        results = self.db.query(
            Supplier.id,
            Supplier.name,
            func.count(OrderItem.id).label('total_orders'),
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.avg(OrderItem.delivered_date - OrderItem.created_at).label('avg_delivery'),
            func.avg(Supplier.performance_rating).label('avg_rating')
        ).join(OrderItem, Supplier.id == OrderItem.supplier_id) \
         .filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).group_by(Supplier.id) \
         .order_by(desc(func.sum(OrderItem.total_price))) \
         .limit(10) \
         .all()
        
        return [
            SupplierPerformanceStats(
                supplier_id=r.id,
                supplier_name=r.name,
                total_orders=r.total_orders or 0,
                total_revenue=float(r.total_revenue or 0),
                average_delivery_days=float(r.avg_delivery or 15),
                success_rate=100.0,  # Would need additional calculation
                quality_rating=float(r.avg_rating or 0),
                cost_efficiency=float(r.total_revenue or 0) / (r.total_orders or 1)
            )
            for r in results
        ]
    
    def _get_profit_trend(
        self, 
        date_from: datetime, 
        date_to: datetime
    ) -> List[Dict[str, Any]]:
        """Get monthly profit trend"""
        
        results = self.db.query(
            func.date_trunc('month', OrderItem.created_at).label('month'),
            func.sum(OrderItem.total_price).label('revenue'),
            func.sum(OrderItem.total_cost).label('cost')
        ).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to
            )
        ).group_by(func.date_trunc('month', OrderItem.created_at)) \
         .order_by(func.date_trunc('month', OrderItem.created_at)) \
         .all()
        
        return [
            {
                "month": r.month.strftime("%Y-%m"),
                "revenue": float(r.revenue or 0),
                "cost": float(r.cost or 0),
                "profit": float((r.revenue or 0) - (r.cost or 0))
            }
            for r in results
        ]