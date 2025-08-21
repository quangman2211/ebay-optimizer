from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


class ListingStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    OPTIMIZED = "optimized"
    ARCHIVED = "archived"


class ListingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=4000)
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    keywords: Optional[List[str]] = []
    item_specifics: Optional[Dict[str, str]] = {}
    

class ListingCreate(ListingBase):
    pass


class ListingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=80)
    description: Optional[str] = Field(None, max_length=4000)
    category: Optional[str] = None
    price: Optional[float] = Field(None, gt=0)
    quantity: Optional[int] = Field(None, ge=0)
    keywords: Optional[List[str]] = None
    item_specifics: Optional[Dict[str, str]] = None
    status: Optional[ListingStatus] = None


class Listing(ListingBase):
    id: str
    status: ListingStatus = ListingStatus.DRAFT
    created_at: datetime
    updated_at: datetime
    sheet_row: Optional[int] = None
    
    class Config:
        from_attributes = True


class OptimizationRequest(BaseModel):
    title: str
    description: Optional[str] = None
    category: str
    keywords: Optional[List[str]] = []
    item_specifics: Optional[Dict[str, str]] = {}


class OptimizationResponse(BaseModel):
    original_title: str
    optimized_title: str
    title_score: float
    original_description: Optional[str] = None
    optimized_description: Optional[str] = None
    suggested_keywords: List[str]
    improvements: List[str]
    seo_score: float


class BulkOptimizationRequest(BaseModel):
    listing_ids: List[str]
    optimize_title: bool = True
    optimize_description: bool = True
    generate_keywords: bool = True


class BulkOptimizationResponse(BaseModel):
    total: int
    successful: int
    failed: int
    results: List[OptimizationResponse]
    errors: Optional[List[Dict[str, str]]] = []