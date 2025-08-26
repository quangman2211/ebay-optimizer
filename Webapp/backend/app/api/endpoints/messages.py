"""
Messages API Endpoints
Handles operations for eBay messages management
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.core.deps import get_db, get_current_active_user
from app.repositories.message import MessageRepository
from app.repositories.account import AccountRepository
from app.models.database_models import User, Message
from app.schemas.schemas import APIResponse
from datetime import datetime
from pydantic import BaseModel

router = APIRouter()

# Pydantic models for request/response
class MessageCreate(BaseModel):
    account_id: int
    listing_id: Optional[str] = None
    order_id: Optional[str] = None
    ebay_message_id: Optional[str] = None
    message_type: str = "general"
    subject: Optional[str] = None
    message_text: Optional[str] = None
    sender_username: Optional[str] = None
    recipient_username: Optional[str] = None
    direction: str  # inbound, outbound
    priority: str = "normal"
    message_date: Optional[datetime] = None
    reply_by_date: Optional[datetime] = None

class MessageUpdate(BaseModel):
    subject: Optional[str] = None
    message_text: Optional[str] = None
    priority: Optional[str] = None
    is_read: Optional[bool] = None
    is_replied: Optional[bool] = None
    reply_by_date: Optional[datetime] = None

class BulkReadUpdate(BaseModel):
    message_ids: List[str]

class BulkPriorityUpdate(BaseModel):
    message_ids: List[str]
    priority: str


@router.get("/", response_model=APIResponse)
async def get_messages(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    priority: Optional[str] = Query(None, description="Filter by priority"),
    is_read: Optional[bool] = Query(None, description="Filter by read status"),
    is_replied: Optional[bool] = Query(None, description="Filter by replied status"),
    direction: Optional[str] = Query(None, description="Filter by direction (inbound/outbound)"),
    search: Optional[str] = Query(None, description="Search in subject/content/sender"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages with filtering and pagination"""
    repo = MessageRepository(db)
    
    try:
        if search:
            messages = repo.search_messages(
                query=search,
                account_id=account_id,
                message_type=message_type,
                skip=skip,
                limit=limit
            )
        elif priority:
            messages = repo.get_by_priority(priority, account_id)
            messages = messages[skip:skip+limit]  # Manual pagination
        elif message_type:
            messages = repo.get_by_message_type(message_type, account_id)
            messages = messages[skip:skip+limit]
        elif account_id:
            messages = repo.get_by_account_id(account_id, skip, limit)
        else:
            messages = repo.get_all(skip=skip, limit=limit)
        
        # Apply additional filters
        if is_read is not None:
            messages = [m for m in messages if m.is_read == is_read]
        
        if is_replied is not None:
            messages = [m for m in messages if m.is_replied == is_replied]
            
        if direction:
            messages = [m for m in messages if m.direction == direction]
        
        # Convert to dict for response
        messages_data = []
        for message in messages:
            message_dict = {
                'id': message.id,
                'account_id': message.account_id,
                'listing_id': message.listing_id,
                'order_id': message.order_id,
                'ebay_message_id': message.ebay_message_id,
                'message_type': message.message_type,
                'subject': message.subject,
                'message_text': message.message_text,
                'sender_username': message.sender_username,
                'recipient_username': message.recipient_username,
                'direction': message.direction,
                'is_read': message.is_read,
                'is_replied': message.is_replied,
                'priority': message.priority,
                'message_date': message.message_date.isoformat() if message.message_date else None,
                'reply_by_date': message.reply_by_date.isoformat() if message.reply_by_date else None,
                'created_at': message.created_at.isoformat() if message.created_at else None,
                'updated_at': message.updated_at.isoformat() if message.updated_at else None
            }
            messages_data.append(message_dict)
        
        return APIResponse(
            success=True,
            message=f"Found {len(messages_data)} messages",
            data=messages_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching messages: {str(e)}"
        )


