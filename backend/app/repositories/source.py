"""
Source Repository - Specialized CRUD operations cho Source model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from app.repositories.base import CRUDBase
from app.models.database_models import Source, SourceProduct, SourceStatusEnum
from app.schemas.schemas import SourceCreate, SourceUpdate


class SourceRepository(CRUDBase[Source, SourceCreate, SourceUpdate]):
    """Source repository với specialized methods"""

    def get_by_name(self, db: Session, *, name: str, user_id: int) -> Optional[Source]:
        """Get source by name"""
        return db.query(Source).filter(
            and_(Source.name == name, Source.user_id == user_id)
        ).first()

    def get_by_status(
        self, 
        db: Session, 
        *, 
        status: SourceStatusEnum, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get sources by status"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"status": status},
            user_id=user_id,
            sort_by="last_sync",
            sort_order="desc"
        )

    def search_sources(
        self, 
        db: Session, 
        *, 
        search: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search sources by name, website_url"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            search_fields=["name", "website_url"],
            user_id=user_id
        )

    def get_connected_sources(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all connected sources"""
        return self.get_by_status(db, status=SourceStatusEnum.CONNECTED, user_id=user_id, skip=skip, limit=limit)

    def get_sources_with_products(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Source]:
        """Get sources có products"""
        return db.query(Source).options(joinedload(Source.products)).filter(
            and_(
                Source.user_id == user_id,
                Source.products.any()
            )
        ).offset(skip).limit(limit).all()

    def get_high_roi_sources(
        self, 
        db: Session, 
        *, 
        user_id: int,
        min_roi: float = 20.0,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Source]:
        """Get sources với high ROI"""
        return db.query(Source).filter(
            and_(
                Source.user_id == user_id,
                Source.average_roi >= min_roi,
                Source.status == SourceStatusEnum.CONNECTED
            )
        ).order_by(desc(Source.average_roi)).offset(skip).limit(limit).all()

    def get_sources_need_sync(
        self, 
        db: Session, 
        *, 
        user_id: int,
        hours_threshold: int = 24
    ) -> List[Source]:
        """Get sources cần sync (last_sync > threshold)"""
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        return db.query(Source).filter(
            and_(
                Source.user_id == user_id,
                Source.auto_sync == True,
                Source.status == SourceStatusEnum.CONNECTED,
                or_(
                    Source.last_sync.is_(None),
                    Source.last_sync < cutoff_time
                )
            )
        ).all()

    def update_sync_status(
        self, 
        db: Session, 
        *, 
        source_id: str,
        status: SourceStatusEnum,
        last_sync: Optional[datetime] = None
    ) -> Optional[Source]:
        """Update sync status và last_sync time"""
        source = self.get(db, id=source_id)
        if not source:
            return None
        
        source.status = status
        if last_sync:
            source.last_sync = last_sync
        elif status == SourceStatusEnum.CONNECTED:
            source.last_sync = datetime.now()
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        return source

    def update_statistics(
        self, 
        db: Session, 
        *, 
        source_id: str,
        total_products: Optional[int] = None,
        active_products: Optional[int] = None,
        total_revenue: Optional[float] = None,
        average_roi: Optional[float] = None
    ) -> Optional[Source]:
        """Update source statistics"""
        source = self.get(db, id=source_id)
        if not source:
            return None
        
        if total_products is not None:
            source.total_products = total_products
        if active_products is not None:
            source.active_products = active_products
        if total_revenue is not None:
            source.total_revenue = total_revenue
        if average_roi is not None:
            source.average_roi = average_roi
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        return source

    def get_statistics(self, db: Session, *, user_id: int) -> Dict[str, Any]:
        """Get source statistics for user"""
        stats = {}
        
        # Count by status
        for status in SourceStatusEnum:
            count = db.query(func.count(Source.id)).filter(
                and_(Source.user_id == user_id, Source.status == status)
            ).scalar()
            stats[f"{status.value}_count"] = count
        
        # Total sources
        stats["total_sources"] = db.query(func.count(Source.id)).filter(
            Source.user_id == user_id
        ).scalar()
        
        # Aggregated statistics
        aggregates = db.query(
            func.sum(Source.total_products),
            func.sum(Source.active_products),
            func.sum(Source.total_revenue),
            func.avg(Source.average_roi)
        ).filter(Source.user_id == user_id).first()
        
        stats["total_products"] = int(aggregates[0]) if aggregates[0] else 0
        stats["total_active_products"] = int(aggregates[1]) if aggregates[1] else 0
        stats["total_revenue"] = float(aggregates[2]) if aggregates[2] else 0.0
        stats["avg_roi"] = float(aggregates[3]) if aggregates[3] else 0.0
        
        # Sources needing sync
        sources_need_sync = len(self.get_sources_need_sync(db, user_id=user_id))
        stats["sources_need_sync"] = sources_need_sync
        
        # Top performing sources
        top_sources = db.query(Source.name, Source.average_roi).filter(
            and_(
                Source.user_id == user_id,
                Source.average_roi.isnot(None)
            )
        ).order_by(desc(Source.average_roi)).limit(5).all()
        
        stats["top_sources"] = [
            {"name": source[0], "roi": float(source[1])}
            for source in top_sources
        ]
        
        return stats

    def bulk_sync(self, db: Session, *, source_ids: List[str], user_id: int) -> Dict[str, Any]:
        """Bulk sync multiple sources"""
        updated = db.query(Source).filter(
            and_(
                Source.id.in_(source_ids),
                Source.user_id == user_id
            )
        ).update({
            "status": SourceStatusEnum.SYNCING,
            "last_sync": datetime.now()
        }, synchronize_session=False)
        
        db.commit()
        
        return {
            "success": updated,
            "failed": len(source_ids) - updated
        }

    def get_product_count(self, db: Session, *, source_id: str) -> int:
        """Get product count for source"""
        return db.query(func.count(SourceProduct.id)).filter(
            SourceProduct.source_id == source_id
        ).scalar()

    def calculate_roi(self, db: Session, *, source_id: str) -> Optional[float]:
        """Calculate average ROI for source based on products"""
        avg_roi = db.query(func.avg(SourceProduct.roi)).filter(
            and_(
                SourceProduct.source_id == source_id,
                SourceProduct.roi.isnot(None)
            )
        ).scalar()
        
        return float(avg_roi) if avg_roi else None

    def update_auto_calculated_stats(self, db: Session, *, source_id: str) -> Optional[Source]:
        """Update statistics based on actual product data"""
        source = self.get(db, id=source_id)
        if not source:
            return None
        
        # Calculate from actual products
        total_products = self.get_product_count(db, source_id=source_id)
        active_products = db.query(func.count(SourceProduct.id)).filter(
            and_(
                SourceProduct.source_id == source_id,
                SourceProduct.in_stock == True
            )
        ).scalar()
        
        average_roi = self.calculate_roi(db, source_id=source_id)
        
        # Update source
        source.total_products = total_products
        source.active_products = active_products
        if average_roi is not None:
            source.average_roi = average_roi
        
        db.add(source)
        db.commit()
        db.refresh(source)
        
        return source


# Create repository instance
source_repo = SourceRepository(Source)