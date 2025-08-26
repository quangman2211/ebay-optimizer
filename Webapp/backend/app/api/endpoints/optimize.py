from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from enum import Enum

from app.schemas.schemas import (
    OptimizationRequest, OptimizationResponse,
    BulkOptimizationRequest, BulkOptimizationResponse,
    ListingStatus
)
# Temporarily commented out to fix imports
# from app.core.optimizer import EbayOptimizer
# from app.core.strategies.optimization_strategies import OptimizationType
# from app.core.strategies.export_strategies import ExportFormat
# from app.services.sheets_management import GoogleSheetsService

router = APIRouter()
# optimizer = EbayOptimizer()
# sheets_service = GoogleSheetsService()


class StrategyResponse(dict):
    """Response model for strategy information"""
    pass


@router.post("/title", response_model=OptimizationResponse)
async def optimize_title(
    request: OptimizationRequest,
    strategy_type: Optional[OptimizationType] = Query(OptimizationType.BASIC, description="Optimization strategy to use")
):
    """
    Optimize a single listing title
    """
    try:
        # Optimize title using strategy pattern
        optimized_title, title_score = optimizer.optimize_title(
            title=request.title,
            category=request.category,
            keywords=request.keywords,
            item_specifics=request.item_specifics,
            strategy_type=strategy_type
        )
        
        # Generate keywords using strategy pattern
        suggested_keywords = optimizer.generate_keywords(
            title=request.title,
            description=request.description or "",
            category=request.category,
            strategy_type=strategy_type
        )
        
        # Optimize description if provided using strategy pattern
        optimized_description = None
        if request.description:
            optimized_description = optimizer.optimize_description(
                title=optimized_title,
                description=request.description,
                category=request.category,
                item_specifics=request.item_specifics,
                keywords=suggested_keywords,
                strategy_type=strategy_type
            )
        
        # Calculate overall SEO score
        seo_score = title_score
        if optimized_description:
            # Add description contribution to score
            desc_length = len(optimized_description)
            if 500 <= desc_length <= 2000:
                seo_score = min(seo_score + 10, 100)
        
        # Generate improvements list
        improvements = []
        if len(request.title) < 40:
            improvements.append("Title is too short. Add more descriptive keywords.")
        if len(request.title) > 80:
            improvements.append("Title exceeds 80 characters. Consider shortening.")
        if not any(word in request.title.lower() for word in optimizer.power_words):
            improvements.append("Add power words like 'new', 'authentic', 'genuine' for better visibility.")
        if request.category and not any(kw in request.title.lower() for kw in suggested_keywords[:5]):
            improvements.append("Include category-specific keywords in the title.")
        
        return OptimizationResponse(
            original_title=request.title,
            optimized_title=optimized_title,
            title_score=title_score,
            original_description=request.description,
            optimized_description=optimized_description,
            suggested_keywords=suggested_keywords,
            improvements=improvements,
            seo_score=seo_score
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing title: {str(e)}")


@router.post("/description")
async def optimize_description(
    request: OptimizationRequest,
    strategy_type: Optional[OptimizationType] = Query(OptimizationType.BASIC, description="Optimization strategy to use")
):
    """
    Generate optimized description for a listing
    """
    try:
        # Generate keywords first for better description optimization
        keywords = optimizer.generate_keywords(
            title=request.title,
            description=request.description or "",
            category=request.category,
            strategy_type=strategy_type
        )
        
        optimized_description = optimizer.optimize_description(
            title=request.title,
            description=request.description or "",
            category=request.category,
            item_specifics=request.item_specifics,
            keywords=keywords,
            strategy_type=strategy_type
        )
        
        return {
            "original_description": request.description,
            "optimized_description": optimized_description,
            "character_count": len(optimized_description)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing description: {str(e)}")


@router.post("/keywords")
async def generate_keywords(
    request: OptimizationRequest,
    strategy_type: Optional[OptimizationType] = Query(OptimizationType.BASIC, description="Optimization strategy to use")
):
    """
    Generate relevant keywords for a listing
    """
    try:
        keywords = optimizer.generate_keywords(
            title=request.title,
            description=request.description or "",
            category=request.category,
            strategy_type=strategy_type
        )
        
        return {
            "keywords": keywords,
            "count": len(keywords)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")


@router.post("/bulk", response_model=BulkOptimizationResponse)
async def bulk_optimize(request: Dict[str, Any]):
    """
    Optimize multiple listings at once
    """
    try:
        # Handle both direct listings array and listing_ids
        if "listings" in request:
            # Direct listings provided in request
            listings_to_optimize = request["listings"]
        elif "listing_ids" in request:
            # Get listings from sheets by IDs
            all_listings = sheets_service.get_all_listings()
            listings_to_optimize = [
                l for l in all_listings 
                if l.get('id') in request["listing_ids"]
            ]
        else:
            raise HTTPException(status_code=422, detail="Request must contain either 'listings' array or 'listing_ids' array")
        
        if not listings_to_optimize:
            raise HTTPException(status_code=404, detail="No listings found with provided IDs")
        
        results = []
        errors = []
        updates_for_sheets = []
        
        # Get optimization settings from request
        optimize_title = request.get("optimize_title", True)
        optimize_description = request.get("optimize_description", True) 
        generate_keywords = request.get("generate_keywords", True)
        
        for listing in listings_to_optimize:
            try:
                # Prepare optimization request
                opt_request = OptimizationRequest(
                    title=listing.get('title', ''),
                    description=listing.get('description'),
                    category=listing.get('category', 'general'),
                    keywords=listing.get('keywords', []),
                    item_specifics=listing.get('item_specifics', {})
                )
                
                # Optimize title using strategy pattern
                optimized_title = listing.get('title', '')
                title_score = 0
                if optimize_title:
                    optimized_title, title_score = optimizer.optimize_title(
                        title=opt_request.title,
                        category=opt_request.category,
                        keywords=opt_request.keywords,
                        item_specifics=opt_request.item_specifics,
                        strategy_type=OptimizationType.BASIC  # Default strategy for bulk
                    )
                
                # Optimize description using strategy pattern
                optimized_description = listing.get('description')
                if optimize_description and opt_request.description:
                    optimized_description = optimizer.optimize_description(
                        title=optimized_title,
                        description=opt_request.description,
                        category=opt_request.category,
                        item_specifics=opt_request.item_specifics,
                        keywords=opt_request.keywords,
                        strategy_type=OptimizationType.BASIC  # Default strategy for bulk
                    )
                
                # Generate keywords using strategy pattern
                suggested_keywords = listing.get('keywords', [])
                if generate_keywords:
                    suggested_keywords = optimizer.generate_keywords(
                        title=optimized_title,
                        description=optimized_description or "",
                        category=opt_request.category,
                        strategy_type=OptimizationType.BASIC  # Default strategy for bulk
                    )
                
                # Calculate SEO score
                seo_score = title_score
                if optimized_description:
                    desc_length = len(optimized_description)
                    if 500 <= desc_length <= 2000:
                        seo_score = min(seo_score + 10, 100)
                
                # Add to results
                results.append(OptimizationResponse(
                    original_title=opt_request.title,
                    optimized_title=optimized_title,
                    title_score=title_score,
                    original_description=opt_request.description,
                    optimized_description=optimized_description,
                    suggested_keywords=suggested_keywords,
                    improvements=[],
                    seo_score=seo_score
                ))
                
                # Prepare update for sheets
                listing_update = listing.copy()
                listing_update['title'] = optimized_title
                if optimized_description:
                    listing_update['description'] = optimized_description
                listing_update['keywords'] = suggested_keywords
                listing_update['status'] = ListingStatus.OPTIMIZED
                updates_for_sheets.append(listing_update)
                
            except Exception as e:
                errors.append({
                    "listing_id": listing.get('id'),
                    "error": str(e)
                })
        
        # Batch update sheets
        if updates_for_sheets:
            sheets_result = sheets_service.batch_update_listings(updates_for_sheets)
        
        # Calculate total based on input type
        total_count = len(request.get("listing_ids", [])) if "listing_ids" in request else len(request.get("listings", []))
        
        return BulkOptimizationResponse(
            total=total_count,
            successful=len(results),
            failed=len(errors),
            results=results,
            errors=errors if errors else None
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in bulk optimization: {str(e)}")


@router.post("/analyze/{listing_id}")
async def analyze_listing(listing_id: str):
    """
    Analyze a listing and provide optimization suggestions
    """
    try:
        # Get listing
        all_listings = sheets_service.get_all_listings()
        listing = next((l for l in all_listings if l.get('id') == listing_id), None)
        
        if not listing:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        title = listing.get('title', '')
        description = listing.get('description', '')
        category = listing.get('category', 'general')
        
        # Analyze title
        title_issues = []
        title_length = len(title)
        
        if title_length < 40:
            title_issues.append({
                "issue": "Title too short",
                "suggestion": "Add more descriptive keywords to reach 60-80 characters"
            })
        elif title_length > 80:
            title_issues.append({
                "issue": "Title too long",
                "suggestion": "Shorten to under 80 characters"
            })
        
        if title.isupper():
            title_issues.append({
                "issue": "All caps title",
                "suggestion": "Use proper capitalization for better readability"
            })
        
        # Check for power words
        has_power_words = any(word in title.lower() for word in optimizer.power_words)
        if not has_power_words:
            title_issues.append({
                "issue": "Missing power words",
                "suggestion": "Add words like 'new', 'authentic', 'genuine' for better visibility"
            })
        
        # Analyze description
        desc_issues = []
        if description:
            desc_length = len(description)
            if desc_length < 200:
                desc_issues.append({
                    "issue": "Description too short",
                    "suggestion": "Add more details about the product"
                })
            elif desc_length > 3000:
                desc_issues.append({
                    "issue": "Description too long",
                    "suggestion": "Consider condensing to under 3000 characters"
                })
            
            if not any(char in description for char in ['•', '-', '*']):
                desc_issues.append({
                    "issue": "No bullet points",
                    "suggestion": "Use bullet points for better readability"
                })
        else:
            desc_issues.append({
                "issue": "No description",
                "suggestion": "Add a detailed product description"
            })
        
        # Generate suggestions
        keywords = optimizer.generate_keywords(title, description or "", category)
        
        return {
            "listing_id": listing_id,
            "current_status": listing.get('status'),
            "title_analysis": {
                "length": title_length,
                "issues": title_issues,
                "has_power_words": has_power_words
            },
            "description_analysis": {
                "length": len(description) if description else 0,
                "issues": desc_issues
            },
            "suggested_keywords": keywords[:10],
            "optimization_potential": "high" if (title_issues or desc_issues) else "low"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error analyzing listing: {str(e)}")


@router.get("/strategies")
async def get_optimization_strategies():
    """
    Get available optimization strategies
    """
    try:
        strategies = optimizer.get_available_optimization_strategies()
        return {
            "strategies": strategies,
            "default": OptimizationType.BASIC.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting strategies: {str(e)}")


@router.get("/export-formats")
async def get_export_formats():
    """
    Get available export formats
    """
    try:
        formats = optimizer.get_available_export_formats()
        return {
            "formats": formats,
            "default": ExportFormat.CSV.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting export formats: {str(e)}")


@router.post("/listing/complete")
async def optimize_complete_listing(
    request: OptimizationRequest,
    strategy_type: Optional[OptimizationType] = Query(OptimizationType.BASIC, description="Optimization strategy to use")
):
    """
    Optimize complete listing using strategy pattern
    """
    try:
        # Prepare listing data for strategy pattern
        listing_data = {
            "title": request.title,
            "description": request.description or "",
            "category": request.category,
            "keywords": request.keywords or []
        }
        
        # Optimize using strategy pattern
        result = optimizer.optimize_listing(listing_data, strategy_type)
        
        return {
            "optimization_result": result,
            "strategy_used": result["strategy_used"],
            "strategy_type": result["strategy_type"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing complete listing: {str(e)}")


@router.post("/export")
async def export_listings(
    listing_ids: List[str],
    export_format: Optional[ExportFormat] = Query(ExportFormat.CSV, description="Export format to use"),
    filename: Optional[str] = Query(None, description="Custom filename")
):
    """
    Export listings using strategy pattern
    """
    try:
        # Get listings data
        all_listings = sheets_service.get_all_listings()
        listings_to_export = [
            listing for listing in all_listings
            if listing.get('id') in listing_ids
        ]
        
        if not listings_to_export:
            raise HTTPException(status_code=404, detail="No listings found with provided IDs")
        
        # Export using strategy pattern
        export_result = optimizer.export_data(
            data=listings_to_export,
            export_format=export_format,
            filename=filename
        )
        
        return {
            "export_result": export_result,
            "download_info": {
                "filename": export_result["filename"],
                "content_type": export_result["content_type"],
                "record_count": export_result["record_count"],
                "format_name": export_result["format_name"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error exporting listings: {str(e)}")