@router.post("/", response_model=APIResponse)
async def create_message(
    message_data: MessageCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Create a new message"""
    repo = MessageRepository(db)
    account_repo = AccountRepository(db)
    
    try:
        # Verify account exists and belongs to user
        account = account_repo.get(message_data.account_id)
        if not account or account.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account not found or access denied"
            )
        
        # Generate unique message ID
        import uuid
        message_id = f"MSG_{uuid.uuid4().hex[:8].upper()}"
        
        # Create message
        message = Message(
            id=message_id,
            user_id=current_user.id,
            account_id=message_data.account_id,
            listing_id=message_data.listing_id,
            order_id=message_data.order_id,
            ebay_message_id=message_data.ebay_message_id,
            message_type=message_data.message_type,
            subject=message_data.subject,
            message_text=message_data.message_text,
            sender_username=message_data.sender_username,
            recipient_username=message_data.recipient_username,
            direction=message_data.direction,
            priority=message_data.priority,
            message_date=message_data.message_date or datetime.utcnow(),
            reply_by_date=message_data.reply_by_date,
            is_read=False,
            is_replied=False,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        created_message = repo.create(message)
        
        return APIResponse(
            success=True,
            message="Message created successfully",
            data={
                'id': created_message.id,
                'account_id': created_message.account_id,
                'subject': created_message.subject,
                'message_type': created_message.message_type,
                'priority': created_message.priority,
                'direction': created_message.direction
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error creating message: {str(e)}"
        )


@router.get("/{message_id}", response_model=APIResponse)
async def get_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get a specific message"""
    repo = MessageRepository(db)
    
    try:
        message = repo.get_with_relations(message_id)
        if not message or message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        message_data = {
            'id': message.id,
            'account_id': message.account_id,
            'listing_id': message.listing_id,
            'order_id': message.order_id,
            'ebay_message_id': message.ebay_message_id,
            'message_type': message.message_type,
            'subject': message.subject,
            'message_text': message.message_text,
            'sender_username': message.sender_username,
            'recipient_username': message.recipient_username,
            'direction': message.direction,
            'is_read': message.is_read,
            'is_replied': message.is_replied,
            'priority': message.priority,
            'message_date': message.message_date.isoformat() if message.message_date else None,
            'reply_by_date': message.reply_by_date.isoformat() if message.reply_by_date else None,
            'created_at': message.created_at.isoformat() if message.created_at else None,
            'updated_at': message.updated_at.isoformat() if message.updated_at else None
        }
        
        return APIResponse(
            success=True,
            message="Message retrieved successfully",
            data=message_data
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching message: {str(e)}"
        )


@router.put("/{message_id}", response_model=APIResponse)
async def update_message(
    message_id: str,
    message_data: MessageUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update a message"""
    repo = MessageRepository(db)
    
    try:
        message = repo.get(message_id)
        if not message or message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Update fields
        update_data = message_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(message, field):
                setattr(message, field, value)
        
        message.updated_at = datetime.utcnow()
        
        updated_message = repo.update(message)
        
        return APIResponse(
            success=True,
            message="Message updated successfully",
            data={
                'id': updated_message.id,
                'is_read': updated_message.is_read,
                'is_replied': updated_message.is_replied,
                'priority': updated_message.priority,
                'updated_at': updated_message.updated_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error updating message: {str(e)}"
        )


@router.delete("/{message_id}", response_model=APIResponse)
async def delete_message(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a message"""
    repo = MessageRepository(db)
    
    try:
        message = repo.get(message_id)
        if not message or message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        repo.delete(message_id)
        
        return APIResponse(
            success=True,
            message="Message deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error deleting message: {str(e)}"
        )


@router.patch("/{message_id}/read", response_model=APIResponse)
async def mark_message_read(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark message as read"""
    repo = MessageRepository(db)
    
    try:
        message = repo.get(message_id)
        if not message or message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        updated_message = repo.mark_as_read(message_id)
        
        return APIResponse(
            success=True,
            message="Message marked as read",
            data={
                'id': updated_message.id,
                'is_read': updated_message.is_read,
                'updated_at': updated_message.updated_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error marking message as read: {str(e)}"
        )


@router.patch("/{message_id}/replied", response_model=APIResponse)
async def mark_message_replied(
    message_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Mark message as replied"""
    repo = MessageRepository(db)
    
    try:
        message = repo.get(message_id)
        if not message or message.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        updated_message = repo.mark_as_replied(message_id)
        
        return APIResponse(
            success=True,
            message="Message marked as replied",
            data={
                'id': updated_message.id,
                'is_replied': updated_message.is_replied,
                'updated_at': updated_message.updated_at.isoformat()
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error marking message as replied: {str(e)}"
        )


@router.patch("/bulk-read", response_model=APIResponse)
async def bulk_mark_read(
    read_data: BulkReadUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk mark messages as read"""
    repo = MessageRepository(db)
    
    try:
        updated_count = repo.bulk_mark_read(read_data.message_ids)
        
        return APIResponse(
            success=True,
            message=f"Marked {updated_count} messages as read",
            data={'updated_count': updated_count}
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error bulk marking messages as read: {str(e)}"
        )


@router.patch("/bulk-priority", response_model=APIResponse)
async def bulk_update_priority(
    priority_data: BulkPriorityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Bulk update priority for messages"""
    repo = MessageRepository(db)
    
    try:
        updated_count = repo.bulk_update_priority(priority_data.message_ids, priority_data.priority)
        
        return APIResponse(
            success=True,
            message=f"Updated priority for {updated_count} messages",
            data={'updated_count': updated_count, 'new_priority': priority_data.priority}
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error bulk updating message priority: {str(e)}"
        )


@router.get("/unread/count", response_model=APIResponse)
async def get_unread_count(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get count of unread messages"""
    repo = MessageRepository(db)
    
    try:
        unread_messages = repo.get_unread_messages(account_id)
        
        return APIResponse(
            success=True,
            message="Unread count retrieved",
            data={'unread_count': len(unread_messages)}
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error getting unread count: {str(e)}"
        )


@router.get("/unreplied/list", response_model=APIResponse)
async def get_unreplied_messages(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get messages that need replies"""
    repo = MessageRepository(db)
    
    try:
        unreplied_messages = repo.get_unreplied_messages(account_id)
        
        messages_data = []
        for message in unreplied_messages:
            messages_data.append({
                'id': message.id,
                'account_id': message.account_id,
                'subject': message.subject,
                'sender_username': message.sender_username,
                'priority': message.priority,
                'message_date': message.message_date.isoformat() if message.message_date else None,
                'reply_by_date': message.reply_by_date.isoformat() if message.reply_by_date else None
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(messages_data)} messages needing replies",
            data=messages_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error getting unreplied messages: {str(e)}"
        )


@router.get("/overdue/list", response_model=APIResponse)
async def get_overdue_messages(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get overdue messages past reply deadline"""
    repo = MessageRepository(db)
    
    try:
        overdue_messages = repo.get_overdue_messages(account_id)
        
        messages_data = []
        for message in overdue_messages:
            messages_data.append({
                'id': message.id,
                'account_id': message.account_id,
                'subject': message.subject,
                'sender_username': message.sender_username,
                'priority': message.priority,
                'message_date': message.message_date.isoformat() if message.message_date else None,
                'reply_by_date': message.reply_by_date.isoformat() if message.reply_by_date else None
            })
        
        return APIResponse(
            success=True,
            message=f"Found {len(messages_data)} overdue messages",
            data=messages_data
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error getting overdue messages: {str(e)}"
        )


@router.get("/analytics", response_model=APIResponse)
async def get_message_analytics(
    account_id: Optional[int] = Query(None, description="Filter by account ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get message analytics"""
    repo = MessageRepository(db)
    
    try:
        analytics = repo.get_analytics(account_id)
        
        return APIResponse(
            success=True,
            message="Message analytics retrieved successfully",
            data=analytics
        )
    
    except Exception as e:
        return APIResponse(
            success=False,
            message=f"Error fetching message analytics: {str(e)}"
        )