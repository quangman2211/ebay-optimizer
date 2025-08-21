from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any

from app.models.listing import (
    OptimizationRequest, OptimizationResponse,
    BulkOptimizationRequest, BulkOptimizationResponse,
    ListingStatus
)
from app.core.optimizer import EbayOptimizer
from app.services.google_sheets import GoogleSheetsService

router = APIRouter()
optimizer = EbayOptimizer()
sheets_service = GoogleSheetsService()


@router.post("/title", response_model=OptimizationResponse)
async def optimize_title(request: OptimizationRequest):
    """
    Optimize a single listing title
    """
    try:
        # Optimize title
        optimized_title, title_score = optimizer.optimize_title(
            title=request.title,
            category=request.category,
            keywords=request.keywords,
            item_specifics=request.item_specifics
        )
        
        # Generate keywords
        suggested_keywords = optimizer.generate_keywords(
            title=request.title,
            description=request.description or "",
            category=request.category
        )
        
        # Optimize description if provided
        optimized_description = None
        if request.description:
            optimized_description = optimizer.optimize_description(
                title=optimized_title,
                description=request.description,
                category=request.category,
                item_specifics=request.item_specifics
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
async def optimize_description(request: OptimizationRequest):
    """
    Generate optimized description for a listing
    """
    try:
        optimized_description = optimizer.optimize_description(
            title=request.title,
            description=request.description or "",
            category=request.category,
            item_specifics=request.item_specifics
        )
        
        return {
            "original_description": request.description,
            "optimized_description": optimized_description,
            "character_count": len(optimized_description)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing description: {str(e)}")


@router.post("/keywords")
async def generate_keywords(request: OptimizationRequest):
    """
    Generate relevant keywords for a listing
    """
    try:
        keywords = optimizer.generate_keywords(
            title=request.title,
            description=request.description or "",
            category=request.category
        )
        
        return {
            "keywords": keywords,
            "count": len(keywords)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating keywords: {str(e)}")


@router.post("/bulk", response_model=BulkOptimizationResponse)
async def bulk_optimize(request: BulkOptimizationRequest):
    """
    Optimize multiple listings at once
    """
    try:
        # Get all listings
        all_listings = sheets_service.get_all_listings()
        
        # Filter listings to optimize
        listings_to_optimize = [
            l for l in all_listings 
            if l.get('id') in request.listing_ids
        ]
        
        if not listings_to_optimize:
            raise HTTPException(status_code=404, detail="No listings found with provided IDs")
        
        results = []
        errors = []
        updates_for_sheets = []
        
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
                
                # Optimize title
                optimized_title = listing.get('title', '')
                title_score = 0
                if request.optimize_title:
                    optimized_title, title_score = optimizer.optimize_title(
                        title=opt_request.title,
                        category=opt_request.category,
                        keywords=opt_request.keywords,
                        item_specifics=opt_request.item_specifics
                    )
                
                # Optimize description
                optimized_description = listing.get('description')
                if request.optimize_description and opt_request.description:
                    optimized_description = optimizer.optimize_description(
                        title=optimized_title,
                        description=opt_request.description,
                        category=opt_request.category,
                        item_specifics=opt_request.item_specifics
                    )
                
                # Generate keywords
                suggested_keywords = listing.get('keywords', [])
                if request.generate_keywords:
                    suggested_keywords = optimizer.generate_keywords(
                        title=optimized_title,
                        description=optimized_description or "",
                        category=opt_request.category
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
        
        return BulkOptimizationResponse(
            total=len(request.listing_ids),
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