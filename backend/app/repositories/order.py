"""
Order Repository - Specialized CRUD operations cho Order model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, between
from datetime import datetime, timedelta

from app.repositories.base import CRUDBase
from app.models.database_models import Order, OrderStatusEnum, Listing
from app.schemas.schemas import OrderCreate, OrderUpdate


class OrderRepository(CRUDBase[Order, OrderCreate, OrderUpdate]):
    """Order repository với specialized methods"""

    def get_by_order_number(self, db: Session, *, order_number: str, user_id: int) -> Optional[Order]:
        """Get order by order number"""
        return db.query(Order).filter(
            and_(Order.order_number == order_number, Order.user_id == user_id)
        ).first()

    def get_by_tracking_number(self, db: Session, *, tracking_number: str, user_id: int) -> Optional[Order]:
        """Get order by tracking number"""
        return db.query(Order).filter(
            and_(Order.tracking_number == tracking_number, Order.user_id == user_id)
        ).first()

    def get_by_status(
        self, 
        db: Session, 
        *, 
        status: OrderStatusEnum, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get orders by status"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"status": status},
            user_id=user_id,
            sort_by="order_date",
            sort_order="desc"
        )

    def get_by_customer(
        self, 
        db: Session, 
        *, 
        customer_email: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get orders by customer email"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"customer_email": customer_email},
            user_id=user_id
        )

    def search_orders(
        self, 
        db: Session, 
        *, 
        search: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search orders by order number, customer name, product name"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            search_fields=["order_number", "customer_name", "customer_email", "product_name"],
            user_id=user_id
        )

    def get_pending_orders(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all pending orders"""
        return self.get_by_status(db, status=OrderStatusEnum.PENDING, user_id=user_id, skip=skip, limit=limit)

    def get_processing_orders(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all processing orders"""
        return self.get_by_status(db, status=OrderStatusEnum.PROCESSING, user_id=user_id, skip=skip, limit=limit)

    def get_shipped_orders(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all shipped orders"""
        return self.get_by_status(db, status=OrderStatusEnum.SHIPPED, user_id=user_id, skip=skip, limit=limit)

    def get_overdue_orders(
        self, 
        db: Session, 
        *, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Get orders quá hạn ship date"""
        today = datetime.now().date()
        return db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.status.in_([OrderStatusEnum.PENDING, OrderStatusEnum.PROCESSING]),
                Order.expected_ship_date < today
            )
        ).order_by(asc(Order.expected_ship_date)).offset(skip).limit(limit).all()

    def get_orders_by_date_range(
        self, 
        db: Session, 
        *, 
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Get orders trong khoảng thời gian"""
        return db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                between(Order.order_date, start_date, end_date)
            )
        ).order_by(desc(Order.order_date)).offset(skip).limit(limit).all()

    def get_recent_orders(
        self, 
        db: Session, 
        *, 
        user_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[Order]:
        """Get recent orders"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.order_date >= cutoff_date
            )
        ).order_by(desc(Order.order_date)).limit(limit).all()

    def get_high_value_orders(
        self, 
        db: Session, 
        *, 
        user_id: int,
        min_value: float = 100.0,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Order]:
        """Get high value orders"""
        return db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.price_ebay >= min_value
            )
        ).order_by(desc(Order.price_ebay)).offset(skip).limit(limit).all()

    def get_orders_with_alerts(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Order]:
        """Get orders có alerts"""
        return db.query(Order).filter(
            and_(
                Order.user_id == user_id,
                Order.alerts.isnot(None),
                func.json_array_length(Order.alerts) > 0
            )
        ).order_by(desc(Order.order_date)).offset(skip).limit(limit).all()

    def update_tracking(
        self, 
        db: Session, 
        *, 
        order_id: str,
        tracking_number: str,
        carrier: str,
        ship_date: Optional[datetime] = None
    ) -> Optional[Order]:
        """Update tracking information"""
        order = self.get(db, id=order_id)
        if not order:
            return None
        
        order.tracking_number = tracking_number
        order.carrier = carrier
        order.actual_ship_date = ship_date or datetime.now()
        
        # Update status to shipped if not already
        if order.status in [OrderStatusEnum.PENDING, OrderStatusEnum.PROCESSING]:
            order.status = OrderStatusEnum.SHIPPED
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return order

    def add_alert(self, db: Session, *, order_id: str, alert_message: str) -> Optional[Order]:
        """Add alert message to order"""
        order = self.get(db, id=order_id)
        if not order:
            return None
        
        if not order.alerts:
            order.alerts = []
        
        if alert_message not in order.alerts:
            order.alerts.append(alert_message)
            db.add(order)
            db.commit()
            db.refresh(order)
        
        return order

    def remove_alert(self, db: Session, *, order_id: str, alert_message: str) -> Optional[Order]:
        """Remove alert message from order"""
        order = self.get(db, id=order_id)
        if not order or not order.alerts:
            return order
        
        if alert_message in order.alerts:
            order.alerts.remove(alert_message)
            db.add(order)
            db.commit()
            db.refresh(order)
        
        return order

    def bulk_update_status(
        self, 
        db: Session, 
        *, 
        order_ids: List[str], 
        status: OrderStatusEnum,
        user_id: int
    ) -> Dict[str, Any]:
        """Bulk update status for multiple orders"""
        updated = db.query(Order).filter(
            and_(
                Order.id.in_(order_ids),
                Order.user_id == user_id
            )
        ).update({"status": status}, synchronize_session=False)
        
        db.commit()
        
        return {
            "success": updated,
            "failed": len(order_ids) - updated
        }

    def get_statistics(self, db: Session, *, user_id: int) -> Dict[str, Any]:
        """Get order statistics for user"""
        stats = {}
        
        # Count by status
        for status in OrderStatusEnum:
            count = db.query(func.count(Order.id)).filter(
                and_(Order.user_id == user_id, Order.status == status)
            ).scalar()
            stats[f"{status.value}_count"] = count
        
        # Total orders
        stats["total_orders"] = db.query(func.count(Order.id)).filter(
            Order.user_id == user_id
        ).scalar()
        
        # Revenue calculations
        revenue_data = db.query(
            func.sum(Order.price_ebay),
            func.sum(Order.net_profit),
            func.sum(Order.ebay_fees),
            func.avg(Order.price_ebay)
        ).filter(Order.user_id == user_id).first()
        
        stats["total_revenue"] = float(revenue_data[0]) if revenue_data[0] else 0.0
        stats["total_profit"] = float(revenue_data[1]) if revenue_data[1] else 0.0
        stats["total_fees"] = float(revenue_data[2]) if revenue_data[2] else 0.0
        stats["avg_order_value"] = float(revenue_data[3]) if revenue_data[3] else 0.0
        
        # Monthly revenue (current month)
        current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = db.query(func.sum(Order.price_ebay)).filter(
            and_(
                Order.user_id == user_id,
                Order.order_date >= current_month_start
            )
        ).scalar()
        stats["monthly_revenue"] = float(monthly_revenue) if monthly_revenue else 0.0
        
        # Orders with tracking
        tracking_count = db.query(func.count(Order.id)).filter(
            and_(
                Order.user_id == user_id,
                Order.tracking_number.isnot(None),
                Order.tracking_number != ""
            )
        ).scalar()
        stats["orders_with_tracking"] = tracking_count
        
        # Customer types breakdown (simplified - grouping by customer name patterns)
        stats["customer_types"] = {"all": stats["total_orders"]}
        
        return stats

    def get_revenue_by_period(
        self, 
        db: Session, 
        *, 
        user_id: int,
        period_days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily revenue for specified period"""
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=period_days)
        
        # Query daily revenue
        daily_revenue = db.query(
            func.date(Order.order_date).label('date'),
            func.sum(Order.price_ebay).label('revenue'),
            func.count(Order.id).label('order_count')
        ).filter(
            and_(
                Order.user_id == user_id,
                func.date(Order.order_date) >= start_date,
                func.date(Order.order_date) <= end_date
            )
        ).group_by(func.date(Order.order_date)).order_by(func.date(Order.order_date)).all()
        
        return [
            {
                "date": str(row.date),
                "revenue": float(row.revenue) if row.revenue else 0.0,
                "order_count": row.order_count
            }
            for row in daily_revenue
        ]


# Create repository instance
order_repo = OrderRepository(Order)