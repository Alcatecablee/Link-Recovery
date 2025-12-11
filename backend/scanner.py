from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timedelta
from gsc_service import query_search_analytics, inspect_url
from models import Error404, ScanLog, Backlink
import logging

logger = logging.getLogger(__name__)

async def scan_site_for_404s(user_id: str, site_id: str, site_url: str, db: AsyncIOMotorDatabase):
    """
    Scan a site for 404 errors using GSC data
    """
    # Create scan log
    scan_log = ScanLog(
        site_id=site_id,
        scan_type="manual",
        status="running"
    )
    
    scan_collection = db.scan_logs
    await scan_collection.insert_one(scan_log.model_dump())
    
    try:
        # Query search analytics for the last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Get all pages with data
        rows = await query_search_analytics(
            user_id,
            db,
            site_url,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
            dimensions=["page"]
        )
        
        errors_collection = db.errors_404
        backlinks_collection = db.backlinks
        
        errors_found = 0
        
        # Sample URLs to inspect (check up to 50 URLs with low clicks)
        urls_to_inspect = []
        for row in rows[:50]:  # Limit to avoid quota issues
            page_url = row["keys"][0]
            clicks = row.get("clicks", 0)
            impressions = row.get("impressions", 0)
            
            # Focus on pages with impressions but no clicks (potential 404s)
            if impressions > 0 and clicks == 0:
                urls_to_inspect.append({
                    "url": page_url,
                    "impressions": impressions,
                    "clicks": clicks
                })
        
        # Inspect each URL
        for item in urls_to_inspect[:20]:  # Further limit to 20 to stay within quota
            try:
                inspection = await inspect_url(user_id, db, site_url, item["url"])
                
                if inspection.get("is_404"):
                    # Check if error already exists
                    existing_error = await errors_collection.find_one(
                        {"site_id": site_id, "url": item["url"]},
                        {"_id": 0}
                    )
                    
                    if existing_error:
                        # Update existing error
                        await errors_collection.update_one(
                            {"id": existing_error["id"]},
                            {
                                "$set": {
                                    "last_checked": datetime.utcnow(),
                                    "impressions": item["impressions"],
                                    "clicks": item["clicks"]
                                }
                            }
                        )
                    else:
                        # Create new error record
                        error_404 = Error404(
                            site_id=site_id,
                            url=item["url"],
                            impressions=item["impressions"],
                            clicks=item["clicks"],
                            priority_score=min(item["impressions"], 100)  # Simple priority based on impressions
                        )
                        
                        await errors_collection.insert_one(error_404.model_dump())
                        errors_found += 1
                        
                        # Try to get backlinks from GSC (limited data)
                        # In production, you'd integrate with Ahrefs/SEMrush here
                        # For MVP, we'll simulate checking for internal backlinks
                        
            except Exception as e:
                logger.error(f"Failed to inspect URL {item['url']}: {e}")
                continue
        
        # Update scan log
        await scan_collection.update_one(
            {"id": scan_log.id},
            {
                "$set": {
                    "status": "completed",
                    "errors_found": errors_found,
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        return {
            "status": "completed",
            "errors_found": errors_found,
            "urls_inspected": len(urls_to_inspect)
        }
    
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        
        # Update scan log with error
        await scan_collection.update_one(
            {"id": scan_log.id},
            {
                "$set": {
                    "status": "failed",
                    "error_message": str(e),
                    "completed_at": datetime.utcnow()
                }
            }
        )
        
        raise