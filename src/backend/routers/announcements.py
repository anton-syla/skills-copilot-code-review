"""
Announcements endpoints for the High School Management System API
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from datetime import datetime
from bson import ObjectId

from ..database import announcements_collection, teachers_collection

router = APIRouter(
    prefix="/announcements",
    tags=["announcements"]
)


def get_current_user(username: str) -> Dict[str, Any]:
    """Dependency to verify user is logged in"""
    teacher = teachers_collection.find_one({"_id": username})
    if not teacher:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return teacher


@router.get("/active")
def get_active_announcements() -> List[Dict[str, Any]]:
    """Get all active announcements (public endpoint)"""
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Find announcements that are currently active
    announcements = list(announcements_collection.find({
        "$or": [
            {"start_date": None},  # No start date = start immediately
            {"start_date": {"$lte": today}}
        ],
        "expiration_date": {"$gte": today}  # Not expired
    }).sort("_id", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.get("/all")
def get_all_announcements(username: str) -> List[Dict[str, Any]]:
    """Get all announcements (admin only)"""
    user = get_current_user(username)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    announcements = list(announcements_collection.find().sort("_id", -1))
    
    # Convert ObjectId to string for JSON serialization
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    
    return announcements


@router.post("/create")
def create_announcement(
    username: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Create a new announcement (admin only)"""
    user = get_current_user(username)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate dates
    today = datetime.now().strftime("%Y-%m-%d")
    if expiration_date < today:
        raise HTTPException(status_code=400, detail="Expiration date must be in the future")
    
    if start_date and start_date < today:
        raise HTTPException(status_code=400, detail="Start date cannot be in the past")
    
    announcement = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date,
        "created_at": datetime.now().strftime("%Y-%m-%d"),
        "created_by": username
    }
    
    result = announcements_collection.insert_one(announcement)
    announcement["_id"] = str(result.inserted_id)
    
    return announcement


@router.put("/update/{announcement_id}")
def update_announcement(
    announcement_id: str,
    username: str,
    title: str,
    message: str,
    expiration_date: str,
    start_date: Optional[str] = None
) -> Dict[str, Any]:
    """Update an existing announcement (admin only)"""
    user = get_current_user(username)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Validate dates
    today = datetime.now().strftime("%Y-%m-%d")
    if expiration_date < today:
        raise HTTPException(status_code=400, detail="Expiration date must be in the future")
    
    if start_date and start_date < today:
        raise HTTPException(status_code=400, detail="Start date cannot be in the past")
    
    try:
        obj_id = ObjectId(announcement_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    update_data = {
        "title": title,
        "message": message,
        "start_date": start_date,
        "expiration_date": expiration_date
    }
    
    result = announcements_collection.find_one_and_update(
        {"_id": obj_id},
        {"$set": update_data},
        return_document=True
    )
    
    if not result:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    result["_id"] = str(result["_id"])
    return result


@router.delete("/delete/{announcement_id}")
def delete_announcement(announcement_id: str, username: str) -> Dict[str, str]:
    """Delete an announcement (admin only)"""
    user = get_current_user(username)
    
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        obj_id = ObjectId(announcement_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid announcement ID")
    
    result = announcements_collection.delete_one({"_id": obj_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    return {"message": "Announcement deleted successfully"}
