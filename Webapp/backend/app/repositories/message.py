"""
Message Repository
Handles database operations for messages table
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc, asc, func
from app.repositories.base import BaseRepository
from app.models.database_models import Message, Account, Listing, Order
from datetime import datetime, timedelta


class MessageRepository(BaseRepository[Message]):
    """Repository for Message operations"""
    
    def __init__(self, db: Session):
        super().__init__(Message, db)
    
    def get_by_account_id(self, account_id: int, skip: int = 0, limit: int = 100) -> List[Message]:
        """Get messages by account ID"""
        return (
            self.db.query(Message)
            .filter(Message.account_id == account_id)
            .order_by(desc(Message.message_date))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_by_listing_id(self, listing_id: str) -> List[Message]:
        """Get messages related to a specific listing"""
        return (
            self.db.query(Message)
            .filter(Message.listing_id == listing_id)
            .order_by(desc(Message.message_date))
            .all()
        )
    
    def get_by_order_id(self, order_id: str) -> List[Message]:
        """Get messages related to a specific order"""
        return (
            self.db.query(Message)
            .filter(Message.order_id == order_id)
            .order_by(desc(Message.message_date))
            .all()
        )
    
    def get_by_priority(self, priority: str, account_id: Optional[int] = None) -> List[Message]:
        """Get messages by priority level"""
        query = self.db.query(Message).filter(Message.priority == priority)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.message_date)).all()
    
    def get_unread_messages(self, account_id: Optional[int] = None) -> List[Message]:
        """Get unread messages"""
        query = self.db.query(Message).filter(Message.is_read == False)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.message_date)).all()
    
    def get_unreplied_messages(self, account_id: Optional[int] = None) -> List[Message]:
        """Get messages that need replies"""
        query = (
            self.db.query(Message)
            .filter(
                and_(
                    Message.is_replied == False,
                    Message.direction == 'inbound'
                )
            )
        )
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.message_date)).all()
    
    def get_overdue_messages(self, account_id: Optional[int] = None) -> List[Message]:
        """Get messages past their reply deadline"""
        current_time = datetime.utcnow()
        
        query = (
            self.db.query(Message)
            .filter(
                and_(
                    Message.reply_by_date < current_time,
                    Message.is_replied == False,
                    Message.direction == 'inbound'
                )
            )
        )
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.reply_by_date)).all()
    
    def get_by_message_type(self, message_type: str, account_id: Optional[int] = None) -> List[Message]:
        """Get messages by type"""
        query = self.db.query(Message).filter(Message.message_type == message_type)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.message_date)).all()
    
    def get_by_sender(self, sender_username: str, account_id: Optional[int] = None) -> List[Message]:
        """Get messages from specific sender"""
        query = self.db.query(Message).filter(Message.sender_username == sender_username)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.message_date)).all()
    
    def search_messages(self, 
                       query: str, 
                       account_id: Optional[int] = None,
                       message_type: Optional[str] = None,
                       skip: int = 0,
                       limit: int = 50) -> List[Message]:
        """Search messages by subject or message text"""
        search_filter = or_(
            Message.subject.contains(query),
            Message.message_text.contains(query),
            Message.sender_username.contains(query)
        )
        
        db_query = self.db.query(Message).filter(search_filter)
        
        if account_id:
            db_query = db_query.filter(Message.account_id == account_id)
        
        if message_type:
            db_query = db_query.filter(Message.message_type == message_type)
        
        return (
            db_query
            .order_by(desc(Message.message_date))
            .offset(skip)
            .limit(limit)
            .all()
        )
    
    def get_recent_messages(self, days: int = 7, account_id: Optional[int] = None) -> List[Message]:
        """Get messages from last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.db.query(Message).filter(Message.message_date >= cutoff_date)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        return query.order_by(desc(Message.message_date)).all()
    
    def mark_as_read(self, message_id: str) -> Optional[Message]:
        """Mark message as read"""
        message = self.get(message_id)
        if message:
            message.is_read = True
            message.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(message)
        return message
    
    def mark_as_replied(self, message_id: str) -> Optional[Message]:
        """Mark message as replied"""
        message = self.get(message_id)
        if message:
            message.is_replied = True
            message.updated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(message)
        return message
    
    def bulk_mark_read(self, message_ids: List[str]) -> int:
        """Bulk mark messages as read"""
        updated = (
            self.db.query(Message)
            .filter(Message.id.in_(message_ids))
            .update({Message.is_read: True, Message.updated_at: datetime.utcnow()}, synchronize_session=False)
        )
        self.db.commit()
        return updated
    
    def bulk_update_priority(self, message_ids: List[str], priority: str) -> int:
        """Bulk update priority for multiple messages"""
        updated = (
            self.db.query(Message)
            .filter(Message.id.in_(message_ids))
            .update({Message.priority: priority, Message.updated_at: datetime.utcnow()}, synchronize_session=False)
        )
        self.db.commit()
        return updated
    
    def count_by_status(self, account_id: Optional[int] = None) -> Dict[str, int]:
        """Count messages by read/replied status"""
        query = self.db.query(Message)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        total = query.count()
        unread = query.filter(Message.is_read == False).count()
        unreplied = query.filter(
            and_(Message.is_replied == False, Message.direction == 'inbound')
        ).count()
        
        return {
            'total': total,
            'unread': unread,
            'unreplied': unreplied,
            'read': total - unread
        }
    
    def count_by_priority(self, account_id: Optional[int] = None) -> Dict[str, int]:
        """Count messages by priority"""
        query = self.db.query(Message.priority, func.count(Message.id))
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        results = query.group_by(Message.priority).all()
        return {priority: count for priority, count in results}
    
    def count_by_type(self, account_id: Optional[int] = None) -> Dict[str, int]:
        """Count messages by type"""
        query = self.db.query(Message.message_type, func.count(Message.id))
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        results = query.group_by(Message.message_type).all()
        return {msg_type: count for msg_type, count in results}
    
    def get_analytics(self, account_id: Optional[int] = None) -> Dict[str, Any]:
        """Get message analytics"""
        query = self.db.query(Message)
        
        if account_id:
            query = query.filter(Message.account_id == account_id)
        
        # Basic counts
        status_counts = self.count_by_status(account_id)
        priority_counts = self.count_by_priority(account_id)
        type_counts = self.count_by_type(account_id)
        
        # Recent activity (last 7 days)
        recent_messages = self.get_recent_messages(7, account_id)
        
        # Average response time for replied messages
        avg_response_time_query = (
            query
            .filter(
                and_(
                    Message.is_replied == True,
                    Message.message_date.isnot(None),
                    Message.updated_at.isnot(None)
                )
            )
        )
        
        # Count overdue messages
        overdue_count = len(self.get_overdue_messages(account_id))
        
        return {
            'status_breakdown': status_counts,
            'priority_breakdown': priority_counts,
            'type_breakdown': type_counts,
            'recent_activity': {
                'last_7_days': len(recent_messages)
            },
            'overdue_messages': overdue_count,
            'response_rate': {
                'replied': status_counts.get('total', 0) - status_counts.get('unreplied', 0),
                'total_inbound': query.filter(Message.direction == 'inbound').count()
            }
        }
    
    def get_with_relations(self, message_id: str) -> Optional[Message]:
        """Get message with account, listing, and order info"""
        return (
            self.db.query(Message)
            .join(Account, Message.account_id == Account.id)
            .outerjoin(Listing, Message.listing_id == Listing.id)
            .outerjoin(Order, Message.order_id == Order.id)
            .filter(Message.id == message_id)
            .first()
        )