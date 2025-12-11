from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional

# Import local modules
from config import settings
from models import (
    Site, SiteCreate, Error404, Error404Update, Recommendation,
    ScanLog, User, ScanTrigger
)
from auth_handler import create_access_token, get_current_user
from gsc_service import get_verified_sites, query_search_analytics
from ai_service import generate_redirect_recommendation, generate_content_suggestion
from scanner import scan_site_for_404s

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MongoDB connection
ROOT_DIR = Path(__file__).parent

# Database manager
class MongoDBManager:
    client: AsyncIOMotorClient = None
    database: AsyncIOMotorDatabase = None

    async def connect(self):
        self.client = AsyncIOMotorClient(settings.mongo_url)
        self.database = self.client[settings.db_name]
        await self.database.command("ping")
        logger.info("Connected to MongoDB")

    async def close(self):
        if self.client:
            self.client.close()
            logger.info("Disconnected from MongoDB")

    async def get_database(self) -> AsyncIOMotorDatabase:
        return self.database

db_manager = MongoDBManager()

@asynccontextmanager
async def lifespan(app: FastAPI):
    await db_manager.connect()
    yield
    await db_manager.close()

# Create FastAPI app
app = FastAPI(lifespan=lifespan, title="404 Recovery & Backlink Retention Tool")

# Create API router
api_router = APIRouter(prefix="/api")

# Dependency for database
async def get_db() -> AsyncIOMotorDatabase:
    return await db_manager.get_database()

# ============ AUTH ROUTES ============

@api_router.get("/auth/status")
async def auth_status(request: Request, db: AsyncIOMotorDatabase = Depends(get_db)):
    """Check if user is authenticated"""
    try:
        current_user = await get_current_user(request)
        user_data = await db.users.find_one({"id": current_user["sub"]}, {"_id": 0})
        
        return {
            "authenticated": True,
            "user": {
                "id": user_data["id"],
                "email": user_data["email"]
            }
        }
    except:
        return {"authenticated": False}

@api_router.get("/auth/google")
async def login_google():
    """Initiate Google OAuth flow - For MVP, we'll use a simulated flow"""
    # In production, implement full OAuth with Google
    # For MVP testing without OAuth setup, return instruction
    return {
        "message": "For MVP: Please add GSC credentials manually",
        "oauth_url": "/api/auth/google/callback"
    }

@api_router.post("/auth/demo-login")
async def demo_login(db: AsyncIOMotorDatabase = Depends(get_db)):
    """Create a demo user for MVP testing (no OAuth required)"""
    demo_user = User(
        email="demo@linkrecovery.com",
        google_id="demo_user"
    )
    
    # Check if demo user exists
    existing = await db.users.find_one({"email": demo_user.email}, {"_id": 0})
    
    if not existing:
        await db.users.insert_one(demo_user.model_dump())
        user_id = demo_user.id
    else:
        user_id = existing["id"]
    
    # Create JWT token
    access_token = create_access_token({"sub": user_id, "email": demo_user.email})
    
    response = Response(content='{"message": "Logged in as demo user"}', media_type="application/json")
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=30 * 60
    )
    
    return response

@api_router.post("/auth/logout")
async def logout():
    """Logout user"""
    response = Response(content='{"message": "Logged out"}', media_type="application/json")
    response.delete_cookie("access_token")
    return response

# ============ SITES ROUTES ============

