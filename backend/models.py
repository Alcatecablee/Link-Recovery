from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

from database import Base

def generate_uuid():
    return str(uuid.uuid4())

class UserDB(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=generate_uuid)
    email = Column(String, unique=True, nullable=False)
    google_id = Column(String, nullable=True)
    google_access_token = Column(Text, nullable=True)
    google_refresh_token = Column(Text, nullable=True)
    google_token_expiry = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    sites = relationship("SiteDB", back_populates="user")

class SiteDB(Base):
    __tablename__ = "sites"
    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    site_url = Column(String, nullable=False)
    site_type = Column(String, default="url-prefix")
    permission_level = Column(String, nullable=False)
    last_scan = Column(DateTime, nullable=True)
    status = Column(String, default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("UserDB", back_populates="sites")
    errors = relationship("Error404DB", back_populates="site")
    scan_logs = relationship("ScanLogDB", back_populates="site")

class Error404DB(Base):
    __tablename__ = "errors_404"
    id = Column(String, primary_key=True, default=generate_uuid)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    url = Column(String, nullable=False)
    backlink_count = Column(Integer, default=0)
    priority_score = Column(Integer, default=0)
    status = Column(String, default="new")
    detected_at = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow)
    impressions = Column(Integer, default=0)
    clicks = Column(Integer, default=0)
    
    site = relationship("SiteDB", back_populates="errors")
    backlinks = relationship("BacklinkDB", back_populates="error")
    recommendation = relationship("RecommendationDB", back_populates="error", uselist=False)

class BacklinkDB(Base):
    __tablename__ = "backlinks"
    id = Column(String, primary_key=True, default=generate_uuid)
    error_id = Column(String, ForeignKey("errors_404.id"), nullable=False)
    source_url = Column(String, nullable=False)
    anchor_text = Column(String, nullable=True)
    discovered_at = Column(DateTime, default=datetime.utcnow)
    
    error = relationship("Error404DB", back_populates="backlinks")

class RecommendationDB(Base):
    __tablename__ = "recommendations"
    id = Column(String, primary_key=True, default=generate_uuid)
    error_id = Column(String, ForeignKey("errors_404.id"), nullable=False, unique=True)
    redirect_target = Column(String, nullable=True)
    redirect_reason = Column(Text, nullable=True)
    content_suggestion = Column(Text, nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    error = relationship("Error404DB", back_populates="recommendation")

class ScanLogDB(Base):
    __tablename__ = "scan_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    site_id = Column(String, ForeignKey("sites.id"), nullable=False)
    scan_type = Column(String, nullable=False)
    status = Column(String, nullable=False)
    errors_found = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    site = relationship("SiteDB", back_populates="scan_logs")

class SiteCreate(BaseModel):
    site_url: str

class Error404Update(BaseModel):
    status: str

class ScanTrigger(BaseModel):
    site_id: str
