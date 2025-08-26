"""
Account Repository - Specialized CRUD operations cho Account model
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc, asc
from datetime import datetime, timedelta

from app.repositories.base import CRUDBase
from app.models.database_models import Account, AccountStatusEnum
from app.schemas.schemas import AccountCreate, AccountUpdate


class AccountRepository(CRUDBase[Account, AccountCreate, AccountUpdate]):
    """Account repository với specialized methods"""

    def get_by_username(self, db: Session, *, ebay_username: str, user_id: int) -> Optional[Account]:
        """Get account by eBay username"""
        return db.query(Account).filter(
            and_(Account.ebay_username == ebay_username, Account.user_id == user_id)
        ).first()

    def get_by_email(self, db: Session, *, email: str, user_id: int) -> Optional[Account]:
        """Get account by email"""
        return db.query(Account).filter(
            and_(Account.email == email, Account.user_id == user_id)
        ).first()

    def get_by_status(
        self, 
        db: Session, 
        *, 
        status: AccountStatusEnum, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get accounts by status"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"status": status},
            user_id=user_id,
            sort_by="last_activity",
            sort_order="desc"
        )

    def get_by_country(
        self, 
        db: Session, 
        *, 
        country: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Get accounts by country"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            filters={"country": country},
            user_id=user_id
        )

    def search_accounts(
        self, 
        db: Session, 
        *, 
        search: str, 
        user_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> Dict[str, Any]:
        """Search accounts by username, email, store_name"""
        return self.get_multi(
            db,
            skip=skip,
            limit=limit,
            search=search,
            search_fields=["ebay_username", "email", "store_name"],
            user_id=user_id
        )

    def get_active_accounts(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all active accounts"""
        return self.get_by_status(db, status=AccountStatusEnum.ACTIVE, user_id=user_id, skip=skip, limit=limit)

    def get_suspended_accounts(self, db: Session, *, user_id: int, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        """Get all suspended accounts"""
        return self.get_by_status(db, status=AccountStatusEnum.SUSPENDED, user_id=user_id, skip=skip, limit=limit)

    def get_high_health_accounts(
        self, 
        db: Session, 
        *, 
        user_id: int,
        min_health: float = 80.0,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Account]:
        """Get accounts với high health score"""
        return db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.health_score >= min_health,
                Account.status == AccountStatusEnum.ACTIVE
            )
        ).order_by(desc(Account.health_score)).offset(skip).limit(limit).all()

    def get_accounts_near_limits(
        self, 
        db: Session, 
        *, 
        user_id: int,
        threshold_percentage: float = 80.0
    ) -> List[Account]:
        """Get accounts gần đạt limits (listing hoặc revenue)"""
        return db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.status == AccountStatusEnum.ACTIVE,
                or_(
                    (Account.used_listing_count / Account.monthly_listing_limit) * 100 >= threshold_percentage,
                    (Account.used_revenue_amount / Account.monthly_revenue_limit) * 100 >= threshold_percentage
                )
            )
        ).all()

    def get_accounts_need_sync(
        self, 
        db: Session, 
        *, 
        user_id: int,
        hours_threshold: int = 6
    ) -> List[Account]:
        """Get accounts cần sync (last_sync > threshold)"""
        cutoff_time = datetime.now() - timedelta(hours=hours_threshold)
        return db.query(Account).filter(
            and_(
                Account.user_id == user_id,
                Account.auto_sync == True,
                Account.status == AccountStatusEnum.ACTIVE,
                or_(
                    Account.last_sync.is_(None),
                    Account.last_sync < cutoff_time
                )
            )
        ).all()

    def update_health_score(self, db: Session, *, account_id: int, health_score: float) -> Optional[Account]:
        """Update health score cho account"""
        account = self.get(db, id=account_id)
        if account:
            account.health_score = max(0.0, min(100.0, health_score))  # Clamp between 0-100
            account.last_activity = datetime.now()
            db.add(account)
            db.commit()
            db.refresh(account)
        return account

    def update_metrics(
        self, 
        db: Session, 
        *, 
        account_id: int,
        feedback_score: Optional[float] = None,
        feedback_count: Optional[int] = None,
        total_listings: Optional[int] = None,
        active_listings: Optional[int] = None,
        total_sales: Optional[int] = None,
        monthly_revenue: Optional[float] = None
    ) -> Optional[Account]:
        """Update account performance metrics"""
        account = self.get(db, id=account_id)
        if not account:
            return None
        
        if feedback_score is not None:
            account.feedback_score = feedback_score
        if feedback_count is not None:
            account.feedback_count = feedback_count
        if total_listings is not None:
            account.total_listings = total_listings
        if active_listings is not None:
            account.active_listings = active_listings
        if total_sales is not None:
            account.total_sales = total_sales
        if monthly_revenue is not None:
            account.monthly_revenue = monthly_revenue
        
        account.last_activity = datetime.now()
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account

    def update_usage(
        self, 
        db: Session, 
        *, 
        account_id: int,
        used_listing_count: Optional[int] = None,
        used_revenue_amount: Optional[float] = None
    ) -> Optional[Account]:
        """Update account usage statistics"""
        account = self.get(db, id=account_id)
        if not account:
            return None
        
        if used_listing_count is not None:
            account.used_listing_count = used_listing_count
        if used_revenue_amount is not None:
            account.used_revenue_amount = used_revenue_amount
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account

    def update_sync_status(
        self, 
        db: Session, 
        *, 
        account_id: int,
        last_sync: Optional[datetime] = None
    ) -> Optional[Account]:
        """Update last_sync time"""
        account = self.get(db, id=account_id)
        if not account:
            return None
        
        account.last_sync = last_sync or datetime.now()
        
        db.add(account)
        db.commit()
        db.refresh(account)
        
        return account

    def get_statistics(self, db: Session, *, user_id: int) -> Dict[str, Any]:
        """Get account statistics for user"""
        stats = {}
        
        # Count by status
        for status in AccountStatusEnum:
            count = db.query(func.count(Account.id)).filter(
                and_(Account.user_id == user_id, Account.status == status)
            ).scalar()
            stats[f"{status.value}_count"] = count
        
        # Total accounts
        stats["total_accounts"] = db.query(func.count(Account.id)).filter(
            Account.user_id == user_id
        ).scalar()
        
        # Aggregated performance metrics
        aggregates = db.query(
            func.avg(Account.health_score),
            func.avg(Account.feedback_score),
            func.sum(Account.total_listings),
            func.sum(Account.active_listings),
            func.sum(Account.total_sales),
            func.sum(Account.monthly_revenue)
        ).filter(Account.user_id == user_id).first()
        
        stats["avg_health_score"] = float(aggregates[0]) if aggregates[0] else 0.0
        stats["avg_feedback_score"] = float(aggregates[1]) if aggregates[1] else 0.0
        stats["total_listings"] = int(aggregates[2]) if aggregates[2] else 0
        stats["total_active_listings"] = int(aggregates[3]) if aggregates[3] else 0
        stats["total_sales"] = int(aggregates[4]) if aggregates[4] else 0
        stats["total_monthly_revenue"] = float(aggregates[5]) if aggregates[5] else 0.0
        
        # Usage statistics
        usage_stats = db.query(
            func.sum(Account.used_listing_count),
            func.sum(Account.used_revenue_amount),
            func.sum(Account.monthly_listing_limit),
            func.sum(Account.monthly_revenue_limit)
        ).filter(Account.user_id == user_id).first()
        
        stats["used_listings"] = int(usage_stats[0]) if usage_stats[0] else 0
        stats["used_revenue"] = float(usage_stats[1]) if usage_stats[1] else 0.0
        stats["total_listing_limit"] = int(usage_stats[2]) if usage_stats[2] else 0
        stats["total_revenue_limit"] = float(usage_stats[3]) if usage_stats[3] else 0.0
        
        # Calculate usage percentages
        if stats["total_listing_limit"] > 0:
            stats["listing_usage_percentage"] = (stats["used_listings"] / stats["total_listing_limit"]) * 100
        else:
            stats["listing_usage_percentage"] = 0.0
            
        if stats["total_revenue_limit"] > 0:
            stats["revenue_usage_percentage"] = (stats["used_revenue"] / stats["total_revenue_limit"]) * 100
        else:
            stats["revenue_usage_percentage"] = 0.0
        
        # Country distribution
        countries = db.query(
            Account.country,
            func.count(Account.id)
        ).filter(
            Account.user_id == user_id
        ).group_by(Account.country).all()
        
        stats["countries"] = {country[0]: country[1] for country in countries if country[0]}
        
        # Accounts needing attention
        stats["accounts_near_limits"] = len(self.get_accounts_near_limits(db, user_id=user_id))
        stats["accounts_need_sync"] = len(self.get_accounts_need_sync(db, user_id=user_id))
        
        return stats

    def bulk_sync(self, db: Session, *, account_ids: List[int], user_id: int) -> Dict[str, Any]:
        """Bulk sync multiple accounts"""
        updated = db.query(Account).filter(
            and_(
                Account.id.in_(account_ids),
                Account.user_id == user_id
            )
        ).update({
            "last_sync": datetime.now()
        }, synchronize_session=False)
        
        db.commit()
        
        return {
            "success": updated,
            "failed": len(account_ids) - updated
        }

    def calculate_health_score(
        self,
        feedback_score: float,
        feedback_count: int,
        listing_usage_percent: float,
        revenue_usage_percent: float,
        account_age_days: int
    ) -> float:
        """
        Calculate health score based on multiple factors
        Returns score 0-100
        """
        score = 0.0
        
        # Feedback score weight: 40%
        if feedback_score >= 99.0:
            score += 40.0
        elif feedback_score >= 95.0:
            score += 30.0
        elif feedback_score >= 90.0:
            score += 20.0
        else:
            score += 10.0
        
        # Feedback count weight: 20%
        if feedback_count >= 1000:
            score += 20.0
        elif feedback_count >= 500:
            score += 15.0
        elif feedback_count >= 100:
            score += 10.0
        else:
            score += 5.0
        
        # Usage efficiency weight: 25%
        avg_usage = (listing_usage_percent + revenue_usage_percent) / 2
        if avg_usage <= 60.0:
            score += 25.0
        elif avg_usage <= 80.0:
            score += 20.0
        elif avg_usage <= 95.0:
            score += 10.0
        else:
            score += 5.0  # Too close to limits
        
        # Account age weight: 15%
        if account_age_days >= 365 * 3:  # 3+ years
            score += 15.0
        elif account_age_days >= 365:  # 1+ year
            score += 10.0
        elif account_age_days >= 180:  # 6+ months
            score += 5.0
        else:
            score += 2.0
        
        return min(100.0, max(0.0, score))


# Create repository instance
account_repo = AccountRepository(Account)