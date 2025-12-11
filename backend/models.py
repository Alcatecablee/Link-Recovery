from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid

class Site(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    site_url: str
    site_type: str = "url-prefix"  # or 'domain'
    permission_level: str
    last_scan: Optional[datetime] = None
    status: str = "active"  # active, paused, error
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Error404(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    site_id: str
    url: str
    backlink_count: int = 0
    priority_score: int = 0  # 0-100 based on backlinks and traffic
    status: str = "new"  # new, fixed, ignored
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked: datetime = Field(default_factory=datetime.utcnow)
    impressions: int = 0
    clicks: int = 0

class Backlink(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error_id: str
    source_url: str
    anchor_text: Optional[str] = None
    discovered_at: datetime = Field(default_factory=datetime.utcnow)

class Recommendation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    error_id: str
    redirect_target: Optional[str] = None
    redirect_reason: Optional[str] = None
    content_suggestion: Optional[str] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class ScanLog(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    site_id: str
    scan_type: str  # manual, scheduled
    status: str  # running, completed, failed
    errors_found: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    google_id: Optional[str] = None
    google_access_token: Optional[str] = None
    google_refresh_token: Optional[str] = None
    google_token_expiry: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

# Request/Response models
class SiteCreate(BaseModel):
    site_url: str

class Error404Update(BaseModel):
    status: str  # fixed, ignored

class ScanTrigger(BaseModel):
    site_id: str