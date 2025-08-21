"""
Draft Listing Repository
Handles database operations for draft_listings table
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc
from app.repositories.base import BaseRepository
from app.models.database_models import DraftListing, Account, SourceProduct


class DraftListingRepository(BaseRepository[DraftListing]):
    """Repository for DraftListing operations"""
    
    def __init__(self, db: Session):
        super().__init__(DraftListing, db)
    
    def get_by_account_id(self, account_id: int, skip: int = 0, limit: int = 100) -> List[DraftListing]:
        """Get draft listings by account ID"""
        return (
            self.db.query(DraftListing)
            .filter(DraftListing.account_id == account_id)
            .order_by(desc(DraftListing.created_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_source_product_id(self, source_product_id: str) -> List[DraftListing]:
        """Get all drafts for a source product (across all accounts)"""
        return (
            self.db.query(DraftListing)
            .filter(DraftListing.source_product_id == source_product_id)
            .order_by(asc(DraftListing.account_id))
            .all()
        )
    
    def get_by_status(self, status: str, account_id: Optional[int] = None) -> List[DraftListing]:
        """Get drafts by status, optionally filtered by account"""
        query = self.db.query(DraftListing).filter(DraftListing.status == status)
        
        if account_id:
            query = query.filter(DraftListing.account_id == account_id)
        
        return query.order_by(desc(DraftListing.updated_at)).all()
    
    def get_by_image_status(self, image_status: str, account_id: Optional[int] = None) -> List[DraftListing]:
        """Get drafts by image status"""
        query = self.db.query(DraftListing).filter(DraftListing.image_status == image_status)
        
        if account_id:
            query = query.filter(DraftListing.account_id == account_id)
        
        return query.order_by(desc(DraftListing.edit_date)).all()
    
    def get_ready_to_list(self, account_id: Optional[int] = None) -> List[DraftListing]:
        """Get drafts that are ready to list"""
        query = (
            self.db.query(DraftListing)
            .filter(
                and_(
                    DraftListing.status == 'ready',
                    DraftListing.image_status == 'approved'
                )
            )
        )
        
        if account_id:
            query = query.filter(DraftListing.account_id == account_id)
        
        return query.order_by(asc(DraftListing.scheduled_date)).all()
    
    def get_scheduled_drafts(self) -> List[DraftListing]:
        """Get drafts scheduled for listing"""
        return (
            self.db.query(DraftListing)
            .filter(
                and_(
                    DraftListing.status == 'scheduled',
                    DraftListing.scheduled_date.isnot(None)
                )
            )
            .order_by(asc(DraftListing.scheduled_date))
            .all()
        )
    
    def get_drafts_by_employee(self, edited_by: str) -> List[DraftListing]:
        """Get drafts edited by specific employee"""
        return (
            self.db.query(DraftListing)
            .filter(DraftListing.edited_by == edited_by)
            .order_by(desc(DraftListing.edit_date))
            .all()
        )
    
    def get_with_account_and_source(self, draft_id: str) -> Optional[DraftListing]:
        """Get draft with account and source product info"""
        return (
            self.db.query(DraftListing)
            .join(Account, DraftListing.account_id == Account.id)
            .outerjoin(SourceProduct, DraftListing.source_product_id == SourceProduct.id)
            .filter(DraftListing.id == draft_id)
            .first()
        )
    
    def search_drafts(self, 
                     query: str, 
                     account_id: Optional[int] = None,
                     status: Optional[str] = None,
                     skip: int = 0,
                     limit: int = 50) -> List[DraftListing]:
        """Search drafts by title or description"""
        search_filter = or_(
            DraftListing.title.contains(query),
            DraftListing.description.contains(query)
        )
        
        db_query = self.db.query(DraftListing).filter(search_filter)
        
        if account_id:
            db_query = db_query.filter(DraftListing.account_id == account_id)
        
        if status:
            db_query = db_query.filter(DraftListing.status == status)
        
        return (
            db_query
            .order_by(desc(DraftListing.updated_at))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def count_by_status(self, account_id: Optional[int] = None) -> Dict[str, int]:
        """Count drafts by status"""
        query = self.db.query(DraftListing.status, self.db.func.count(DraftListing.id))
        
        if account_id:
            query = query.filter(DraftListing.account_id == account_id)
        
        results = query.group_by(DraftListing.status).all()
        return {status: count for status, count in results}
    
    def count_by_image_status(self, account_id: Optional[int] = None) -> Dict[str, int]:
        """Count drafts by image status"""
        query = self.db.query(DraftListing.image_status, self.db.func.count(DraftListing.id))
        
        if account_id:
            query = query.filter(DraftListing.account_id == account_id)
        
        results = query.group_by(DraftListing.image_status).all()
        return {status: count for status, count in results}
    
    def update_image_status(self, draft_id: str, image_status: str, edited_by: str = None) -> Optional[DraftListing]:
        """Update image status of draft"""
        draft = self.get(draft_id)
        if draft:
            draft.image_status = image_status
            if edited_by:
                draft.edited_by = edited_by
                # Update edit_date if needed
                from datetime import datetime
                draft.edit_date = datetime.utcnow()
            self.db.commit()
            self.db.refresh(draft)
        return draft
    
    def bulk_update_status(self, draft_ids: List[str], status: str) -> int:
        """Bulk update status for multiple drafts"""
        updated = (
            self.db.query(DraftListing)
            .filter(DraftListing.id.in_(draft_ids))
            .update({DraftListing.status: status}, synchronize_session=False)
        )
        self.db.commit()
        return updated
    
    def get_analytics(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get draft analytics"""
        query = self.db.query(DraftListing)
        
        if account_id:
            query = query.filter(DraftListing.account_id == account_id)
        
        total = query.count()
        
        # Status breakdown
        status_counts = self.count_by_status(account_id)
        
        # Image status breakdown
        image_status_counts = self.count_by_image_status(account_id)
        
        # Average profit margin
        avg_profit = (
            query
            .filter(DraftListing.profit_margin.isnot(None))
            .with_entities(self.db.func.avg(DraftListing.profit_margin))
            .scalar() or 0
        )
        
        # Price range
        price_stats = (
            query
            .filter(DraftListing.price.isnot(None))
            .with_entities(
                self.db.func.min(DraftListing.price),
                self.db.func.max(DraftListing.price),
                self.db.func.avg(DraftListing.price)
            )
            .first()
        )
        
        return {
            'total_drafts': total,
            'status_breakdown': status_counts,
            'image_status_breakdown': image_status_counts,
            'average_profit_margin': float(avg_profit),
            'price_stats': {
                'min': float(price_stats[0]) if price_stats[0] else 0,
                'max': float(price_stats[1]) if price_stats[1] else 0,
                'avg': float(price_stats[2]) if price_stats[2] else 0
            }
        }