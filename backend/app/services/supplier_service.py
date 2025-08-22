"""
Supplier Management Service - SOLID Architecture Implementation
Handles comprehensive supplier management with performance tracking
Single Responsibility: Manages all supplier-related business logic
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc

from app.models.database_models import (
    Supplier, Product, SupplierProduct, PriceHistory, OrderItem, Order
)
from app.schemas.schemas import (
    SupplierCreate, SupplierUpdate, SupplierStatus, SupplierBusinessType,
    DiscountTier, SupplierPerformanceStats, PaginationParams, FilterParams
)


class SupplierService:
    """
    SOLID Principle: Single Responsibility
    Manages all supplier-related operations including CRUD, performance tracking,
    and business intelligence analytics
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ===========================================
    # CORE CRUD OPERATIONS
    # ===========================================
    
    def create_supplier(self, supplier_data: SupplierCreate) -> Supplier:
        """Create a new supplier with initial performance metrics"""
        try:
            # Check for duplicate email
            if supplier_data.email:
                existing = self.get_supplier_by_email(supplier_data.email)
                if existing:
                    raise ValueError(f"Supplier with email {supplier_data.email} already exists")
            
            # Create new supplier
            db_supplier = Supplier(
                name=supplier_data.name,
                company_name=supplier_data.company_name,
                contact_person=supplier_data.contact_person,
                email=supplier_data.email,
                phone=supplier_data.phone,
                address=supplier_data.address,
                country=supplier_data.country,
                website=supplier_data.website,
                business_type=supplier_data.business_type.value,
                payment_terms=supplier_data.payment_terms,
                minimum_order_value=supplier_data.minimum_order_value,
                currency=supplier_data.currency,
                discount_tier=supplier_data.discount_tier.value,
                priority_level=supplier_data.priority_level,
                notes=supplier_data.notes,
                tags=supplier_data.tags,
                status="active",
                # Initialize performance metrics
                performance_rating=0.0,
                reliability_score=50,
                total_orders=0,
                successful_orders=0,
                average_delivery_days=15
            )
            
            self.db.add(db_supplier)
            self.db.commit()
            self.db.refresh(db_supplier)
            
            return db_supplier
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to create supplier: {str(e)}")
    
    def get_supplier(self, supplier_id: int) -> Optional[Supplier]:
        """Get supplier by ID"""
        return self.db.query(Supplier).filter(Supplier.id == supplier_id).first()
    
    def get_supplier_by_email(self, email: str) -> Optional[Supplier]:
        """Get supplier by email address"""
        return self.db.query(Supplier).filter(Supplier.email == email).first()
    
    def get_suppliers(
        self, 
        pagination: Optional[PaginationParams] = None,
        filters: Optional[FilterParams] = None,
        status: Optional[SupplierStatus] = None,
        business_type: Optional[SupplierBusinessType] = None,
        country: Optional[str] = None
    ) -> Tuple[List[Supplier], int]:
        """Get suppliers with filtering and pagination"""
        
        query = self.db.query(Supplier)
        
        # Apply filters
        if status:
            query = query.filter(Supplier.status == status.value)
        
        if business_type:
            query = query.filter(Supplier.business_type == business_type.value)
        
        if country:
            query = query.filter(Supplier.country == country)
        
        if filters:
            if filters.search:
                search_term = f"%{filters.search}%"
                query = query.filter(
                    or_(
                        Supplier.name.ilike(search_term),
                        Supplier.company_name.ilike(search_term),
                        Supplier.contact_person.ilike(search_term),
                        Supplier.email.ilike(search_term)
                    )
                )
            
            if filters.date_from:
                query = query.filter(Supplier.created_at >= filters.date_from)
            
            if filters.date_to:
                query = query.filter(Supplier.created_at <= filters.date_to)
        
        # Get total count for pagination
        total = query.count()
        
        # Apply sorting
        if pagination and pagination.sort_by:
            if pagination.sort_by == "name":
                order_col = Supplier.name
            elif pagination.sort_by == "performance":
                order_col = Supplier.performance_rating
            elif pagination.sort_by == "orders":
                order_col = Supplier.total_orders
            elif pagination.sort_by == "created":
                order_col = Supplier.created_at
            else:
                order_col = Supplier.name
            
            if pagination.sort_order == "desc":
                query = query.order_by(desc(order_col))
            else:
                query = query.order_by(asc(order_col))
        else:
            query = query.order_by(desc(Supplier.performance_rating), Supplier.name)
        
        # Apply pagination
        if pagination:
            offset = (pagination.page - 1) * pagination.size
            query = query.offset(offset).limit(pagination.size)
        
        suppliers = query.all()
        return suppliers, total
    
    def update_supplier(self, supplier_id: int, supplier_data: SupplierUpdate) -> Optional[Supplier]:
        """Update supplier information"""
        try:
            supplier = self.get_supplier(supplier_id)
            if not supplier:
                return None
            
            # Update fields
            update_data = supplier_data.dict(exclude_unset=True)
            
            # Handle enum conversions
            if "business_type" in update_data and update_data["business_type"]:
                update_data["business_type"] = update_data["business_type"].value
            if "status" in update_data and update_data["status"]:
                update_data["status"] = update_data["status"].value
            if "discount_tier" in update_data and update_data["discount_tier"]:
                update_data["discount_tier"] = update_data["discount_tier"].value
            
            for field, value in update_data.items():
                if hasattr(supplier, field):
                    setattr(supplier, field, value)
            
            supplier.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(supplier)
            
            return supplier
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update supplier: {str(e)}")
    
    def delete_supplier(self, supplier_id: int) -> bool:
        """Soft delete supplier (set status to inactive)"""
        try:
            supplier = self.get_supplier(supplier_id)
            if not supplier:
                return False
            
            # Check if supplier has active products
            active_products = self.db.query(Product).filter(
                and_(
                    or_(
                        Product.primary_supplier_id == supplier_id,
                        Product.backup_supplier_id == supplier_id
                    ),
                    Product.status == "active"
                )
            ).count()
            
            if active_products > 0:
                # Soft delete - set to inactive
                supplier.status = "inactive"
                supplier.updated_at = datetime.utcnow()
            else:
                # Hard delete if no active products
                self.db.delete(supplier)
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to delete supplier: {str(e)}")
    
    # ===========================================
    # PERFORMANCE TRACKING & ANALYTICS
    # ===========================================
    
    def update_supplier_performance(self, supplier_id: int) -> bool:
        """Recalculate and update supplier performance metrics"""
        try:
            supplier = self.get_supplier(supplier_id)
            if not supplier:
                return False
            
            # Get order statistics from order_items
            order_stats = self.db.query(
                func.count(OrderItem.id).label('total_orders'),
                func.count(
                    func.nullif(OrderItem.fulfillment_status == 'delivered', False)
                ).label('successful_orders'),
                func.avg(
                    func.julianday(OrderItem.delivered_date) - 
                    func.julianday(OrderItem.created_at)
                ).label('avg_delivery_days')
            ).filter(OrderItem.supplier_id == supplier_id).first()
            
            # Calculate performance metrics
            total_orders = order_stats.total_orders or 0
            successful_orders = order_stats.successful_orders or 0
            avg_delivery_days = int(order_stats.avg_delivery_days or 15)
            
            # Calculate success rate
            success_rate = (successful_orders / total_orders * 100) if total_orders > 0 else 0
            
            # Calculate reliability score (0-100)
            # Based on success rate, delivery speed, and order volume
            delivery_score = max(0, 100 - (avg_delivery_days - 7) * 5)  # Penalize slow delivery
            volume_score = min(100, total_orders * 2)  # Reward order volume
            reliability_score = int((success_rate + delivery_score + volume_score) / 3)
            
            # Calculate performance rating (0.0-5.0)
            performance_rating = round(reliability_score / 20, 2)  # Convert to 0-5 scale
            
            # Update supplier metrics
            supplier.total_orders = total_orders
            supplier.successful_orders = successful_orders
            supplier.average_delivery_days = avg_delivery_days
            supplier.reliability_score = reliability_score
            supplier.performance_rating = performance_rating
            supplier.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update supplier performance: {str(e)}")
    
    def get_supplier_performance_stats(self, supplier_id: int) -> Optional[SupplierPerformanceStats]:
        """Get detailed performance statistics for a supplier"""
        supplier = self.get_supplier(supplier_id)
        if not supplier:
            return None
        
        # Get revenue statistics
        revenue_stats = self.db.query(
            func.sum(OrderItem.total_price).label('total_revenue'),
            func.count(OrderItem.id).label('total_orders')
        ).filter(OrderItem.supplier_id == supplier_id).first()
        
        # Get quality metrics
        quality_stats = self.db.query(
            func.avg(SupplierProduct.quality_rating).label('avg_quality'),
            func.avg(OrderItem.customer_rating).label('avg_customer_rating')
        ).outerjoin(SupplierProduct, SupplierProduct.supplier_id == supplier_id)\
         .outerjoin(OrderItem, OrderItem.supplier_id == supplier_id).first()
        
        # Calculate cost efficiency (revenue per order)
        total_revenue = float(revenue_stats.total_revenue or 0)
        total_orders = revenue_stats.total_orders or 0
        cost_efficiency = total_revenue / total_orders if total_orders > 0 else 0
        
        return SupplierPerformanceStats(
            supplier_id=supplier.id,
            supplier_name=supplier.name,
            total_orders=supplier.total_orders,
            total_revenue=total_revenue,
            average_delivery_days=float(supplier.average_delivery_days),
            success_rate=float(supplier.successful_orders / supplier.total_orders * 100) if supplier.total_orders > 0 else 0.0,
            quality_rating=float(quality_stats.avg_quality or 0),
            cost_efficiency=cost_efficiency
        )
    
    def get_top_suppliers(self, limit: int = 10, metric: str = "performance") -> List[SupplierPerformanceStats]:
        """Get top performing suppliers based on specified metric"""
        
        if metric == "performance":
            order_by = desc(Supplier.performance_rating)
        elif metric == "orders":
            order_by = desc(Supplier.total_orders)
        elif metric == "reliability":
            order_by = desc(Supplier.reliability_score)
        else:
            order_by = desc(Supplier.performance_rating)
        
        suppliers = self.db.query(Supplier)\
            .filter(Supplier.status == "active")\
            .order_by(order_by)\
            .limit(limit)\
            .all()
        
        stats = []
        for supplier in suppliers:
            stat = self.get_supplier_performance_stats(supplier.id)
            if stat:
                stats.append(stat)
        
        return stats
    
    # ===========================================
    # BUSINESS INTELLIGENCE
    # ===========================================
    
    def get_supplier_analytics(self, date_from: Optional[datetime] = None, date_to: Optional[datetime] = None) -> Dict[str, Any]:
        """Get comprehensive supplier analytics"""
        
        if not date_from:
            date_from = datetime.utcnow() - timedelta(days=30)
        if not date_to:
            date_to = datetime.utcnow()
        
        # Supplier status distribution
        status_dist = self.db.query(
            Supplier.status,
            func.count(Supplier.id).label('count')
        ).group_by(Supplier.status).all()
        
        # Business type distribution
        business_type_dist = self.db.query(
            Supplier.business_type,
            func.count(Supplier.id).label('count')
        ).group_by(Supplier.business_type).all()
        
        # Country distribution
        country_dist = self.db.query(
            Supplier.country,
            func.count(Supplier.id).label('count')
        ).filter(Supplier.country.isnot(None))\
         .group_by(Supplier.country)\
         .order_by(desc(func.count(Supplier.id)))\
         .limit(10).all()
        
        # Performance metrics
        performance_stats = self.db.query(
            func.avg(Supplier.performance_rating).label('avg_performance'),
            func.avg(Supplier.reliability_score).label('avg_reliability'),
            func.avg(Supplier.average_delivery_days).label('avg_delivery'),
            func.count(Supplier.id).label('total_suppliers')
        ).filter(Supplier.status == "active").first()
        
        # Recent activity
        recent_orders = self.db.query(
            func.date(OrderItem.created_at).label('order_date'),
            func.count(OrderItem.id).label('orders'),
            func.sum(OrderItem.total_price).label('revenue')
        ).filter(
            and_(
                OrderItem.created_at >= date_from,
                OrderItem.created_at <= date_to,
                OrderItem.supplier_id.isnot(None)
            )
        ).group_by(func.date(OrderItem.created_at)).all()
        
        return {
            "status_distribution": [{"status": s.status, "count": s.count} for s in status_dist],
            "business_type_distribution": [{"type": bt.business_type, "count": bt.count} for bt in business_type_dist],
            "country_distribution": [{"country": c.country, "count": c.count} for c in country_dist],
            "performance_overview": {
                "total_suppliers": performance_stats.total_suppliers,
                "average_performance": float(performance_stats.avg_performance or 0),
                "average_reliability": float(performance_stats.avg_reliability or 0),
                "average_delivery_days": float(performance_stats.avg_delivery or 0)
            },
            "recent_activity": [
                {
                    "date": activity.order_date.strftime("%Y-%m-%d"),
                    "orders": activity.orders,
                    "revenue": float(activity.revenue or 0)
                }
                for activity in recent_orders
            ]
        }
    
    def update_contact_date(self, supplier_id: int, contact_date: Optional[datetime] = None) -> bool:
        """Update last contact date for supplier"""
        try:
            supplier = self.get_supplier(supplier_id)
            if not supplier:
                return False
            
            supplier.last_contact_date = contact_date or datetime.utcnow()
            supplier.updated_at = datetime.utcnow()
            
            self.db.commit()
            return True
            
        except Exception as e:
            self.db.rollback()
            raise Exception(f"Failed to update contact date: {str(e)}")
    
    def get_suppliers_by_performance_tier(self, tier: str) -> List[Supplier]:
        """Get suppliers by performance tier"""
        
        if tier == "excellent":
            min_rating = 4.0
        elif tier == "good":
            min_rating = 3.0
            max_rating = 4.0
        elif tier == "average":
            min_rating = 2.0
            max_rating = 3.0
        else:  # poor
            min_rating = 0.0
            max_rating = 2.0
        
        query = self.db.query(Supplier)\
            .filter(Supplier.status == "active")\
            .filter(Supplier.performance_rating >= min_rating)
        
        if tier != "excellent":
            query = query.filter(Supplier.performance_rating < max_rating)
        
        return query.order_by(desc(Supplier.performance_rating)).all()
    
    def bulk_update_performance(self) -> Dict[str, int]:
        """Update performance metrics for all active suppliers"""
        try:
            active_suppliers = self.db.query(Supplier)\
                .filter(Supplier.status == "active")\
                .all()
            
            updated = 0
            failed = 0
            
            for supplier in active_suppliers:
                try:
                    self.update_supplier_performance(supplier.id)
                    updated += 1
                except Exception:
                    failed += 1
                    continue
            
            return {
                "total": len(active_suppliers),
                "updated": updated,
                "failed": failed
            }
            
        except Exception as e:
            raise Exception(f"Failed to bulk update performance: {str(e)}")