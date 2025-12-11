from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager
import os
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Optional
import uuid

from database import get_db, init_db, engine, Base
from models import (
    UserDB, SiteDB, Error404DB, BacklinkDB, RecommendationDB, ScanLogDB,
    SiteCreate, Error404Update, ScanTrigger
)
from auth_handler import create_access_token, get_current_user
from ai_service import generate_redirect_recommendation, generate_content_suggestion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")
    yield

app = FastAPI(lifespan=lifespan, title="404 Recovery & Backlink Retention Tool")
api_router = APIRouter(prefix="/api")

@api_router.get("/auth/status")
async def auth_status(request: Request, db: AsyncSession = Depends(get_db)):
    try:
        current_user = await get_current_user(request)
        result = await db.execute(select(UserDB).where(UserDB.id == current_user["sub"]))
        user = result.scalar_one_or_none()
        
        if user:
            return {
                "authenticated": True,
                "user": {"id": user.id, "email": user.email}
            }
        return {"authenticated": False}
    except:
        return {"authenticated": False}

@api_router.post("/auth/demo-login")
async def demo_login(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(UserDB).where(UserDB.email == "demo@linkrecovery.com"))
    user = result.scalar_one_or_none()
    
    if not user:
        user = UserDB(
            id=str(uuid.uuid4()),
            email="demo@linkrecovery.com",
            google_id="demo_user"
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    access_token = create_access_token({"sub": user.id, "email": user.email})
    
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
    response = Response(content='{"message": "Logged out"}', media_type="application/json")
    response.delete_cookie("access_token")
    return response

@api_router.get("/sites")
async def list_sites(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    result = await db.execute(select(SiteDB).where(SiteDB.user_id == current_user["sub"]))
    sites = result.scalars().all()
    return {"sites": [{"id": s.id, "site_url": s.site_url, "status": s.status, "last_scan": s.last_scan} for s in sites]}

@api_router.post("/sites")
async def create_site(site_data: SiteCreate, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    result = await db.execute(
        select(SiteDB).where(SiteDB.user_id == current_user["sub"], SiteDB.site_url == site_data.site_url)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Site already exists")
    
    site = SiteDB(
        id=str(uuid.uuid4()),
        user_id=current_user["sub"],
        site_url=site_data.site_url,
        permission_level="owner"
    )
    db.add(site)
    await db.commit()
    await db.refresh(site)
    
    return {"message": "Site added successfully", "site": {"id": site.id, "site_url": site.site_url}}

@api_router.post("/sites/{site_id}/scan")
async def trigger_scan(site_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    result = await db.execute(
        select(SiteDB).where(SiteDB.id == site_id, SiteDB.user_id == current_user["sub"])
    )
    site = result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    
    sample_errors = [
        {"url": f"{site.site_url}/old-product-page", "backlink_count": 5, "priority_score": 75, "impressions": 150},
        {"url": f"{site.site_url}/deleted-blog-post", "backlink_count": 12, "priority_score": 90, "impressions": 450},
        {"url": f"{site.site_url}/missing-category", "backlink_count": 3, "priority_score": 60, "impressions": 80},
    ]
    
    errors_inserted = 0
    for err_data in sample_errors:
        result = await db.execute(
            select(Error404DB).where(Error404DB.site_id == site_id, Error404DB.url == err_data["url"])
        )
        if not result.scalar_one_or_none():
            error = Error404DB(
                id=str(uuid.uuid4()),
                site_id=site_id,
                url=err_data["url"],
                backlink_count=err_data["backlink_count"],
                priority_score=err_data["priority_score"],
                impressions=err_data["impressions"]
            )
            db.add(error)
            errors_inserted += 1
    
    site.last_scan = datetime.utcnow()
    await db.commit()
    
    return {"message": "Scan completed", "errors_found": errors_inserted}

@api_router.get("/errors")
async def list_errors(request: Request, site_id: Optional[str] = None, status: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    query = select(Error404DB).join(SiteDB).where(SiteDB.user_id == current_user["sub"])
    
    if site_id:
        query = query.where(Error404DB.site_id == site_id)
    if status:
        query = query.where(Error404DB.status == status)
    
    query = query.order_by(Error404DB.priority_score.desc())
    result = await db.execute(query)
    errors = result.scalars().all()
    
    return {
        "errors": [
            {
                "id": e.id, "site_id": e.site_id, "url": e.url,
                "backlink_count": e.backlink_count, "priority_score": e.priority_score,
                "status": e.status, "impressions": e.impressions, "clicks": e.clicks
            } for e in errors
        ],
        "count": len(errors)
    }

@api_router.get("/errors/{error_id}")
async def get_error_details(error_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    result = await db.execute(
        select(Error404DB).options(selectinload(Error404DB.backlinks), selectinload(Error404DB.recommendation))
        .where(Error404DB.id == error_id)
    )
    error = result.scalar_one_or_none()
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    site_result = await db.execute(
        select(SiteDB).where(SiteDB.id == error.site_id, SiteDB.user_id == current_user["sub"])
    )
    site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Unauthorized")
    
    return {
        "error": {
            "id": error.id, "site_id": error.site_id, "url": error.url,
            "backlink_count": error.backlink_count, "priority_score": error.priority_score,
            "status": error.status
        },
        "site": {"id": site.id, "site_url": site.site_url},
        "backlinks": [{"id": b.id, "source_url": b.source_url, "anchor_text": b.anchor_text} for b in error.backlinks],
        "recommendation": {
            "redirect_target": error.recommendation.redirect_target,
            "redirect_reason": error.recommendation.redirect_reason,
            "content_suggestion": error.recommendation.content_suggestion
        } if error.recommendation else None
    }

@api_router.post("/errors/{error_id}/generate-recommendations")
async def generate_recommendations(error_id: str, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    result = await db.execute(select(Error404DB).where(Error404DB.id == error_id))
    error = result.scalar_one_or_none()
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    site_result = await db.execute(
        select(SiteDB).where(SiteDB.id == error.site_id, SiteDB.user_id == current_user["sub"])
    )
    site = site_result.scalar_one_or_none()
    
    if not site:
        raise HTTPException(status_code=404, detail="Unauthorized")
    
    redirect_rec = await generate_redirect_recommendation(error.url, site.site_url, [])
    content_suggestion = await generate_content_suggestion(error.url, site.site_url, error.backlink_count)
    
    rec_result = await db.execute(select(RecommendationDB).where(RecommendationDB.error_id == error_id))
    existing_rec = rec_result.scalar_one_or_none()
    
    if existing_rec:
        existing_rec.redirect_target = redirect_rec.get("redirect_target")
        existing_rec.redirect_reason = redirect_rec.get("reason")
        existing_rec.content_suggestion = content_suggestion
        existing_rec.generated_at = datetime.utcnow()
    else:
        rec = RecommendationDB(
            id=str(uuid.uuid4()),
            error_id=error_id,
            redirect_target=redirect_rec.get("redirect_target"),
            redirect_reason=redirect_rec.get("reason"),
            content_suggestion=content_suggestion
        )
        db.add(rec)
    
    await db.commit()
    
    return {"recommendation": {
        "redirect_target": redirect_rec.get("redirect_target"),
        "redirect_reason": redirect_rec.get("reason"),
        "content_suggestion": content_suggestion
    }}

@api_router.patch("/errors/{error_id}")
async def update_error_status(error_id: str, update_data: Error404Update, request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    result = await db.execute(select(Error404DB).where(Error404DB.id == error_id))
    error = result.scalar_one_or_none()
    
    if not error:
        raise HTTPException(status_code=404, detail="Error not found")
    
    site_result = await db.execute(
        select(SiteDB).where(SiteDB.id == error.site_id, SiteDB.user_id == current_user["sub"])
    )
    if not site_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Unauthorized")
    
    error.status = update_data.status
    error.last_checked = datetime.utcnow()
    await db.commit()
    
    return {"message": "Error status updated", "status": update_data.status}

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user(request)
    
    sites_result = await db.execute(select(SiteDB).where(SiteDB.user_id == current_user["sub"]))
    sites = sites_result.scalars().all()
    site_ids = [s.id for s in sites]
    
    if not site_ids:
        return {
            "sites_count": 0, "total_errors": 0, "new_errors": 0,
            "fixed_errors": 0, "backlinks_affected": 0, "recent_scans": []
        }
    
    total_result = await db.execute(
        select(func.count(Error404DB.id)).where(Error404DB.site_id.in_(site_ids))
    )
    total_errors = total_result.scalar() or 0
    
    new_result = await db.execute(
        select(func.count(Error404DB.id)).where(Error404DB.site_id.in_(site_ids), Error404DB.status == "new")
    )
    new_errors = new_result.scalar() or 0
    
    fixed_result = await db.execute(
        select(func.count(Error404DB.id)).where(Error404DB.site_id.in_(site_ids), Error404DB.status == "fixed")
    )
    fixed_errors = fixed_result.scalar() or 0
    
    backlinks_result = await db.execute(
        select(func.sum(Error404DB.backlink_count)).where(Error404DB.site_id.in_(site_ids))
    )
    backlinks_affected = backlinks_result.scalar() or 0
    
    return {
        "sites_count": len(sites),
        "total_errors": total_errors,
        "new_errors": new_errors,
        "fixed_errors": fixed_errors,
        "backlinks_affected": backlinks_affected,
        "recent_scans": []
    }

@api_router.get("/")
async def root():
    return {"message": "404 Recovery & Backlink Retention API", "version": "1.0.0", "status": "running"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
