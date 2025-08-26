"""
Supplier Performance Analytics Service - SOLID Architecture Implementation
Handles comprehensive supplier analytics, performance tracking, and reporting
Single Responsibility: Manages all supplier performance analysis and reporting
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc, text

from app.models.database_models import (
    Supplier, SupplierProduct, Product, OrderItem, Order, PriceHistory
)
from app.schemas.schemas import (
    SupplierPerformanceStats, ProductPerformanceStats
)


class SupplierAnalyticsService:
    """
    SOLID Principle: Single Responsibility
    Manages supplier performance analytics, KPI tracking, and comprehensive reporting
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.default_analysis_period = 30  # Days
        self.performance_thresholds = {
            "delivery_time": 14,  # days
            "quality_rating": 4.0,  # out of 5
            "success_rate": 95.0,  # percentage
            "cost_efficiency": 10.0  # percentage savings
        }
    
    # ===========================================
    # COMPREHENSIVE SUPPLIER PERFORMANCE
    # ===========================================
    
    def get_supplier_performance_dashboard(
        self,
        supplier_id: Optional[int] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Get comprehensive supplier performance dashboard"""
        
        date_from = datetime.utcnow() - timedelta(days=period_days)
        
        if supplier_id:
            suppliers = [self.db.query(Supplier).filter(Supplier.id == supplier_id).first()]
            if not suppliers[0]:
                raise ValueError(f"Supplier {supplier_id} not found")
        else:
            suppliers = self.db.query(Supplier).filter(Supplier.status == "active").all()
        
        dashboard_data = {
            "period_days": period_days,
            "total_suppliers": len(suppliers),
            "analysis_date": datetime.utcnow().isoformat(),
            "suppliers": [],
            "summary_metrics": {
                "avg_delivery_time": 0.0,
                "avg_quality_rating": 0.0,
                "avg_success_rate": 0.0,
                "total_orders": 0,
                "total_value": 0.0
            },
            "performance_categories": {
                "excellent": 0,
                "good": 0,
                "average": 0,
                "poor": 0
            },
            "top_performers": [],
            "improvement_opportunities": []
        }
        
        total_delivery_time = 0
        total_quality_rating = 0
        total_success_rate = 0
        total_orders = 0
        total_value = 0.0
        
        for supplier in suppliers:
            supplier_performance = self._analyze_supplier_performance(supplier.id, date_from)
            dashboard_data["suppliers"].append(supplier_performance)
            
            # Aggregate metrics
            if supplier_performance["metrics"]["avg_delivery_days"]:
                total_delivery_time += supplier_performance["metrics"]["avg_delivery_days"]
            total_quality_rating += supplier_performance["metrics"]["quality_rating"]
            total_success_rate += supplier_performance["metrics"]["success_rate"]
            total_orders += supplier_performance["metrics"]["total_orders"]
            total_value += supplier_performance["metrics"]["total_value"]
            
            # Categorize performance
            performance_score = supplier_performance["performance_score"]
            if performance_score >= 90:
                dashboard_data["performance_categories"]["excellent"] += 1
            elif performance_score >= 75:
                dashboard_data["performance_categories"]["good"] += 1
            elif performance_score >= 60:
                dashboard_data["performance_categories"]["average"] += 1
            else:
                dashboard_data["performance_categories"]["poor"] += 1
        
        # Calculate summary metrics
        if suppliers:
            dashboard_data["summary_metrics"] = {
                "avg_delivery_time": round(total_delivery_time / len(suppliers), 1),
                "avg_quality_rating": round(total_quality_rating / len(suppliers), 2),
                "avg_success_rate": round(total_success_rate / len(suppliers), 1),
                "total_orders": total_orders,
                "total_value": round(total_value, 2)
            }
        
        # Sort suppliers by performance and extract top performers
        dashboard_data["suppliers"].sort(key=lambda x: x["performance_score"], reverse=True)
        dashboard_data["top_performers"] = dashboard_data["suppliers"][:5]
        
        # Identify improvement opportunities
        dashboard_data["improvement_opportunities"] = self._identify_improvement_opportunities(
            dashboard_data["suppliers"]
        )
        
        return dashboard_data
    
    def _analyze_supplier_performance(
        self, 
        supplier_id: int, 
        date_from: datetime
    ) -> Dict[str, Any]:
        """Analyze individual supplier performance"""
        
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        if not supplier:
            return {}
        
        # Get order data for the period
        order_data = self.db.query(
            func.count(OrderItem.id).label('total_orders'),
            func.sum(OrderItem.total_price).label('total_value'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.avg(OrderItem.unit_price).label('avg_unit_price'),
            func.avg(OrderItem.customer_rating).label('avg_rating')
        ).filter(
            and_(
                OrderItem.supplier_id == supplier_id,
                OrderItem.created_at >= date_from
            )
        ).first()
        
        # Get delivery performance
        delivery_data = self.db.query(
            func.avg(
                func.extract('day', OrderItem.delivered_date - OrderItem.created_at)
            ).label('avg_delivery_days'),
            func.count(
                func.case(
                    (OrderItem.delivered_date.isnot(None), 1),
                    else_=None
                )
            ).label('delivered_orders'),
            func.count(
                func.case(
                    (OrderItem.status == 'cancelled', 1),
                    else_=None
                )
            ).label('cancelled_orders')
        ).filter(
            and_(
                OrderItem.supplier_id == supplier_id,
                OrderItem.created_at >= date_from
            )
        ).first()
        
        # Get product variety
        product_variety = self.db.query(
            func.count(func.distinct(Product.category)).label('categories'),
            func.count(func.distinct(SupplierProduct.product_id)).label('products')
        ).join(SupplierProduct, Product.id == SupplierProduct.product_id) \
         .filter(SupplierProduct.supplier_id == supplier_id).first()
        
        # Calculate metrics
        total_orders = order_data.total_orders or 0
        delivered_orders = delivery_data.delivered_orders or 0
        cancelled_orders = delivery_data.cancelled_orders or 0
        
        success_rate = (delivered_orders / total_orders * 100) if total_orders > 0 else 0
        avg_delivery_days = float(delivery_data.avg_delivery_days or 0)
        
        # Calculate performance score (0-100)
        performance_score = self._calculate_performance_score({
            "delivery_time": avg_delivery_days,
            "quality_rating": float(order_data.avg_rating or 0),
            "success_rate": success_rate,
            "total_orders": total_orders
        })
        
        # Cost efficiency analysis
        cost_efficiency = self._calculate_cost_efficiency(supplier_id, date_from)
        
        return {
            "supplier_id": supplier_id,
            "supplier_name": supplier.company_name,
            "contact_person": supplier.contact_person,
            "metrics": {
                "total_orders": total_orders,
                "total_value": float(order_data.total_value or 0),
                "total_quantity": int(order_data.total_quantity or 0),
                "avg_delivery_days": avg_delivery_days,
                "success_rate": round(success_rate, 1),
                "quality_rating": float(order_data.avg_rating or 0),
                "cancelled_orders": cancelled_orders,
                "product_variety": int(product_variety.products or 0),
                "category_coverage": int(product_variety.categories or 0)
            },
            "cost_efficiency": cost_efficiency,
            "performance_score": round(performance_score, 1),
            "performance_category": self._get_performance_category(performance_score),
            "trends": self._analyze_supplier_trends(supplier_id, date_from),
            "recommendations": self._generate_supplier_recommendations(supplier_id, {
                "delivery_time": avg_delivery_days,
                "quality_rating": float(order_data.avg_rating or 0),
                "success_rate": success_rate,
                "cost_efficiency": cost_efficiency["efficiency_score"]
            })
        }
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate overall performance score (0-100)"""
        
        score = 0.0
        
        # Delivery time score (30% weight)
        if metrics["delivery_time"] > 0:
            delivery_score = max(0, (self.performance_thresholds["delivery_time"] - metrics["delivery_time"]) / self.performance_thresholds["delivery_time"] * 100)
            score += delivery_score * 0.3
        
        # Quality rating score (25% weight)
        quality_score = (metrics["quality_rating"] / 5.0) * 100
        score += quality_score * 0.25
        
        # Success rate score (25% weight)
        score += metrics["success_rate"] * 0.25
        
        # Order volume score (20% weight)
        volume_score = min(100, metrics["total_orders"] * 2)  # 50 orders = 100%
        score += volume_score * 0.2
        
        return min(100, max(0, score))
    
    def _get_performance_category(self, score: float) -> str:
        """Get performance category based on score"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "average"
        else:
            return "poor"
    
    def _calculate_cost_efficiency(
        self, 
        supplier_id: int, 
        date_from: datetime
    ) -> Dict[str, Any]:
        """Calculate cost efficiency metrics"""
        
        # Get supplier costs vs market prices
        supplier_products = self.db.query(
            SupplierProduct.product_id,
            SupplierProduct.supplier_cost,
            Product.selling_price,
            Product.name
        ).join(Product, SupplierProduct.product_id == Product.id) \
         .filter(SupplierProduct.supplier_id == supplier_id).all()
        
        if not supplier_products:
            return {
                "efficiency_score": 0.0,
                "avg_margin": 0.0,
                "cost_savings": 0.0,
                "product_analysis": []
            }
        
        total_margin = 0.0
        total_products = 0
        product_analysis = []
        
        for sp in supplier_products:
            if sp.supplier_cost and sp.selling_price:
                cost = float(sp.supplier_cost)
                price = float(sp.selling_price)
                margin = ((price - cost) / price) * 100
                total_margin += margin
                total_products += 1
                
                product_analysis.append({
                    "product_id": sp.product_id,
                    "product_name": sp.name,
                    "cost": cost,
                    "selling_price": price,
                    "margin": round(margin, 2)
                })
        
        avg_margin = total_margin / total_products if total_products > 0 else 0
        
        # Calculate efficiency score based on margin
        efficiency_score = min(100, avg_margin * 2)  # 50% margin = 100% efficiency
        
        return {
            "efficiency_score": round(efficiency_score, 1),
            "avg_margin": round(avg_margin, 2),
            "cost_savings": 0.0,  # Would need competitor comparison
            "product_analysis": product_analysis[:10]  # Top 10 products
        }
    
    def _analyze_supplier_trends(
        self, 
        supplier_id: int, 
        date_from: datetime
    ) -> Dict[str, Any]:
        """Analyze supplier performance trends"""
        
        # Get monthly performance data
        monthly_data = self.db.query(
            func.date_trunc('month', OrderItem.created_at).label('month'),
            func.count(OrderItem.id).label('orders'),
            func.sum(OrderItem.total_price).label('value'),
            func.avg(OrderItem.customer_rating).label('rating')
        ).filter(
            and_(
                OrderItem.supplier_id == supplier_id,
                OrderItem.created_at >= date_from
            )
        ).group_by(func.date_trunc('month', OrderItem.created_at)) \
         .order_by(func.date_trunc('month', OrderItem.created_at)).all()
        
        trends = {
            "monthly_performance": [
                {
                    "month": data.month.strftime("%Y-%m"),
                    "orders": data.orders or 0,
                    "value": float(data.value or 0),
                    "avg_rating": float(data.rating or 0)
                }
                for data in monthly_data
            ],
            "order_trend": "stable",
            "value_trend": "stable",
            "quality_trend": "stable"
        }
        
        # Calculate trends
        if len(trends["monthly_performance"]) >= 2:
            first_month = trends["monthly_performance"][0]
            last_month = trends["monthly_performance"][-1]
            
            # Order trend
            order_change = (last_month["orders"] - first_month["orders"]) / first_month["orders"] * 100 if first_month["orders"] > 0 else 0
            trends["order_trend"] = "increasing" if order_change > 10 else "decreasing" if order_change < -10 else "stable"
            
            # Value trend
            value_change = (last_month["value"] - first_month["value"]) / first_month["value"] * 100 if first_month["value"] > 0 else 0
            trends["value_trend"] = "increasing" if value_change > 10 else "decreasing" if value_change < -10 else "stable"
            
            # Quality trend
            quality_change = last_month["avg_rating"] - first_month["avg_rating"]
            trends["quality_trend"] = "improving" if quality_change > 0.2 else "declining" if quality_change < -0.2 else "stable"
        
        return trends
    
    def _generate_supplier_recommendations(
        self, 
        supplier_id: int, 
        metrics: Dict[str, Any]
    ) -> List[str]:
        """Generate improvement recommendations for supplier"""
        
        recommendations = []
        
        # Delivery time recommendations
        if metrics["delivery_time"] > self.performance_thresholds["delivery_time"]:
            recommendations.append(f"Improve delivery time - currently {metrics['delivery_time']:.1f} days vs target {self.performance_thresholds['delivery_time']} days")
        
        # Quality recommendations
        if metrics["quality_rating"] < self.performance_thresholds["quality_rating"]:
            recommendations.append(f"Focus on quality improvement - current rating {metrics['quality_rating']:.1f}/5.0")
        
        # Success rate recommendations
        if metrics["success_rate"] < self.performance_thresholds["success_rate"]:
            recommendations.append(f"Reduce order cancellations - current success rate {metrics['success_rate']:.1f}%")
        
        # Cost efficiency recommendations
        if metrics["cost_efficiency"] < 70:
            recommendations.append("Negotiate better pricing to improve cost efficiency")
        
        # Add positive reinforcements
        if metrics["quality_rating"] >= 4.5:
            recommendations.append("Excellent quality standards - maintain current performance")
        
        if metrics["delivery_time"] <= 7:
            recommendations.append("Outstanding delivery performance - leverage as competitive advantage")
        
        return recommendations
    
    def _identify_improvement_opportunities(
        self, 
        suppliers: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Identify improvement opportunities across suppliers"""
        
        opportunities = []
        
        # Find suppliers with poor performance
        poor_performers = [s for s in suppliers if s["performance_score"] < 60]
        if poor_performers:
            opportunities.append({
                "type": "performance_improvement",
                "priority": "high",
                "description": f"{len(poor_performers)} suppliers need performance improvement",
                "affected_suppliers": [s["supplier_id"] for s in poor_performers]
            })
        
        # Find delivery time issues
        slow_delivery = [s for s in suppliers if s["metrics"]["avg_delivery_days"] > 14]
        if slow_delivery:
            opportunities.append({
                "type": "delivery_optimization",
                "priority": "medium",
                "description": f"{len(slow_delivery)} suppliers have slow delivery times",
                "affected_suppliers": [s["supplier_id"] for s in slow_delivery]
            })
        
        # Find cost efficiency opportunities
        inefficient_cost = [s for s in suppliers if s["cost_efficiency"]["efficiency_score"] < 70]
        if inefficient_cost:
            opportunities.append({
                "type": "cost_optimization",
                "priority": "high",
                "description": f"{len(inefficient_cost)} suppliers have cost efficiency issues",
                "affected_suppliers": [s["supplier_id"] for s in inefficient_cost]
            })
        
        return opportunities
    
    # ===========================================
    # SUPPLIER COMPARISON & BENCHMARKING
    # ===========================================
    
    def compare_suppliers(
        self,
        supplier_ids: List[int],
        metrics: List[str] = None,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """Compare multiple suppliers across key metrics"""
        
        if not metrics:
            metrics = ["delivery_time", "quality_rating", "success_rate", "cost_efficiency", "order_volume"]
        
        date_from = datetime.utcnow() - timedelta(days=period_days)
        comparison_data = {
            "comparison_date": datetime.utcnow().isoformat(),
            "period_days": period_days,
            "suppliers": [],
            "metrics_comparison": {},
            "rankings": {},
            "recommendations": []
        }
        
        # Get performance data for each supplier
        for supplier_id in supplier_ids:
            supplier_performance = self._analyze_supplier_performance(supplier_id, date_from)
            comparison_data["suppliers"].append(supplier_performance)
        
        # Create metrics comparison
        for metric in metrics:
            comparison_data["metrics_comparison"][metric] = []
            
            for supplier in comparison_data["suppliers"]:
                if metric == "delivery_time":
                    value = supplier["metrics"]["avg_delivery_days"]
                elif metric == "quality_rating":
                    value = supplier["metrics"]["quality_rating"]
                elif metric == "success_rate":
                    value = supplier["metrics"]["success_rate"]
                elif metric == "cost_efficiency":
                    value = supplier["cost_efficiency"]["efficiency_score"]
                elif metric == "order_volume":
                    value = supplier["metrics"]["total_orders"]
                else:
                    value = 0
                
                comparison_data["metrics_comparison"][metric].append({
                    "supplier_id": supplier["supplier_id"],
                    "supplier_name": supplier["supplier_name"],
                    "value": value
                })
        
        # Create rankings
        for metric in metrics:
            metric_data = comparison_data["metrics_comparison"][metric]
            
            # Sort based on metric (ascending for delivery_time, descending for others)
            reverse_sort = metric != "delivery_time"
            sorted_data = sorted(metric_data, key=lambda x: x["value"], reverse=reverse_sort)
            
            comparison_data["rankings"][metric] = [
                {
                    "rank": idx + 1,
                    "supplier_id": item["supplier_id"],
                    "supplier_name": item["supplier_name"],
                    "value": item["value"]
                }
                for idx, item in enumerate(sorted_data)
            ]
        
        # Generate comparison recommendations
        comparison_data["recommendations"] = self._generate_comparison_recommendations(
            comparison_data["rankings"]
        )
        
        return comparison_data
    
    def _generate_comparison_recommendations(
        self, 
        rankings: Dict[str, List[Dict[str, Any]]]
    ) -> List[str]:
        """Generate recommendations based on supplier comparison"""
        
        recommendations = []
        
        # Find best performers
        if "delivery_time" in rankings and rankings["delivery_time"]:
            best_delivery = rankings["delivery_time"][0]
            recommendations.append(f"Best delivery: {best_delivery['supplier_name']} ({best_delivery['value']:.1f} days)")
        
        if "quality_rating" in rankings and rankings["quality_rating"]:
            best_quality = rankings["quality_rating"][0]
            recommendations.append(f"Highest quality: {best_quality['supplier_name']} ({best_quality['value']:.1f}/5.0)")
        
        if "cost_efficiency" in rankings and rankings["cost_efficiency"]:
            best_cost = rankings["cost_efficiency"][0]
            recommendations.append(f"Best cost efficiency: {best_cost['supplier_name']} ({best_cost['value']:.1f}%)")
        
        # Identify consolidation opportunities
        if len(rankings.get("order_volume", [])) > 3:
            low_volume_suppliers = [s for s in rankings["order_volume"] if s["value"] < 10]
            if len(low_volume_suppliers) > 1:
                recommendations.append(f"Consider consolidating {len(low_volume_suppliers)} low-volume suppliers")
        
        return recommendations
    
    # ===========================================
    # SUPPLIER RISK ASSESSMENT
    # ===========================================
    
    def assess_supplier_risk(
        self, 
        supplier_id: int, 
        period_days: int = 90
    ) -> Dict[str, Any]:
        """Comprehensive supplier risk assessment"""
        
        date_from = datetime.utcnow() - timedelta(days=period_days)
        supplier = self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
        
        if not supplier:
            raise ValueError(f"Supplier {supplier_id} not found")
        
        risk_assessment = {
            "supplier_id": supplier_id,
            "supplier_name": supplier.company_name,
            "assessment_date": datetime.utcnow().isoformat(),
            "period_days": period_days,
            "overall_risk_score": 0.0,
            "risk_level": "low",
            "risk_factors": [],
            "mitigation_strategies": []
        }
        
        risk_score = 0.0
        
        # Performance risk
        performance_data = self._analyze_supplier_performance(supplier_id, date_from)
        if performance_data["performance_score"] < 60:
            risk_score += 30
            risk_assessment["risk_factors"].append({
                "factor": "poor_performance",
                "severity": "high",
                "description": f"Performance score below 60% ({performance_data['performance_score']:.1f}%)"
            })
        
        # Delivery risk
        if performance_data["metrics"]["avg_delivery_days"] > 21:
            risk_score += 20
            risk_assessment["risk_factors"].append({
                "factor": "delivery_delays",
                "severity": "medium",
                "description": f"Average delivery time {performance_data['metrics']['avg_delivery_days']:.1f} days"
            })
        
        # Quality risk
        if performance_data["metrics"]["quality_rating"] < 3.5:
            risk_score += 25
            risk_assessment["risk_factors"].append({
                "factor": "quality_issues",
                "severity": "high",
                "description": f"Quality rating below 3.5 ({performance_data['metrics']['quality_rating']:.1f})"
            })
        
        # Financial risk (order cancellation rate)
        cancellation_rate = (performance_data["metrics"]["cancelled_orders"] / max(1, performance_data["metrics"]["total_orders"])) * 100
        if cancellation_rate > 10:
            risk_score += 15
            risk_assessment["risk_factors"].append({
                "factor": "high_cancellation_rate",
                "severity": "medium",
                "description": f"Order cancellation rate {cancellation_rate:.1f}%"
            })
        
        # Dependency risk (check if this supplier has too much volume)
        total_orders = self.db.query(func.count(OrderItem.id)).filter(
            OrderItem.created_at >= date_from
        ).scalar()
        
        supplier_orders = performance_data["metrics"]["total_orders"]
        dependency_ratio = (supplier_orders / max(1, total_orders)) * 100
        
        if dependency_ratio > 30:
            risk_score += 10
            risk_assessment["risk_factors"].append({
                "factor": "high_dependency",
                "severity": "medium",
                "description": f"Supplier handles {dependency_ratio:.1f}% of total orders"
            })
        
        # Determine risk level
        risk_assessment["overall_risk_score"] = min(100, risk_score)
        
        if risk_score >= 70:
            risk_assessment["risk_level"] = "high"
        elif risk_score >= 40:
            risk_assessment["risk_level"] = "medium"
        else:
            risk_assessment["risk_level"] = "low"
        
        # Generate mitigation strategies
        risk_assessment["mitigation_strategies"] = self._generate_risk_mitigation_strategies(
            risk_assessment["risk_factors"]
        )
        
        return risk_assessment
    
    def _generate_risk_mitigation_strategies(
        self, 
        risk_factors: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate risk mitigation strategies"""
        
        strategies = []
        
        for factor in risk_factors:
            if factor["factor"] == "poor_performance":
                strategies.append("Implement performance improvement plan with monthly reviews")
                strategies.append("Consider backup supplier for critical products")
            
            elif factor["factor"] == "delivery_delays":
                strategies.append("Negotiate delivery time commitments with penalties")
                strategies.append("Implement buffer inventory for this supplier")
            
            elif factor["factor"] == "quality_issues":
                strategies.append("Implement quality control inspections")
                strategies.append("Request quality improvement action plan")
            
            elif factor["factor"] == "high_cancellation_rate":
                strategies.append("Review order processes and communication")
                strategies.append("Implement order confirmation requirements")
            
            elif factor["factor"] == "high_dependency":
                strategies.append("Diversify supplier base to reduce dependency")
                strategies.append("Develop alternative suppliers for key products")
        
        return strategies