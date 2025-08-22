"""
Supplier Analytics API Endpoints - SOLID Architecture Implementation
Provides comprehensive supplier performance analytics and reporting endpoints
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.supplier_analytics_service import SupplierAnalyticsService
from app.schemas.schemas import (
    SupplierPerformanceStats, ProductPerformanceStats
)

router = APIRouter()


# ===========================================
# SUPPLIER PERFORMANCE DASHBOARD
# ===========================================

@router.get("/supplier-analytics/dashboard")
async def get_supplier_performance_dashboard(
    supplier_id: Optional[int] = Query(None, description="Specific supplier ID (optional)"),
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive supplier performance dashboard
    
    Returns:
    - Overall supplier performance metrics
    - Performance categorization (excellent/good/average/poor)
    - Top performers and improvement opportunities
    - Summary statistics and trends
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        dashboard_data = analytics_service.get_supplier_performance_dashboard(
            supplier_id=supplier_id,
            period_days=period_days
        )
        
        return {
            "success": True,
            "data": dashboard_data,
            "message": f"Supplier performance dashboard for {period_days} days period"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate dashboard: {str(e)}")


@router.get("/supplier-analytics/performance/{supplier_id}")
async def get_supplier_performance_details(
    supplier_id: int,
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get detailed performance analysis for a specific supplier
    
    Returns:
    - Comprehensive performance metrics
    - Cost efficiency analysis
    - Performance trends and recommendations
    - Monthly performance breakdown
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        performance_data = analytics_service._analyze_supplier_performance(
            supplier_id,
            analytics_service.db.query(analytics_service.db.query).first()  # Get date_from
        )
        
        if not performance_data:
            raise HTTPException(status_code=404, detail=f"Supplier {supplier_id} not found")
        
        return {
            "success": True,
            "data": performance_data,
            "message": f"Performance details for supplier {supplier_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze supplier performance: {str(e)}")


# ===========================================
# SUPPLIER COMPARISON & BENCHMARKING
# ===========================================

@router.post("/supplier-analytics/compare")
async def compare_suppliers(
    supplier_ids: List[int],
    metrics: Optional[List[str]] = Query(
        None, 
        description="Metrics to compare (delivery_time, quality_rating, success_rate, cost_efficiency, order_volume)"
    ),
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Compare multiple suppliers across key performance metrics
    
    Body:
    - supplier_ids: List of supplier IDs to compare
    
    Returns:
    - Side-by-side metrics comparison
    - Performance rankings for each metric
    - Recommendations based on comparison
    """
    try:
        if len(supplier_ids) < 2:
            raise HTTPException(status_code=400, detail="At least 2 suppliers required for comparison")
        
        if len(supplier_ids) > 10:
            raise HTTPException(status_code=400, detail="Maximum 10 suppliers allowed for comparison")
        
        analytics_service = SupplierAnalyticsService(db)
        comparison_data = analytics_service.compare_suppliers(
            supplier_ids=supplier_ids,
            metrics=metrics,
            period_days=period_days
        )
        
        return {
            "success": True,
            "data": comparison_data,
            "message": f"Comparison of {len(supplier_ids)} suppliers completed"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to compare suppliers: {str(e)}")


@router.get("/supplier-analytics/benchmarks")
async def get_supplier_benchmarks(
    category: Optional[str] = Query(None, description="Product category for benchmarking"),
    period_days: int = Query(30, description="Analysis period in days", ge=1, le=365),
    db: Session = Depends(get_db)
):
    """
    Get industry benchmarks and performance standards
    
    Returns:
    - Industry average metrics
    - Performance thresholds and targets
    - Top performer benchmarks
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        
        # Get all suppliers for benchmarking
        dashboard_data = analytics_service.get_supplier_performance_dashboard(
            period_days=period_days
        )
        
        # Calculate benchmarks from current supplier base
        suppliers = dashboard_data["suppliers"]
        
        if not suppliers:
            return {
                "success": True,
                "data": {
                    "benchmarks": {},
                    "thresholds": analytics_service.performance_thresholds,
                    "industry_standards": {
                        "delivery_time": {"excellent": 7, "good": 14, "average": 21},
                        "quality_rating": {"excellent": 4.5, "good": 4.0, "average": 3.5},
                        "success_rate": {"excellent": 98, "good": 95, "average": 90}
                    }
                },
                "message": "No supplier data available for benchmarking"
            }
        
        # Calculate percentiles
        delivery_times = [s["metrics"]["avg_delivery_days"] for s in suppliers if s["metrics"]["avg_delivery_days"] > 0]
        quality_ratings = [s["metrics"]["quality_rating"] for s in suppliers if s["metrics"]["quality_rating"] > 0]
        success_rates = [s["metrics"]["success_rate"] for s in suppliers if s["metrics"]["success_rate"] > 0]
        
        benchmarks = {}
        
        if delivery_times:
            delivery_times.sort()
            benchmarks["delivery_time"] = {
                "p25": delivery_times[len(delivery_times)//4] if delivery_times else 0,
                "p50": delivery_times[len(delivery_times)//2] if delivery_times else 0,
                "p75": delivery_times[len(delivery_times)*3//4] if delivery_times else 0,
                "best": min(delivery_times)
            }
        
        if quality_ratings:
            quality_ratings.sort(reverse=True)
            benchmarks["quality_rating"] = {
                "p25": quality_ratings[len(quality_ratings)*3//4] if quality_ratings else 0,
                "p50": quality_ratings[len(quality_ratings)//2] if quality_ratings else 0,
                "p75": quality_ratings[len(quality_ratings)//4] if quality_ratings else 0,
                "best": max(quality_ratings)
            }
        
        if success_rates:
            success_rates.sort(reverse=True)
            benchmarks["success_rate"] = {
                "p25": success_rates[len(success_rates)*3//4] if success_rates else 0,
                "p50": success_rates[len(success_rates)//2] if success_rates else 0,
                "p75": success_rates[len(success_rates)//4] if success_rates else 0,
                "best": max(success_rates)
            }
        
        return {
            "success": True,
            "data": {
                "benchmarks": benchmarks,
                "thresholds": analytics_service.performance_thresholds,
                "industry_standards": {
                    "delivery_time": {"excellent": 7, "good": 14, "average": 21},
                    "quality_rating": {"excellent": 4.5, "good": 4.0, "average": 3.5},
                    "success_rate": {"excellent": 98, "good": 95, "average": 90}
                },
                "sample_size": len(suppliers)
            },
            "message": f"Benchmarks calculated from {len(suppliers)} suppliers"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to calculate benchmarks: {str(e)}")


# ===========================================
# SUPPLIER RISK ASSESSMENT
# ===========================================

@router.get("/supplier-analytics/risk-assessment/{supplier_id}")
async def assess_supplier_risk(
    supplier_id: int,
    period_days: int = Query(90, description="Risk assessment period in days", ge=30, le=365),
    db: Session = Depends(get_db)
):
    """
    Comprehensive supplier risk assessment
    
    Returns:
    - Overall risk score and level
    - Identified risk factors
    - Mitigation strategies and recommendations
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        risk_assessment = analytics_service.assess_supplier_risk(
            supplier_id=supplier_id,
            period_days=period_days
        )
        
        return {
            "success": True,
            "data": risk_assessment,
            "message": f"Risk assessment completed for supplier {supplier_id}"
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to assess supplier risk: {str(e)}")


@router.get("/supplier-analytics/risk-overview")
async def get_supplier_risk_overview(
    risk_level: Optional[str] = Query(None, description="Filter by risk level (low/medium/high)"),
    period_days: int = Query(90, description="Risk assessment period in days", ge=30, le=365),
    db: Session = Depends(get_db)
):
    """
    Get overview of supplier risks across all suppliers
    
    Returns:
    - Risk distribution across supplier base
    - High-risk suppliers requiring attention
    - Risk mitigation priorities
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        
        # Get all active suppliers
        suppliers = db.query(analytics_service.db.query.model.Supplier).filter(
            analytics_service.db.query.model.Supplier.status == "active"
        ).all()
        
        risk_overview = {
            "assessment_date": analytics_service.db.query.func.now(),
            "period_days": period_days,
            "total_suppliers": len(suppliers),
            "risk_distribution": {"low": 0, "medium": 0, "high": 0},
            "high_risk_suppliers": [],
            "risk_summary": [],
            "mitigation_priorities": []
        }
        
        for supplier in suppliers[:20]:  # Limit to 20 suppliers for performance
            try:
                risk_data = analytics_service.assess_supplier_risk(supplier.id, period_days)
                
                # Count risk distribution
                risk_level = risk_data["risk_level"]
                risk_overview["risk_distribution"][risk_level] += 1
                
                # Collect high-risk suppliers
                if risk_level == "high":
                    risk_overview["high_risk_suppliers"].append({
                        "supplier_id": supplier.id,
                        "supplier_name": supplier.company_name,
                        "risk_score": risk_data["overall_risk_score"],
                        "primary_risks": [rf["factor"] for rf in risk_data["risk_factors"][:3]]
                    })
                
                # Add to summary
                risk_overview["risk_summary"].append({
                    "supplier_id": supplier.id,
                    "supplier_name": supplier.company_name,
                    "risk_level": risk_level,
                    "risk_score": risk_data["overall_risk_score"]
                })
                
            except Exception:
                continue  # Skip suppliers with errors
        
        # Sort high-risk suppliers by risk score
        risk_overview["high_risk_suppliers"].sort(key=lambda x: x["risk_score"], reverse=True)
        
        # Generate mitigation priorities
        risk_factors_count = {}
        for supplier_summary in risk_overview["risk_summary"]:
            if supplier_summary["risk_level"] in ["medium", "high"]:
                # This is simplified - in real implementation, we'd track actual risk factors
                risk_factors_count["performance_issues"] = risk_factors_count.get("performance_issues", 0) + 1
        
        risk_overview["mitigation_priorities"] = [
            {
                "priority": "high",
                "action": "Performance improvement plans",
                "affected_suppliers": risk_factors_count.get("performance_issues", 0)
            }
        ]
        
        return {
            "success": True,
            "data": risk_overview,
            "message": f"Risk overview for {len(suppliers)} suppliers completed"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate risk overview: {str(e)}")


# ===========================================
# SUPPLIER ANALYTICS REPORTS
# ===========================================

@router.get("/supplier-analytics/reports/performance-summary")
async def generate_performance_summary_report(
    period_days: int = Query(30, description="Report period in days", ge=1, le=365),
    format: str = Query("json", description="Report format (json, csv)"),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: Session = Depends(get_db)
):
    """
    Generate comprehensive supplier performance summary report
    
    Returns:
    - Executive summary of supplier performance
    - Key metrics and trends
    - Action items and recommendations
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        dashboard_data = analytics_service.get_supplier_performance_dashboard(
            period_days=period_days
        )
        
        # Generate executive summary
        summary_data = dashboard_data["summary_metrics"]
        suppliers = dashboard_data["suppliers"]
        
        report = {
            "report_type": "supplier_performance_summary",
            "generated_at": analytics_service.db.query.func.now(),
            "period_days": period_days,
            "executive_summary": {
                "total_suppliers_analyzed": len(suppliers),
                "average_performance_score": sum(s["performance_score"] for s in suppliers) / len(suppliers) if suppliers else 0,
                "top_performer": suppliers[0]["supplier_name"] if suppliers else "N/A",
                "improvement_needed": len([s for s in suppliers if s["performance_score"] < 60]),
                "key_metrics": summary_data
            },
            "performance_distribution": dashboard_data["performance_categories"],
            "top_performers": dashboard_data["top_performers"][:3],
            "improvement_opportunities": dashboard_data["improvement_opportunities"],
            "action_items": [
                "Review contracts with underperforming suppliers",
                "Implement performance improvement plans",
                "Negotiate better terms with top performers",
                "Diversify supplier base to reduce risk"
            ],
            "recommendations": [
                "Focus on delivery time improvements",
                "Strengthen quality control processes",
                "Optimize cost efficiency through negotiation",
                "Implement supplier scorecards for ongoing monitoring"
            ]
        }
        
        if format.lower() == "csv":
            # For CSV format, we'd typically generate a file and return a download link
            # For now, return JSON with a note about CSV conversion
            report["note"] = "CSV export functionality would be implemented for production use"
        
        return {
            "success": True,
            "data": report,
            "message": f"Performance summary report generated for {period_days} days period"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/supplier-analytics/reports/cost-efficiency")
async def generate_cost_efficiency_report(
    period_days: int = Query(30, description="Report period in days", ge=1, le=365),
    min_margin: float = Query(20.0, description="Minimum acceptable margin percentage"),
    db: Session = Depends(get_db)
):
    """
    Generate cost efficiency analysis report
    
    Returns:
    - Cost efficiency metrics across suppliers
    - Margin analysis and optimization opportunities
    - Cost-saving recommendations
    """
    try:
        analytics_service = SupplierAnalyticsService(db)
        dashboard_data = analytics_service.get_supplier_performance_dashboard(
            period_days=period_days
        )
        
        suppliers = dashboard_data["suppliers"]
        
        # Analyze cost efficiency
        cost_analysis = {
            "report_type": "cost_efficiency_analysis",
            "generated_at": analytics_service.db.query.func.now(),
            "period_days": period_days,
            "min_margin_threshold": min_margin,
            "summary": {
                "suppliers_analyzed": len(suppliers),
                "avg_cost_efficiency": sum(s["cost_efficiency"]["efficiency_score"] for s in suppliers) / len(suppliers) if suppliers else 0,
                "below_threshold": len([s for s in suppliers if s["cost_efficiency"]["avg_margin"] < min_margin]),
                "optimization_potential": 0.0
            },
            "supplier_analysis": [],
            "optimization_opportunities": [],
            "recommendations": []
        }
        
        total_potential_savings = 0.0
        
        for supplier in suppliers:
            cost_eff = supplier["cost_efficiency"]
            supplier_analysis = {
                "supplier_id": supplier["supplier_id"],
                "supplier_name": supplier["supplier_name"],
                "efficiency_score": cost_eff["efficiency_score"],
                "avg_margin": cost_eff["avg_margin"],
                "meets_threshold": cost_eff["avg_margin"] >= min_margin,
                "improvement_potential": max(0, min_margin - cost_eff["avg_margin"])
            }
            
            cost_analysis["supplier_analysis"].append(supplier_analysis)
            
            # Calculate potential savings
            if supplier_analysis["improvement_potential"] > 0:
                potential_value = supplier["metrics"]["total_value"] * (supplier_analysis["improvement_potential"] / 100)
                total_potential_savings += potential_value
                
                cost_analysis["optimization_opportunities"].append({
                    "supplier_id": supplier["supplier_id"],
                    "supplier_name": supplier["supplier_name"],
                    "current_margin": cost_eff["avg_margin"],
                    "target_margin": min_margin,
                    "potential_savings": round(potential_value, 2)
                })
        
        cost_analysis["summary"]["optimization_potential"] = round(total_potential_savings, 2)
        
        # Generate recommendations
        if cost_analysis["summary"]["below_threshold"] > 0:
            cost_analysis["recommendations"].extend([
                "Renegotiate pricing with underperforming suppliers",
                "Consider alternative suppliers for better margins",
                "Implement volume-based pricing tiers"
            ])
        
        if total_potential_savings > 1000:
            cost_analysis["recommendations"].append(f"Potential annual savings of ${total_potential_savings:,.2f} identified")
        
        return {
            "success": True,
            "data": cost_analysis,
            "message": f"Cost efficiency report generated with ${total_potential_savings:,.2f} optimization potential"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate cost efficiency report: {str(e)}")