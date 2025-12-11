from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request as GoogleRequest
from motor.motor_asyncio import AsyncIOMotorDatabase
from config import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

async def get_search_console_service(user_id: str, db: AsyncIOMotorDatabase):
    """Build an authenticated Search Console service"""
    users_collection = db.users
    user = await users_collection.find_one({"id": user_id}, {"_id": 0})
    
    if not user or not user.get("google_access_token"):
        raise ValueError("User not found or not authenticated with Google")
    
    # Create credentials from stored tokens
    credentials = Credentials(
        token=user["google_access_token"],
        refresh_token=user.get("google_refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret
    )
    
    # Refresh if expired
    if credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(GoogleRequest())
            
            # Update tokens in database
            await users_collection.update_one(
                {"id": user_id},
                {
                    "$set": {
                        "google_access_token": credentials.token,
                        "google_refresh_token": credentials.refresh_token,
                        "google_token_expiry": datetime.utcfromtimestamp(credentials.expiry.timestamp()) if credentials.expiry else None,
                        "updated_at": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Failed to refresh token: {e}")
            raise ValueError("Failed to refresh Google credentials")
    
    # Build Search Console service
    service = build("searchconsole", "v1", credentials=credentials)
    return service

async def get_verified_sites(user_id: str, db: AsyncIOMotorDatabase):
    """Get all verified sites from GSC"""
    service = await get_search_console_service(user_id, db)
    
    try:
        site_list = service.sites().list().execute()
        
        verified_sites = [
            {
                "url": site["siteUrl"],
                "type": "url-prefix" if site["siteUrl"].startswith("http") else "domain",
                "permission": site.get("permissionLevel", "unknown")
            }
            for site in site_list.get("siteEntry", [])
            if site.get("permissionLevel") != "siteUnverifiedUser"
        ]
        
        return verified_sites
    except Exception as e:
        logger.error(f"Failed to get verified sites: {e}")
        raise

async def query_search_analytics(user_id: str, db: AsyncIOMotorDatabase, site_url: str, start_date: str, end_date: str, dimensions: list = None):
    """Query search analytics data"""
    service = await get_search_console_service(user_id, db)
    
    if not dimensions:
        dimensions = ["page"]
    
    request_body = {
        "startDate": start_date,
        "endDate": end_date,
        "dimensions": dimensions,
        "rowLimit": 10000
    }
    
    try:
        response = service.searchanalytics().query(
            siteUrl=site_url,
            body=request_body
        ).execute()
        
        return response.get("rows", [])
    except Exception as e:
        logger.error(f"Search analytics query failed: {e}")
        raise

async def inspect_url(user_id: str, db: AsyncIOMotorDatabase, site_url: str, inspection_url: str):
    """Inspect a specific URL to check for 404s and indexing issues"""
    service = await get_search_console_service(user_id, db)
    
    request_body = {
        "inspectionUrl": inspection_url,
        "siteUrl": site_url
    }
    
    try:
        response = service.urlInspection().index().inspect(body=request_body).execute()
        inspection_result = response.get("inspectionResult", {})
        index_status = inspection_result.get("indexStatusResult", {})
        
        return {
            "url": inspection_url,
            "last_crawl_time": index_status.get("lastCrawlTime"),
            "coverage_state": index_status.get("coverageState"),
            "indexing_state": index_status.get("indexingState"),
            "page_fetch_state": index_status.get("pageFetchState"),
            "is_404": index_status.get("pageFetchState") == "NOT_FOUND"
        }
    except Exception as e:
        logger.error(f"URL inspection failed for {inspection_url}: {e}")
        return {"url": inspection_url, "error": str(e)}