@api_router.get("/sites")
async def list_sites(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all connected sites"""
    current_user = await get_current_user(request)
    
    sites = await db.sites.find(
        {"user_id": current_user["sub"]},
        {"_id": 0}
    ).to_list(100)
    
    return {"sites": sites}

@api_router.post("/sites")
async def create_site(
    site_data: SiteCreate,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Add a new site to monitor"""
    current_user = await get_current_user(request)
    
    # Check if site already exists
    existing = await db.sites.find_one(
        {"user_id": current_user["sub"], "site_url": site_data.site_url},
        {"_id": 0}
    )
    
    if existing:
        raise HTTPException(status_code=400, detail="Site already exists")
    
    site = Site(
        user_id=current_user["sub"],
        site_url=site_data.site_url,
        permission_level="owner"
    )
    
    await db.sites.insert_one(site.model_dump())
    
    return {"message": "Site added successfully", "site": site}

@api_router.post("/sites/{site_id}/scan")
async def trigger_scan(
    site_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Trigger a 404 scan for a site"""
    current_user = await get_current_user(request)
    
    # Get site
    site = await db.sites.find_one(
        {"id": site_id, "user_id": current_user["sub"]},
        {"_id": 0}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    # For MVP without OAuth, create sample 404 errors
    # In production, this would call scan_site_for_404s
    sample_errors = [
        Error404(
            site_id=site_id,
            url=f"{site['site_url']}/old-product-page",
            backlink_count=5,
            priority_score=75,
            impressions=150,
            clicks=0
        ),
        Error404(
            site_id=site_id,
            url=f"{site['site_url']}/deleted-blog-post",
            backlink_count=12,
            priority_score=90,
            impressions=450,
            clicks=0
        ),
        Error404(
            site_id=site_id,
            url=f"{site['site_url']}/missing-category",
            backlink_count=3,
            priority_score=60,
            impressions=80,
            clicks=0
        )
    ]
    
    # Insert sample errors
    errors_inserted = 0
    for error in sample_errors:
        existing = await db.errors_404.find_one(
            {"site_id": site_id, "url": error.url},
            {"_id": 0}
        )
        
        if not existing:
            await db.errors_404.insert_one(error.model_dump())
            errors_inserted += 1
    
    # Update site last_scan
    await db.sites.update_one(
        {"id": site_id},
        {"$set": {"last_scan": datetime.utcnow()}}
    )
    
    return {
        "message": "Scan completed",
        "errors_found": errors_inserted
    }

# ============ 404 ERRORS ROUTES ============

@api_router.get("/errors")
async def list_errors(
    request: Request,
    site_id: Optional[str] = None,
    status: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """List all 404 errors with optional filters"""
    current_user = await get_current_user(request)
    
    # Build query
    query = {}
    
    if site_id:
        # Verify user owns the site
        site = await db.sites.find_one(
            {"id": site_id, "user_id": current_user["sub"]},
            {"_id": 0}
        )
        if not site:
            raise HTTPException(status_code=404, detail="Site not found")
        query["site_id"] = site_id
    else:
        # Get all user's sites
        user_sites = await db.sites.find(
            {"user_id": current_user["sub"]},
            {"_id": 0, "id": 1}
        ).to_list(100)
        site_ids = [s["id"] for s in user_sites]
        query["site_id"] = {"$in": site_ids}
    
    if status:
        query["status"] = status
    
    errors = await db.errors_404.find(query, {"_id": 0}).sort("priority_score", -1).to_list(1000)
    
    return {"errors": errors, "count": len(errors)}

@api_router.get("/errors/{error_id}")
async def get_error_details(
    error_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get detailed information about a specific 404 error"""
    current_user = await get_current_user(request)
    
    error = await db.errors_404.find_one({"id": error_id}, {"_id": 0})
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    # Verify user owns the site
    site = await db.sites.find_one(
        {"id": error["site_id"], "user_id": current_user["sub"]},
        {"_id": 0}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Unauthorized")
    
    # Get backlinks
    backlinks = await db.backlinks.find({"error_id": error_id}, {"_id": 0}).to_list(100)
    
    # Get recommendations
    recommendation = await db.recommendations.find_one({"error_id": error_id}, {"_id": 0})
    
    return {
        "error": error,
        "site": site,
        "backlinks": backlinks,
        "recommendation": recommendation
    }

@api_router.post("/errors/{error_id}/generate-recommendations")
async def generate_recommendations(
    error_id: str,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Generate AI-powered recommendations for a 404 error"""
    current_user = await get_current_user(request)
    
    error = await db.errors_404.find_one({"id": error_id}, {"_id": 0})
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    # Verify user owns the site
    site = await db.sites.find_one(
        {"id": error["site_id"], "user_id": current_user["sub"]},
        {"_id": 0}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Unauthorized")
    
    # Get existing pages from the site
    all_site_errors = await db.errors_404.find(
        {"site_id": error["site_id"], "status": "fixed"},
        {"_id": 0, "url": 1}
    ).to_list(50)
    
    existing_pages = [e["url"] for e in all_site_errors]
    
    # Generate redirect recommendation
    redirect_rec = await generate_redirect_recommendation(
        error["url"],
        site["site_url"],
        existing_pages
    )
    
    # Generate content suggestion
    content_suggestion = await generate_content_suggestion(
        error["url"],
        site["site_url"],
        error.get("backlink_count", 0)
    )
    
    # Check if recommendation already exists
    existing_rec = await db.recommendations.find_one({"error_id": error_id}, {"_id": 0})
    
    recommendation = Recommendation(
        error_id=error_id,
        redirect_target=redirect_rec.get("redirect_target"),
        redirect_reason=redirect_rec.get("reason"),
        content_suggestion=content_suggestion
    )
    
    if existing_rec:
        # Update existing
        await db.recommendations.update_one(
            {"id": existing_rec["id"]},
            {"$set": recommendation.model_dump()}
        )
        recommendation.id = existing_rec["id"]
    else:
        # Insert new
        await db.recommendations.insert_one(recommendation.model_dump())
    
    return {"recommendation": recommendation}

@api_router.patch("/errors/{error_id}")
async def update_error_status(
    error_id: str,
    update: Error404Update,
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Update the status of a 404 error (mark as fixed or ignored)"""
    current_user = await get_current_user(request)
    
    error = await db.errors_404.find_one({"id": error_id}, {"_id": 0})
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    # Verify user owns the site
    site = await db.sites.find_one(
        {"id": error["site_id"], "user_id": current_user["sub"]},
        {"_id": 0}
    )
    
    if not site:
        raise HTTPException(status_code=404, detail="Unauthorized")
    
    # Update status
    await db.errors_404.update_one(
        {"id": error_id},
        {"$set": {"status": update.status, "last_checked": datetime.utcnow()}}
    )
    
    return {"message": "Error status updated", "status": update.status}

# ============ DASHBOARD ROUTES ============

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(
    request: Request,
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Get dashboard statistics"""
    current_user = await get_current_user(request)
    
    # Get user's sites
    sites_count = await db.sites.count_documents({"user_id": current_user["sub"]})
    
    # Get all site IDs
    user_sites = await db.sites.find(
        {"user_id": current_user["sub"]},
        {"_id": 0, "id": 1}
    ).to_list(100)
    site_ids = [s["id"] for s in user_sites]
    
    # Get error counts
    total_errors = await db.errors_404.count_documents({"site_id": {"$in": site_ids}})
    new_errors = await db.errors_404.count_documents({
        "site_id": {"$in": site_ids},
        "status": "new"
    })
    fixed_errors = await db.errors_404.count_documents({
        "site_id": {"$in": site_ids},
        "status": "fixed"
    })
    
    # Get total backlinks affected
    total_backlinks = await db.errors_404.aggregate([
        {"$match": {"site_id": {"$in": site_ids}}},
        {"$group": {"_id": None, "total": {"$sum": "$backlink_count"}}}
    ]).to_list(1)
    
    backlinks_affected = total_backlinks[0]["total"] if total_backlinks else 0
    
    # Get recent scans
    recent_scans = await db.scan_logs.find(
        {"site_id": {"$in": site_ids}},
        {"_id": 0}
    ).sort("started_at", -1).limit(5).to_list(5)
    
    return {
        "sites_count": sites_count,
        "total_errors": total_errors,
        "new_errors": new_errors,
        "fixed_errors": fixed_errors,
        "backlinks_affected": backlinks_affected,
        "recent_scans": recent_scans
    }

# Root route
@api_router.get("/")
async def root():
    return {
        "message": "404 Recovery & Backlink Retention API",
        "version": "1.0.0",
        "status": "running"
    }

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=settings.cors_origins.split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shutdown event
@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down application...")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
