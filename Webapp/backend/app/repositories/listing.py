"""
Listing Repository - Specialized CRUD operations cho Listing model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from app.repositories.base import CRUDBase
from app.models.database_models import Listing, ListingStatusEnum, Order
from app.schemas.schemas import ListingCreate, ListingUpdate


class ListingRepository(CRUDBase[Listing, ListingCreate, ListingUpdate]):
    """Listing repository với specialized methods"""

    def get_by_item_id(self, db: Session, *, item_id: str, user_id: int = None) -> Optional[Listing]:
        """Get listing by eBay item ID"""
        query = db.query(Listing).filter(Listing.item_id == item_id)
        if user_id is not None:
            query = query.filter(Listing.user_id == user_id)
        return query.first()

    def get_by_item_number(self, db: Session, *, item_number: str, user_id: int = None) -> Optional[Listing]:
        """Get listing by eBay item number (alias for item_id)"""
        return self.get_by_item_id(db, item_id=item_number, user_id=user_id)

    def get_by_sku(self, db: Session, *, sku: str, user_id: int) -> Optional[Listing]:
        """Get listing by SKU"""
        return db.query(Listing).filter(
            and_(Listing.sku == sku, Listing.user_id == user_id)
        ).first()

    def create_from_dict(self, db: Session, *, obj_in: Dict[str, Any]) -> Listing:
        """Create listing from dictionary"""
        db_obj = Listing(**obj_in)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_from_dict(self, db: Session, *, db_obj: Listing, obj_in: Dict[str, Any]) -> Listing:
        """Update listing from dictionary"""
        for field, value in obj_in.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def count_by_account(self, db: Session, *, account_id: int, user_id: int) -> int:
        """Count listings by account"""
        return db.query(Listing).filter(
            and_(Listing.account_id == account_id, Listing.user_id == user_id)
        ).count()

    def get_latest_by_account(self, db: Session, *, account_id: int, user_id: int) -> Optional[Listing]:
        """Get latest listing by account"""
        return db.query(Listing).filter(
            and_(Listing.account_id == account_id, Listing.user_id == user_id)
        ).order_by(desc(Listing.updated_at)).first()

    def get_by_status(
        self, 
        db: Session, 
        *, 
        status: ListingStatusEnum, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get listings by status"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"status": status},
            user_id=user_id,
            sort_by="updated_at",
            sort_order="desc"
        )

    def get_by_category(
        self, 
        db: Session, 
        *, 
        category: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get listings by category"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"category": category},
            user_id=user_id
        )

    def search_listings(
        self, 
        db: Session, 
        *, 
        search: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search listings by title, description, category"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            search_fields=["title", "description", "category", "sku"],
            user_id=user_id
        )

    def get_active_listings(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all active listings"""
        return self.get_by_status(db, status=ListingStatusEnum.ACTIVE, user_id=user_id, skip=skip, limit=limit)

    def get_draft_listings(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all draft listings"""
        return self.get_by_status(db, status=ListingStatusEnum.DRAFT, user_id=user_id, skip=skip, limit=limit)

    def get_optimized_listings(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all optimized listings"""
        return self.get_by_status(db, status=ListingStatusEnum.OPTIMIZED, user_id=user_id, skip=skip, limit=limit)

    def get_low_performance_listings(
        self, 
        db: Session, 
        *, 
        user_id: int,
        threshold: float = 50.0,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Listing]:
        """Get listings với performance score thấp"""
        return db.query(Listing).filter(
            and_(
                Listing.user_id == user_id,
                Listing.performance_score < threshold,
                Listing.status == ListingStatusEnum.ACTIVE
            )
        ).order_by(asc(Listing.performance_score)).offset(skip).limit(limit).all()

    def get_top_performing_listings(
        self, 
        db: Session, 
        *, 
        user_id: int,
        limit: int = 10
    ) -> List[Listing]:
        """Get top performing listings"""
        return db.query(Listing).filter(
            and_(
                Listing.user_id == user_id,
                Listing.status == ListingStatusEnum.ACTIVE,
                Listing.performance_score.isnot(None)
            )
        ).order_by(desc(Listing.performance_score)).limit(limit).all()

    def get_recent_listings(
        self, 
        db: Session, 
        *, 
        user_id: int,
        days: int = 7,
        limit: int = 10
    ) -> List[Listing]:
        """Get recently created listings"""
        cutoff_date = datetime.now() - timedelta(days=days)
        return db.query(Listing).filter(
            and_(
                Listing.user_id == user_id,
                Listing.created_at >= cutoff_date
            )
        ).order_by(desc(Listing.created_at)).limit(limit).all()

    def get_listings_with_orders(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> List[Listing]:
        """Get listings có orders"""
        return db.query(Listing).options(joinedload(Listing.orders)).filter(
            and_(
                Listing.user_id == user_id,
                Listing.orders.any()
            )
        ).offset(skip).limit(limit).all()

    def update_performance_score(self, db: Session, *, listing_id: str, score: float) -> Optional[Listing]:
        """Update performance score cho listing"""
        listing = self.get(db, id=listing_id)
        if listing:
            listing.performance_score = score
            db.add(listing)
            db.commit()
            db.refresh(listing)
        return listing

    def bulk_update_status(
        self, 
        db: Session, 
        *, 
        listing_ids: List[str], 
        status: ListingStatusEnum,
        user_id: int
    ) -> Dict[str, Any]:
        """Bulk update status for multiple listings"""
        updated = db.query(Listing).filter(
            and_(
                Listing.id.in_(listing_ids),
                Listing.user_id == user_id
            )
        ).update({"status": status}, synchronize_session=False)
        
        db.commit()
        
        return {
            "success": updated,
            "failed": len(listing_ids) - updated
        }

    def get_statistics(self, db: Session, *, user_id: int) -> Dict[str, Any]:
        """Get listing statistics for user"""
        stats = {}
        
        # Count by status
        for status in ListingStatusEnum:
            count = db.query(func.count(Listing.id)).filter(
                and_(Listing.user_id == user_id, Listing.status == status)
            ).scalar()
            stats[f"{status.value}_count"] = count
        
        # Total listings
        stats["total_listings"] = db.query(func.count(Listing.id)).filter(
            Listing.user_id == user_id
        ).scalar()
        
        # Average performance score
        avg_performance = db.query(func.avg(Listing.performance_score)).filter(
            and_(
                Listing.user_id == user_id,
                Listing.performance_score.isnot(None)
            )
        ).scalar()
        stats["avg_performance_score"] = float(avg_performance) if avg_performance else 0.0
        
        # Total views, watchers, sold
        totals = db.query(
            func.sum(Listing.views),
            func.sum(Listing.watchers),
            func.sum(Listing.sold)
        ).filter(Listing.user_id == user_id).first()
        
        stats["total_views"] = int(totals[0]) if totals[0] else 0
        stats["total_watchers"] = int(totals[1]) if totals[1] else 0
        stats["total_sold"] = int(totals[2]) if totals[2] else 0
        
        # Categories breakdown
        categories = db.query(
            Listing.category,
            func.count(Listing.id)
        ).filter(
            Listing.user_id == user_id
        ).group_by(Listing.category).all()
        
        stats["categories"] = {cat[0]: cat[1] for cat in categories if cat[0]}
        
        return stats

    def optimize_listing(
        self, 
        db: Session, 
        *, 
        listing_id: str,
        optimized_title: str,
        optimized_description: Optional[str] = None,
        keywords: Optional[List[str]] = None,
        seo_score: Optional[float] = None,
        notes: Optional[str] = None
    ) -> Optional[Listing]:
        """Update listing với optimization data"""
        listing = self.get(db, id=listing_id)
        if not listing:
            return None
        
        # Store original title if not already stored
        if not listing.original_title:
            listing.original_title = listing.title
        
        # Update với optimization data
        listing.optimized_title = optimized_title
        listing.title = optimized_title  # Update current title
        
        if optimized_description:
            listing.description = optimized_description
        
        if keywords:
            listing.keywords = keywords
        
        if seo_score is not None:
            listing.seo_score = seo_score
        
        if notes:
            listing.optimization_notes = notes
        
        listing.status = ListingStatusEnum.OPTIMIZED
        
        db.add(listing)
        db.commit()
        db.refresh(listing)
        
        return listing


# Create repository instance
listing_repo = ListingRepository(Listing)