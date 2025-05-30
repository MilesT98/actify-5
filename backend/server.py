from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta
import hashlib
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Collections
users_collection = db.users
follows_collection = db.follows
notifications_collection = db.notifications
global_challenges_collection = db.global_challenges
global_submissions_collection = db.global_submissions
global_votes_collection = db.global_votes

# New collections for Global Activity System
daily_global_activities_collection = db.daily_global_activities
global_activity_completions_collection = db.global_activity_completions
activity_dataset_collection = db.activity_dataset

# Create the main app
app = FastAPI(title="ACTIFY API", version="1.0.0")

# NEW: Follow model
class Follow(BaseModel):
    follower_id: str
    following_id: str

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Pydantic Models
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str

class GlobalChallenge(BaseModel):
    id: str
    prompt: str
    created_at: datetime
    expires_at: datetime
    promptness_window_minutes: int
    is_active: bool

class GlobalSubmission(BaseModel):
    id: str
    user_id: str
    username: str
    challenge_id: str
    challenge_prompt: str
    description: str
    photo_data: Optional[str]
    created_at: datetime
    votes: int = 0
    comments: List[Dict[str, Any]] = []
    reactions: Dict[str, int] = {}

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    full_name: str
    created_at: datetime
    avatar_color: str
    groups: List[str] = []
    achievements: List[str] = []

class LoginRequest(BaseModel):
    username: str
    password: str

class GroupCreate(BaseModel):
    name: str
    description: str
    category: str = "fitness"
    is_public: bool = True

# Enhanced Group Models for Weekly Activity Challenge System
class GroupResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str = "fitness"
    is_public: bool = False
    created_by: str
    created_at: datetime
    members: List[str]
    member_count: int
    max_members: int = 7  # Limit to 7 members
    admin_id: str  # Group admin (initially creator)
    invite_code: str  # Unique invite code for joining
    current_challenge: str = "Weekly Activity Challenge"
    
    # Weekly submission system
    submission_day: Optional[str] = None  # Day of week chosen by admin
    current_week_start: Optional[datetime] = None
    activities_submitted_this_week: int = 0
    activities_needed: int = 7  # Always need 7 total activities
    submission_phase_active: bool = False
    
    # Daily reveal system
    daily_reveals: List[dict] = []  # Track daily revealed activities
    current_day_activity: Optional[dict] = None
    
    # Points and ranking
    weekly_rankings: List[dict] = []
    current_week_points: dict = {}  # member_id: points

class WeeklyActivitySubmission(BaseModel):
    id: str
    group_id: str
    submitted_by: str
    activity_title: str
    activity_description: str
    week_start: datetime
    submission_order: int  # 1-7, order submitted this week
    created_at: datetime
    is_revealed: bool = False
    reveal_date: Optional[datetime] = None

class DailyActivityCompletion(BaseModel):
    id: str
    group_id: str
    activity_submission_id: str  # Links to the revealed activity
    completed_by: str
    completion_proof_url: str  # Photo/video proof
    completion_description: str
    completed_at: datetime
    day_of_week: int  # 1-7, which day of the weekly cycle
    completion_order: int  # 1st, 2nd, 3rd to complete this activity
    points_earned: int  # 3, 2, 1, or 0

class WeeklyRanking(BaseModel):
    id: str
    group_id: str
    member_id: str
    week_start: datetime
    total_points: int
    activities_completed: int
    rank_position: int  # 1st, 2nd, 3rd, etc.
    created_at: datetime

class JoinGroupRequest(BaseModel):
    group_id: str

class ActivitySubmission(BaseModel):
    group_id: str
    challenge_type: str
    description: str
    photo_data: Optional[str] = None

class SubmissionResponse(BaseModel):
    id: str
    user_id: str
    username: str
    group_id: str
    challenge_type: str
    description: str
    photo_data: Optional[str]
    created_at: datetime
    votes: int = 0
    reactions: Dict[str, int] = {}

class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    data: Dict[str, Any] = {}
    read: bool = False
    created_at: datetime

# Achievement Models
class Achievement(BaseModel):
    id: str
    name: str
    description: str
    icon: str
    unlocked_at: datetime

# NEW: Global Activity System Models
class ActivityDataset(BaseModel):
    id: str
    title: str
    description: str
    category: str = "general"
    difficulty: str = "easy"  # easy, medium, hard
    estimated_time_minutes: int = 15
    is_active: bool = True
    created_at: datetime

class DailyGlobalActivity(BaseModel):
    id: str
    activity_id: str  # Reference to ActivityDataset
    date: str  # YYYY-MM-DD format
    selected_at: datetime  # Random time between 05:00-00:00 GMT
    activity_title: str
    activity_description: str
    is_active: bool = True
    participant_count: int = 0

class GlobalActivityCompletion(BaseModel):
    id: str
    activity_id: str  # Reference to DailyGlobalActivity
    user_id: str
    username: str
    description: str
    photo_url: Optional[str] = None
    completed_at: datetime
    is_friends_visible: bool = False  # Unlocked after user posts
    votes: int = 0

# Utility functions
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def generate_avatar_color() -> str:
    colors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FCEA2B", "#FF9F43", "#6C5CE7", "#FD79A8"]
    return colors[len(colors) % 8]

async def create_notification(user_id: str, notification_type: str, title: str, message: str, data: Dict = None):
    notification = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "type": notification_type,
        "title": title,
        "message": message,
        "data": data or {},
        "read": False,
        "created_at": datetime.utcnow()
    }
    await db.notifications.insert_one(notification)

# API Routes

@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# User Authentication Routes
@api_router.post("/users", response_model=UserResponse)
async def create_user(user_data: UserCreate):
    # Check if user exists
    existing = await db.users.find_one({"$or": [{"username": user_data.username}, {"email": user_data.email}]})
    if existing:
        raise HTTPException(status_code=400, detail="Username or email already exists")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password": hash_password(user_data.password),
        "full_name": user_data.full_name,
        "created_at": datetime.utcnow(),
        "avatar_color": generate_avatar_color(),
        "groups": [],
        "achievements": [],
        "stats": {
            "total_activities": 0,
            "current_streak": 0,
            "total_groups_joined": 0
        }
    }
    
    await db.users.insert_one(user_doc)
    
    # Create welcome notification
    await create_notification(
        user_id, 
        "welcome", 
        "Welcome to ACTIFY!", 
        f"Hey {user_data.full_name}! Ready to start your fitness journey?"
    )
    
    return UserResponse(**user_doc)

@api_router.post("/login")
async def login(login_data: LoginRequest):
    user = await db.users.find_one({"username": login_data.username})
    if not user or user["password"] != hash_password(login_data.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Create session
    session_id = str(uuid.uuid4())
    session_doc = {
        "session_id": session_id,
        "user_id": user["id"],
        "created_at": datetime.utcnow(),
        "expires_at": datetime.utcnow() + timedelta(days=30)
    }
    await db.sessions.insert_one(session_doc)
    
    return {
        "session_id": session_id,
        "user": UserResponse(**user),
        "message": "Login successful"
    }

@api_router.get("/users/search")
async def search_users(q: str = ""):
    """Search users by username or full name"""
    try:
        if not q or len(q) < 2:
            return []
        
        # Search by username or full name (case insensitive)
        users_cursor = db.users.find(
            {
                "$or": [
                    {"username": {"$regex": q, "$options": "i"}},
                    {"full_name": {"$regex": q, "$options": "i"}}
                ]
            },
            {"_id": 0, "password": 0, "email": 0}
        ).limit(10)
        
        users = await users_cursor.to_list(length=10)
        return users
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse(**user)

# Group Management Routes
@api_router.post("/groups", response_model=GroupResponse)
async def create_group(
    name: str = Form(...),
    description: str = Form(""),
    category: str = Form("fitness"),
    is_public: bool = Form(False),  # Default to private
    user_id: str = Form(...)
):
    import random
    import string
    
    # Generate unique invite code
    invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    # Ensure invite code is unique
    while await db.groups.find_one({"invite_code": invite_code}):
        invite_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    group_doc = {
        "id": str(uuid.uuid4()),
        "name": name,
        "description": description,
        "category": category,
        "is_public": is_public,
        "created_by": user_id,
        "admin_id": user_id,  # Creator is initial admin
        "invite_code": invite_code,
        "created_at": datetime.utcnow(),
        "members": [user_id],  # Creator is first member
        "member_count": 1,
        "max_members": 7,
        "current_challenge": "Weekly Activity Challenge",
        
        # Weekly submission system
        "submission_day": None,
        "current_week_start": None,
        "activities_submitted_this_week": 0,
        "activities_needed": 7,
        "submission_phase_active": False,
        
        # Daily reveal system
        "daily_reveals": [],
        "current_day_activity": None,
        
        # Points and ranking
        "weekly_rankings": [],
        "current_week_points": {user_id: 0}
    }
    
    result = await db.groups.insert_one(group_doc)
    
    # Add group to user's groups
    await db.users.update_one(
        {"id": user_id},
        {"$push": {"groups": group_doc["id"]}, "$inc": {"stats.total_groups_joined": 1}}
    )
    
    return GroupResponse(**group_doc)

@api_router.get("/groups", response_model=List[GroupResponse])
async def get_groups(limit: int = 20):
    groups = await db.groups.find({"is_public": True}).limit(limit).to_list(length=None)
    return [GroupResponse(**group) for group in groups]

@api_router.get("/users/{user_id}/groups", response_model=List[GroupResponse])
async def get_user_groups(user_id: str):
    """Get all groups where the user is a member"""
    groups = await db.groups.find({"members": user_id}).to_list(length=None)
    return [GroupResponse(**group) for group in groups]

# Weekly Activity Challenge System Endpoints

@api_router.post("/groups/{group_id}/join-by-code")
async def join_group_by_invite_code(
    group_id: str,
    invite_code: str = Form(...),
    user_id: str = Form(...)
):
    """Join a group using invite code"""
    group = await db.groups.find_one({"id": group_id, "invite_code": invite_code})
    if not group:
        raise HTTPException(status_code=404, detail="Invalid invite code")
    
    if len(group["members"]) >= group.get("max_members", 7):
        raise HTTPException(status_code=400, detail="Group is full (max 7 members)")
    
    if user_id in group["members"]:
        raise HTTPException(status_code=400, detail="User already in group")
    
    # Add user to group
    await db.groups.update_one(
        {"id": group_id},
        {
            "$push": {"members": user_id},
            "$inc": {"member_count": 1},
            f"$set": {f"current_week_points.{user_id}": 0}
        }
    )
    
    return {"success": True, "message": "Successfully joined group"}

@api_router.post("/groups/{group_id}/set-submission-day")
async def set_submission_day(
    group_id: str,
    submission_day: str = Form(...),  # e.g., "Monday", "Tuesday", etc.
    admin_id: str = Form(...)
):
    """Admin sets the weekly submission day"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if group["admin_id"] != admin_id:
        raise HTTPException(status_code=403, detail="Only group admin can set submission day")
    
    await db.groups.update_one(
        {"id": group_id},
        {"$set": {"submission_day": submission_day}}
    )
    
    return {"success": True, "message": f"Submission day set to {submission_day}"}

@api_router.post("/groups/{group_id}/start-weekly-submissions")
async def start_weekly_submissions(
    group_id: str,
    admin_id: str = Form(...)
):
    """Admin starts the weekly submission phase"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if group["admin_id"] != admin_id:
        raise HTTPException(status_code=403, detail="Only group admin can start submissions")
    
    # Start new week
    week_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    
    await db.groups.update_one(
        {"id": group_id},
        {
            "$set": {
                "submission_phase_active": True,
                "current_week_start": week_start,
                "activities_submitted_this_week": 0
            }
        }
    )
    
    return {"success": True, "message": "Weekly submission phase started"}

@api_router.post("/groups/{group_id}/submit-activity")
async def submit_weekly_activity(
    group_id: str,
    activity_title: str = Form(...),
    activity_description: str = Form(...),
    user_id: str = Form(...)
):
    """Submit an activity idea for the weekly challenge"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.get("submission_phase_active", False):
        raise HTTPException(status_code=400, detail="Submission phase not active")
    
    if group.get("activities_submitted_this_week", 0) >= 7:
        raise HTTPException(status_code=400, detail="All 7 activities already submitted")
    
    if user_id not in group["members"]:
        raise HTTPException(status_code=403, detail="User not in group")
    
    # Create activity submission
    submission_doc = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "submitted_by": user_id,
        "activity_title": activity_title,
        "activity_description": activity_description,
        "week_start": group["current_week_start"],
        "submission_order": group["activities_submitted_this_week"] + 1,
        "created_at": datetime.utcnow(),
        "is_revealed": False,
        "reveal_date": None
    }
    
    await db.weekly_activity_submissions.insert_one(submission_doc)
    
    # Update group submission count
    new_count = group["activities_submitted_this_week"] + 1
    update_data = {"$set": {"activities_submitted_this_week": new_count}}
    
    # If we've reached 7 submissions, end submission phase
    if new_count >= 7:
        update_data["$set"]["submission_phase_active"] = False
    
    await db.groups.update_one({"id": group_id}, update_data)
    
    return {"success": True, "submission_count": new_count, "remaining": 7 - new_count}

@api_router.get("/groups/{group_id}/weekly-activities")
async def get_weekly_activities(group_id: str):
    """Get this week's submitted activities for a group"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if not group.get("current_week_start"):
        return []
    
    activities = await db.weekly_activity_submissions.find({
        "group_id": group_id,
        "week_start": group["current_week_start"]
    }).to_list(length=None)
    
    # Convert MongoDB documents to JSON-serializable format
    serialized_activities = []
    for activity in activities:
        activity.pop('_id', None)  # Remove MongoDB ObjectId
        # Convert datetime to ISO string if needed
        if 'created_at' in activity and hasattr(activity['created_at'], 'isoformat'):
            activity['created_at'] = activity['created_at'].isoformat()
        if 'week_start' in activity and hasattr(activity['week_start'], 'isoformat'):
            activity['week_start'] = activity['week_start'].isoformat()
        if 'reveal_date' in activity and activity['reveal_date'] and hasattr(activity['reveal_date'], 'isoformat'):
            activity['reveal_date'] = activity['reveal_date'].isoformat()
        serialized_activities.append(activity)
    
    return serialized_activities

@api_router.get("/groups/{group_id}/current-day-activity")
async def get_current_day_activity(group_id: str):
    """Get today's revealed activity for the group"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    return {"activity": group.get("current_day_activity")}

@api_router.post("/groups/{group_id}/complete-activity")
async def complete_daily_activity(
    group_id: str,
    activity_submission_id: str = Form(...),
    completion_proof: UploadFile = File(...),
    completion_description: str = Form(""),
    user_id: str = Form(...)
):
    """Submit proof of completing today's activity"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id not in group["members"]:
        raise HTTPException(status_code=403, detail="User not in group")
    
    # Check if user already completed this activity
    existing_completion = await db.daily_activity_completions.find_one({
        "group_id": group_id,
        "activity_submission_id": activity_submission_id,
        "completed_by": user_id
    })
    
    if existing_completion:
        raise HTTPException(status_code=400, detail="Activity already completed by user")
    
    # Count existing completions for this activity to determine points
    completion_count = await db.daily_activity_completions.count_documents({
        "group_id": group_id,
        "activity_submission_id": activity_submission_id
    })
    
    # Determine points (3 for 1st, 2 for 2nd, 1 for 3rd, 0 for rest)
    points_map = {0: 3, 1: 2, 2: 1}
    points_earned = points_map.get(completion_count, 0)
    completion_order = completion_count + 1
    
    # Save proof image (in production, save to cloud storage)
    proof_url = f"data:image/jpeg;base64,{completion_proof.file.read().hex()}"
    
    # Create completion record
    completion_doc = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "activity_submission_id": activity_submission_id,
        "completed_by": user_id,
        "completion_proof_url": proof_url,
        "completion_description": completion_description,
        "completed_at": datetime.utcnow(),
        "day_of_week": completion_count + 1,  # Simplified
        "completion_order": completion_order,
        "points_earned": points_earned
    }
    
    await db.daily_activity_completions.insert_one(completion_doc)
    
    # Update user's weekly points
    await db.groups.update_one(
        {"id": group_id},
        {"$inc": {f"current_week_points.{user_id}": points_earned}}
    )
    
    return {
        "success": True,
        "points_earned": points_earned,
        "completion_order": completion_order,
        "message": f"Activity completed! Earned {points_earned} points"
    }

@api_router.get("/groups/{group_id}/weekly-rankings")
async def get_weekly_rankings(group_id: str):
    """Get current week's rankings for the group"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get user details for the rankings
    member_rankings = []
    current_points = group.get("current_week_points", {})
    
    for member_id, points in current_points.items():
        user = await db.users.find_one({"id": member_id})
        if user:
            member_rankings.append({
                "user_id": member_id,
                "username": user["username"],
                "full_name": user["full_name"],
                "avatar_color": user["avatar_color"],
                "points": points
            })
    
    # Sort by points (descending)
    member_rankings.sort(key=lambda x: x["points"], reverse=True)
    
    # Add rank positions
    for i, ranking in enumerate(member_rankings):
        ranking["rank"] = i + 1
    
    return {"rankings": member_rankings}

@api_router.post("/groups/{group_id}/reveal-daily-activity")
async def reveal_daily_activity(
    group_id: str,
    admin_id: str = Form(...),
    day_number: int = Form(...)  # 1-7, which day of the week
):
    """Admin triggers daily activity reveal (or automated system)"""
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if we have enough activities to reveal
    activities = await db.weekly_activity_submissions.find({
        "group_id": group_id,
        "week_start": group["current_week_start"]
    }).to_list(length=None)
    
    if len(activities) < 7:
        raise HTTPException(status_code=400, detail="Not enough activities submitted yet")
    
    # Check if activity for this day already revealed
    revealed_today = any(r.get("day_number") == day_number for r in group.get("daily_reveals", []))
    if revealed_today:
        return {"message": "Activity already revealed for this day"}
    
    # Randomly select an activity that hasn't been revealed yet
    revealed_activity_ids = [r.get("activity_id") for r in group.get("daily_reveals", [])]
    available_activities = [a for a in activities if a["id"] not in revealed_activity_ids]
    
    if not available_activities:
        raise HTTPException(status_code=400, detail="All activities already revealed")
    
    import random
    selected_activity = random.choice(available_activities)
    
    # Mark activity as revealed and update group
    reveal_data = {
        "day_number": day_number,
        "activity_id": selected_activity["id"],
        "activity_title": selected_activity["activity_title"], 
        "activity_description": selected_activity["activity_description"],
        "revealed_at": datetime.utcnow(),
        "submitted_by": selected_activity["submitted_by"]
    }
    
    # Update group with daily reveal and current day activity
    await db.groups.update_one(
        {"id": group_id},
        {
            "$push": {"daily_reveals": reveal_data},
            "$set": {"current_day_activity": reveal_data}
        }
    )
    
    # Mark the activity submission as revealed
    await db.weekly_activity_submissions.update_one(
        {"id": selected_activity["id"]},
        {"$set": {"is_revealed": True, "reveal_date": datetime.utcnow()}}
    )
    
    return {
        "success": True,
        "revealed_activity": reveal_data,
        "day_number": day_number,
        "message": f"Day {day_number} activity revealed: {selected_activity['activity_title']}"
    }

@api_router.get("/groups/{group_id}", response_model=GroupResponse)
async def get_group(group_id: str):
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return GroupResponse(**group)

@api_router.post("/groups/{group_id}/join")
async def join_group(group_id: str, user_id: str = Form(...)):
    # Check if group exists
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check if user already in group
    if user_id in group.get("members", []):
        raise HTTPException(status_code=400, detail="Already a member of this group")
    
    # Add user to group
    await db.groups.update_one(
        {"id": group_id},
        {"$push": {"members": user_id}, "$inc": {"member_count": 1}}
    )
    
    # Add group to user's groups
    await db.users.update_one(
        {"id": user_id},
        {"$push": {"groups": group_id}, "$inc": {"stats.total_groups_joined": 1}}
    )
    
    # Get user info for notification
    user = await db.users.find_one({"id": user_id})
    
    # Notify all group members (except the new member)
    for member_id in group["members"]:
        if member_id != user_id:
            await create_notification(
                member_id,
                "group_join",
                "New Group Member!",
                f"{user['username']} joined {group['name']}",
                {"group_id": group_id, "new_member_id": user_id}
            )
    
    return {"message": "Successfully joined group", "group_id": group_id}

# Activity Submission Routes
@api_router.post("/submissions", response_model=SubmissionResponse)
async def create_submission(
    group_id: str = Form(...),
    challenge_type: str = Form(...),
    description: str = Form(...),
    user_id: str = Form(...),
    photo: Optional[UploadFile] = File(None)
):
    # Verify user is member of group
    group = await db.groups.find_one({"id": group_id})
    if not group or user_id not in group.get("members", []):
        raise HTTPException(status_code=403, detail="Not a member of this group")
    
    # Process photo if provided
    photo_data = None
    if photo:
        content = await photo.read()
        photo_data = base64.b64encode(content).decode('utf-8')
    
    # Get user info
    user = await db.users.find_one({"id": user_id})
    
    submission_id = str(uuid.uuid4())
    submission_doc = {
        "id": submission_id,
        "user_id": user_id,
        "username": user["username"],
        "group_id": group_id,
        "challenge_type": challenge_type,
        "description": description,
        "photo_data": photo_data,
        "created_at": datetime.utcnow(),
        "votes": 0,
        "reactions": {}
    }
    
    await db.submissions.insert_one(submission_doc)
    
    # Update user stats
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"stats.total_activities": 1, "stats.current_streak": 1}}
    )
    
    # Notify group members
    for member_id in group["members"]:
        if member_id != user_id:
            await create_notification(
                member_id,
                "new_activity",
                "New Activity Posted!",
                f"{user['username']} completed the {challenge_type} challenge",
                {"group_id": group_id, "submission_id": submission_id}
            )
    
    return SubmissionResponse(**submission_doc)

@api_router.get("/groups/{group_id}/submissions", response_model=List[SubmissionResponse])
async def get_group_submissions(group_id: str, limit: int = 20):
    submissions = await db.submissions.find({"group_id": group_id}).sort("created_at", -1).limit(limit).to_list(length=None)
    return [SubmissionResponse(**submission) for submission in submissions]

@api_router.get("/submissions/feed", response_model=List[SubmissionResponse])
async def get_activity_feed(user_id: str, limit: int = 50):
    # Get user's groups
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user_groups = user.get("groups", [])
    if not user_groups:
        return []
    
    # Get submissions from user's groups
    submissions = await db.submissions.find(
        {"group_id": {"$in": user_groups}}
    ).sort("created_at", -1).limit(limit).to_list(length=None)
    
    return [SubmissionResponse(**submission) for submission in submissions]

# Notification Routes
@api_router.get("/notifications/{user_id}", response_model=List[NotificationResponse])
async def get_notifications(user_id: str, limit: int = 50):
    notifications = await db.notifications.find(
        {"user_id": user_id}
    ).sort("created_at", -1).limit(limit).to_list(length=None)
    
    return [NotificationResponse(**notification) for notification in notifications]

@api_router.put("/notifications/{notification_id}/read")
async def mark_notification_read(notification_id: str):
    result = await db.notifications.update_one(
        {"id": notification_id},
        {"$set": {"read": True}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}

# Rankings Routes
@api_router.get("/rankings/weekly")
async def get_weekly_rankings(limit: int = 10):
    # Get submissions from last 7 days
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    pipeline = [
        {"$match": {"created_at": {"$gte": week_ago}}},
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "username": {"$first": "$username"}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    rankings = await db.submissions.aggregate(pipeline).to_list(length=None)
    
    result = []
    for i, ranking in enumerate(rankings):
        result.append({
            "rank": i + 1,
            "user_id": ranking["_id"],
            "username": ranking["username"],
            "activity_count": ranking["count"],
            "period": "weekly"
        })
    
    return result

@api_router.get("/rankings/alltime")
async def get_alltime_rankings(limit: int = 10):
    pipeline = [
        {"$group": {"_id": "$user_id", "count": {"$sum": 1}, "username": {"$first": "$username"}}},
        {"$sort": {"count": -1}},
        {"$limit": limit}
    ]
    
    rankings = await db.submissions.aggregate(pipeline).to_list(length=None)
    
    result = []
    for i, ranking in enumerate(rankings):
        result.append({
            "rank": i + 1,
            "user_id": ranking["_id"],
            "username": ranking["username"],
            "activity_count": ranking["count"],
            "period": "all-time"
        })
    
    return result

# Global Challenge Routes
@api_router.get("/global-challenges/current")
async def get_current_global_challenge():
    # Get the most recent active global challenge
    challenge = await db.global_challenges.find_one(
        {"is_active": True}, 
        sort=[("created_at", -1)]
    )
    
    if not challenge:
        return {"challenge": None, "status": "no_active_challenge"}
    
    now = datetime.utcnow()
    
    # Parse datetime strings
    created_at = datetime.fromisoformat(challenge["created_at"].replace('Z', '+00:00')) if isinstance(challenge["created_at"], str) else challenge["created_at"]
    expires_at = datetime.fromisoformat(challenge["expires_at"].replace('Z', '+00:00')) if isinstance(challenge["expires_at"], str) else challenge["expires_at"]
    
    promptness_expired = now > (created_at + timedelta(minutes=challenge["promptness_window_minutes"]))
    
    return {
        "challenge": GlobalChallenge(**challenge),
        "promptness_expired": promptness_expired,
        "time_remaining": max(0, int((expires_at - now).total_seconds()))
    }

@api_router.post("/global-challenges")
async def create_global_challenge(
    prompt: str = Form(...),
    promptness_window_minutes: int = Form(5),
    duration_hours: int = Form(6)
):
    """Create a new global challenge (admin function)"""
    challenge_id = str(uuid.uuid4())
    now = datetime.utcnow()
    
    # Deactivate any existing challenges
    await db.global_challenges.update_many(
        {"is_active": True},
        {"$set": {"is_active": False}}
    )
    
    challenge_doc = {
        "id": challenge_id,
        "prompt": prompt,
        "created_at": now,
        "expires_at": now + timedelta(hours=duration_hours),
        "promptness_window_minutes": promptness_window_minutes,
        "is_active": True
    }
    
    await db.global_challenges.insert_one(challenge_doc)
    return GlobalChallenge(**challenge_doc)

@api_router.post("/global-submissions")
async def create_global_submission(
    challenge_id: str = Form(...),
    description: str = Form(...),
    user_id: str = Form(...),
    photo: Optional[UploadFile] = File(None)
):
    # Verify challenge exists and is active
    challenge = await db.global_challenges.find_one({"id": challenge_id, "is_active": True})
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found or expired")
    
    # Check if user already submitted for this challenge
    existing = await db.global_submissions.find_one({
        "challenge_id": challenge_id,
        "user_id": user_id
    })
    if existing:
        raise HTTPException(status_code=400, detail="Already submitted for this challenge")
    
    # Process photo if provided
    photo_data = None
    if photo:
        content = await photo.read()
        photo_data = base64.b64encode(content).decode('utf-8')
    
    # Get user info
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    submission_id = str(uuid.uuid4())
    submission_doc = {
        "id": submission_id,
        "user_id": user_id,
        "username": user["username"],
        "challenge_id": challenge_id,
        "challenge_prompt": challenge["prompt"],
        "description": description,
        "photo_data": photo_data,
        "created_at": datetime.utcnow(),
        "votes": 0,
        "comments": [],
        "reactions": {}
    }
    
    await db.global_submissions.insert_one(submission_doc)
    
    # Update user stats
    await db.users.update_one(
        {"id": user_id},
        {"$inc": {"stats.total_activities": 1, "stats.current_streak": 1}}
    )
    
    return GlobalSubmission(**submission_doc)

@api_router.get("/global-feed")
async def get_global_feed(
    user_id: str,
    challenge_id: Optional[str] = None,
    limit: int = 50,
    friends_only: bool = False
):
    # Check if user has submitted for the current challenge
    current_challenge = await db.global_challenges.find_one(
        {"is_active": True}, 
        sort=[("created_at", -1)]
    )
    
    if not current_challenge:
        return {"status": "no_active_challenge", "submissions": []}
    
    target_challenge_id = challenge_id or current_challenge["id"]
    
    # Check if user has submitted for this challenge
    user_submission = await db.global_submissions.find_one({
        "challenge_id": target_challenge_id,
        "user_id": user_id
    })
    
    if not user_submission:
        return {
            "status": "locked", 
            "challenge": GlobalChallenge(**current_challenge),
            "message": "Complete today's Global Challenge to unlock the feed!"
        }
    
    # Build query for submissions
    submissions_query = {"challenge_id": target_challenge_id}
    
    # If friends_only is enabled, filter to include only user's submissions and followed users' submissions
    if friends_only:
        # Get list of users the current user is following
        following_docs = await db.follows.find({"follower_id": user_id}).to_list(None)
        following_ids = [follow["following_id"] for follow in following_docs]
        
        # Include current user's own submissions and submissions from followed users
        following_ids.append(user_id)  # Include user's own submissions
        submissions_query["user_id"] = {"$in": following_ids}
    
    # Get submissions for this challenge
    submissions = await db.global_submissions.find(
        submissions_query
    ).sort("created_at", -1).limit(limit).to_list(length=None)
    
    # Get total participation count (always global, not filtered by friends)
    total_participants = await db.global_submissions.count_documents(
        {"challenge_id": target_challenge_id}
    )
    
    # Get friends participation count if friends_only is enabled
    friends_participants = 0
    if friends_only:
        friends_participants = await db.global_submissions.count_documents(
            submissions_query
        )
    
    return {
        "status": "unlocked",
        "challenge": GlobalChallenge(**current_challenge),
        "submissions": [GlobalSubmission(**sub) for sub in submissions],
        "total_participants": total_participants,
        "friends_participants": friends_participants if friends_only else total_participants,
        "user_submitted": True,
        "friends_only": friends_only
    }

@api_router.post("/global-submissions/{submission_id}/vote")
async def vote_global_submission(submission_id: str, user_id: str = Form(...)):
    # Check if submission exists
    submission = await db.global_submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Prevent self-voting
    if submission["user_id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own submission")
    
    # Check if user already voted (stored in separate votes collection)
    existing_vote = await db.global_votes.find_one({
        "submission_id": submission_id,
        "user_id": user_id
    })
    
    if existing_vote:
        # Remove vote
        await db.global_votes.delete_one({"_id": existing_vote["_id"]})
        await db.global_submissions.update_one(
            {"id": submission_id},
            {"$inc": {"votes": -1}}
        )
        return {"voted": False, "votes": submission["votes"] - 1}
    else:
        # Add vote
        vote_doc = {
            "id": str(uuid.uuid4()),
            "submission_id": submission_id,
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }
        await db.global_votes.insert_one(vote_doc)
        await db.global_submissions.update_one(
            {"id": submission_id},
            {"$inc": {"votes": 1}}
        )
        return {"voted": True, "votes": submission["votes"] + 1}

@api_router.post("/global-submissions/{submission_id}/comment")
async def comment_global_submission(
    submission_id: str, 
    comment: str = Form(...),
    user_id: str = Form(...)
):
    # Check if submission exists
    submission = await db.global_submissions.find_one({"id": submission_id})
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    
    # Get user info
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    comment_doc = {
        "id": str(uuid.uuid4()),
        "user_id": user_id,
        "username": user["username"],
        "comment": comment,
        "created_at": datetime.utcnow()
    }
    
    # Add comment to submission
    await db.global_submissions.update_one(
        {"id": submission_id},
        {"$push": {"comments": comment_doc}}
    )
    
    return {"message": "Comment added successfully", "comment": comment_doc}

# Global Activity System Routes

@api_router.post("/admin/initialize-activity-dataset")
async def initialize_activity_dataset():
    """Initialize the activity dataset with 300 activities (admin function)"""
    activities = [
        # Physical Activities (100 activities)
        ("Take a 15-minute walk", "Go for a brisk 15-minute walk around your neighborhood or a nearby park", "physical", "easy", 15),
        ("Do 10 push-ups", "Complete 10 push-ups with proper form. Modify as needed.", "physical", "easy", 5),
        ("Stretch for 5 minutes", "Do a gentle stretching routine focusing on major muscle groups", "physical", "easy", 5),
        ("Climb stairs for 5 minutes", "Use stairs in your building or find a public staircase", "physical", "easy", 5),
        ("Do 20 jumping jacks", "Perform 20 jumping jacks at a moderate pace", "physical", "easy", 3),
        ("Hold a plank for 30 seconds", "Maintain a plank position for 30 seconds with proper form", "physical", "easy", 2),
        ("Do 15 squats", "Complete 15 bodyweight squats with good form", "physical", "easy", 5),
        ("Take a 30-minute walk", "Enjoy a longer walk, perhaps exploring a new route", "physical", "medium", 30),
        ("Do a 10-minute yoga session", "Follow a short yoga routine or do some basic poses", "physical", "medium", 10),
        ("Complete 25 push-ups", "Challenge yourself with 25 push-ups, take breaks as needed", "physical", "medium", 8),
        
        # Wellness Activities (50 activities)
        ("Meditate for 10 minutes", "Sit quietly and practice mindfulness or guided meditation", "wellness", "easy", 10),
        ("Write in a gratitude journal", "Write down 3-5 things you're grateful for today", "wellness", "easy", 10),
        ("Practice deep breathing", "Do 5 minutes of focused breathing exercises", "wellness", "easy", 5),
        ("Take a cold shower", "End your shower with 30 seconds of cold water", "wellness", "easy", 5),
        ("Drink an extra glass of water", "Stay hydrated by drinking one additional glass of water", "wellness", "easy", 2),
        ("Step outside for fresh air", "Spend at least 5 minutes outdoors breathing fresh air", "wellness", "easy", 5),
        ("Listen to calming music", "Put on relaxing music and listen mindfully for 10 minutes", "wellness", "easy", 10),
        ("Do a digital detox hour", "Spend one hour without any screens or digital devices", "wellness", "medium", 60),
        ("Practice positive affirmations", "Say 5 positive affirmations about yourself", "wellness", "easy", 5),
        ("Take a relaxing bath", "Enjoy a warm, relaxing bath with minimal distractions", "wellness", "medium", 20),
        
        # Learning Activities (50 activities)
        ("Read for 20 minutes", "Read a book, article, or educational material", "learning", "easy", 20),
        ("Learn 5 new words", "Look up and memorize 5 words you don't know", "learning", "easy", 15),
        ("Watch an educational video", "Watch a 10-minute educational or documentary video", "learning", "easy", 10),
        ("Practice a new skill", "Spend 15 minutes practicing something you want to learn", "learning", "medium", 15),
        ("Write in a journal", "Reflect on your day or thoughts by writing for 10 minutes", "learning", "easy", 10),
        ("Listen to a podcast", "Listen to an educational or interesting podcast episode", "learning", "easy", 30),
        ("Learn basic phrases in a new language", "Use an app or website to learn 10 basic phrases", "learning", "medium", 20),
        ("Research a topic you're curious about", "Spend 20 minutes researching something interesting", "learning", "easy", 20),
        ("Practice mental math", "Do 10 mental math problems without a calculator", "learning", "easy", 10),
        ("Organize your digital files", "Spend 15 minutes organizing photos, documents, or emails", "learning", "easy", 15),
        
        # Social Activities (30 activities)
        ("Call a friend or family member", "Have a meaningful conversation with someone you care about", "social", "easy", 15),
        ("Send a thoughtful text", "Send an encouraging or appreciative message to someone", "social", "easy", 5),
        ("Write a thank you note", "Write a handwritten note expressing gratitude", "social", "easy", 10),
        ("Compliment a stranger", "Give a genuine compliment to someone you encounter", "social", "easy", 2),
        ("Help someone today", "Offer assistance to a friend, neighbor, or stranger", "social", "medium", 20),
        ("Share something positive on social media", "Post something uplifting or inspiring", "social", "easy", 5),
        ("Have lunch with a colleague", "Connect with a coworker over a meal or coffee", "social", "medium", 60),
        ("Join a community event", "Participate in a local event or gathering", "social", "medium", 120),
        ("Volunteer for 30 minutes", "Offer your time to help a cause you care about", "social", "medium", 30),
        ("Practice active listening", "Really focus on listening to someone without distractions", "social", "easy", 15),
        
        # Creative Activities (30 activities)
        ("Draw or sketch for 15 minutes", "Create art with whatever materials you have", "creative", "easy", 15),
        ("Write a short story or poem", "Express yourself through creative writing", "creative", "medium", 20),
        ("Take artistic photos", "Capture 5 creative or beautiful photos", "creative", "easy", 15),
        ("Try a new recipe", "Cook or bake something you've never made before", "creative", "medium", 45),
        ("Rearrange a room", "Change the layout or decor of a space in your home", "creative", "medium", 30),
        ("Create a playlist", "Curate music for a specific mood or activity", "creative", "easy", 15),
        ("Make something with your hands", "Craft, build, or create something tangible", "creative", "medium", 30),
        ("Sing or hum your favorite song", "Express yourself through music for 5 minutes", "creative", "easy", 5),
        ("Design something on paper", "Sketch an idea, plan, or design concept", "creative", "easy", 15),
        ("Write a letter to your future self", "Compose a message to yourself to read later", "creative", "easy", 15),
        
        # Productivity Activities (30 activities)
        ("Clean and organize one space", "Tidy up a desk, drawer, or small area", "productivity", "easy", 15),
        ("Plan tomorrow's schedule", "Spend 10 minutes planning your next day", "productivity", "easy", 10),
        ("Complete a task you've been postponing", "Tackle something you've been putting off", "productivity", "medium", 30),
        ("Declutter 10 items", "Choose 10 things to donate, recycle, or throw away", "productivity", "easy", 15),
        ("Update your calendar", "Review and organize your upcoming appointments", "productivity", "easy", 10),
        ("Backup important files", "Ensure your important data is safely backed up", "productivity", "easy", 20),
        ("Review your goals", "Spend 15 minutes reflecting on your personal goals", "productivity", "easy", 15),
        ("Prepare healthy snacks", "Pre-prepare some nutritious snacks for later", "productivity", "easy", 20),
        ("Update your resume or LinkedIn", "Improve your professional profile", "productivity", "medium", 30),
        ("Research something for work or life", "Look into something that could benefit you", "productivity", "easy", 20),
        
        # Extended list continues...
        ("Do 50 jumping jacks", "Challenge yourself with 50 jumping jacks", "physical", "medium", 5),
        ("Walk up 5 flights of stairs", "Find stairs and walk up 5 flights", "physical", "easy", 10),
        ("Do lunges for 2 minutes", "Perform alternating lunges for 2 minutes", "physical", "easy", 3),
        ("Try a new walking route", "Explore a different path in your neighborhood", "physical", "easy", 20),
        ("Do wall push-ups", "Complete 15 wall push-ups as a modified exercise", "physical", "easy", 5),
        ("Practice balance exercises", "Stand on one foot or do balance poses for 5 minutes", "physical", "easy", 5),
        ("Do calf raises", "Complete 20 calf raises", "physical", "easy", 3),
        ("Try dancing", "Dance to your favorite song for one full song", "physical", "easy", 4),
        ("Do mountain climbers", "Perform mountain climbers for 30 seconds", "physical", "medium", 2),
        ("Walk backwards for 2 minutes", "Carefully walk backwards for coordination", "physical", "easy", 3),
    ]
    
    # Add more activities to reach 300 total
    additional_activities = []
    base_activities = [
        ("Take a mindful walk", "Walk slowly and notice your surroundings", "wellness", "easy", 15),
        ("Do breathing exercises", "Practice 4-7-8 breathing technique", "wellness", "easy", 10),
        ("Organize your workspace", "Clean and arrange your work area", "productivity", "easy", 15),
        ("Learn something new online", "Spend 15 minutes learning on a free platform", "learning", "easy", 15),
        ("Practice gratitude", "Think of 5 things you're grateful for", "wellness", "easy", 5),
        ("Take photos of nature", "Capture 3 beautiful nature photos", "creative", "easy", 15),
        ("Do desk exercises", "Stretch and exercise at your desk", "physical", "easy", 10),
        ("Call someone you haven't talked to in a while", "Reconnect with an old friend", "social", "easy", 20),
        ("Try a new healthy snack", "Eat something nutritious you haven't tried", "wellness", "easy", 5),
        ("Write down your thoughts", "Free-write for 10 minutes", "creative", "easy", 10),
    ]
    
    # Multiply base activities to reach 300
    for i in range(20):
        for base_title, base_desc, category, difficulty, time in base_activities:
            activities.append((
                f"{base_title} (Variation {i+1})",
                f"{base_desc} - Daily variation #{i+1}",
                category,
                difficulty,
                time
            ))
    
    # Create activity documents
    activity_docs = []
    for i, (title, description, category, difficulty, time_minutes) in enumerate(activities[:300]):
        activity_doc = {
            "id": str(uuid.uuid4()),
            "title": title,
            "description": description,
            "category": category,
            "difficulty": difficulty,
            "estimated_time_minutes": time_minutes,
            "is_active": True,
            "created_at": datetime.utcnow()
        }
        activity_docs.append(activity_doc)
    
    # Clear existing activities and insert new ones
    await activity_dataset_collection.delete_many({})
    await activity_dataset_collection.insert_many(activity_docs)
    
    return {
        "success": True,
        "message": f"Initialized {len(activity_docs)} activities in the dataset",
        "count": len(activity_docs)
    }

@api_router.get("/daily-global-activity/current")
async def get_current_daily_global_activity():
    """Get today's global activity"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    daily_activity = await daily_global_activities_collection.find_one({"date": today})
    
    if not daily_activity:
        # Create today's activity if it doesn't exist
        await select_daily_global_activity(today)
        daily_activity = await daily_global_activities_collection.find_one({"date": today})
    
    if daily_activity:
        # Remove MongoDB ObjectId and convert datetime
        daily_activity.pop('_id', None)
        if 'selected_at' in daily_activity and hasattr(daily_activity['selected_at'], 'isoformat'):
            daily_activity['selected_at'] = daily_activity['selected_at'].isoformat()
        
        return daily_activity
    
    return {"error": "No daily activity available"}

async def select_daily_global_activity(date_str: str):
    """Select and schedule today's global activity"""
    import random
    
    # Check if activity already exists for this date
    existing = await daily_global_activities_collection.find_one({"date": date_str})
    if existing:
        return existing
    
    # Get random activity from dataset
    activities = await activity_dataset_collection.find({"is_active": True}).to_list(length=None)
    if not activities:
        raise HTTPException(status_code=500, detail="No activities in dataset")
    
    selected_activity = random.choice(activities)
    
    # Generate random time between 05:00 and 00:00 GMT (19 hour window)
    base_time = datetime.strptime(f"{date_str} 05:00:00", "%Y-%m-%d %H:%M:%S")
    random_hours = random.randint(0, 19)
    random_minutes = random.randint(0, 59)
    selected_time = base_time + timedelta(hours=random_hours, minutes=random_minutes)
    
    daily_activity_doc = {
        "id": str(uuid.uuid4()),
        "activity_id": selected_activity["id"],
        "date": date_str,
        "selected_at": selected_time,
        "activity_title": selected_activity["title"],
        "activity_description": selected_activity["description"],
        "is_active": True,
        "participant_count": 0
    }
    
    await daily_global_activities_collection.insert_one(daily_activity_doc)
    return daily_activity_doc

@api_router.post("/daily-global-activity/complete")
async def complete_daily_global_activity(
    user_id: str = Form(...),
    description: str = Form(...),
    photo: Optional[UploadFile] = File(None)
):
    """Submit completion of today's global activity"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Get today's activity
    daily_activity = await daily_global_activities_collection.find_one({"date": today})
    if not daily_activity:
        raise HTTPException(status_code=404, detail="No global activity for today")
    
    # Check if user already completed today's activity
    existing_completion = await global_activity_completions_collection.find_one({
        "activity_id": daily_activity["id"],
        "user_id": user_id
    })
    
    if existing_completion:
        raise HTTPException(status_code=400, detail="Already completed today's global activity")
    
    # Get user info
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Process photo if provided
    photo_url = None
    if photo:
        content = await photo.read()
        photo_url = f"data:image/jpeg;base64,{base64.b64encode(content).decode('utf-8')}"
    
    # Create completion record
    completion_doc = {
        "id": str(uuid.uuid4()),
        "activity_id": daily_activity["id"],
        "user_id": user_id,
        "username": user["username"],
        "description": description,
        "photo_url": photo_url,
        "completed_at": datetime.utcnow(),
        "is_friends_visible": True,  # Unlock friends feed for this user
        "votes": 0
    }
    
    await global_activity_completions_collection.insert_one(completion_doc)
    
    # Update participant count
    await daily_global_activities_collection.update_one(
        {"id": daily_activity["id"]},
        {"$inc": {"participant_count": 1}}
    )
    
    # Remove MongoDB ObjectId for response
    completion_doc.pop('_id', None)
    if 'completed_at' in completion_doc and hasattr(completion_doc['completed_at'], 'isoformat'):
        completion_doc['completed_at'] = completion_doc['completed_at'].isoformat()
    
    return {
        "success": True,
        "completion": completion_doc,
        "message": "Global activity completed! You can now view friends' submissions."
    }

@api_router.get("/daily-global-activity/feed")
async def get_daily_global_activity_feed(
    user_id: str,
    friends_only: bool = True,
    limit: int = 50
):
    """Get feed of global activity completions (friends or global)"""
    today = datetime.utcnow().strftime("%Y-%m-%d")
    
    # Get today's activity
    daily_activity = await daily_global_activities_collection.find_one({"date": today})
    if not daily_activity:
        return {"status": "no_activity", "message": "No global activity for today"}
    
    # Clean up daily_activity first
    daily_activity.pop('_id', None)
    if 'selected_at' in daily_activity and hasattr(daily_activity['selected_at'], 'isoformat'):
        daily_activity['selected_at'] = daily_activity['selected_at'].isoformat()
    
    # Check if user has completed today's activity
    user_completion = await global_activity_completions_collection.find_one({
        "activity_id": daily_activity["id"],
        "user_id": user_id
    })
    
    if not user_completion:
        return {
            "status": "locked",
            "activity": daily_activity,
            "message": "Submit your activity to view friends' posts"
        }
    
    # Build query for completions
    completions_query = {"activity_id": daily_activity["id"]}
    
    if friends_only:
        # Get list of users the current user is following
        following_docs = await db.follows.find({"follower_id": user_id}).to_list(None)
        following_ids = [follow["following_id"] for follow in following_docs]
        
        if following_ids:
            completions_query["user_id"] = {"$in": following_ids}
        else:
            # No friends, return empty feed
            return {
                "status": "unlocked",
                "activity": daily_activity,
                "completions": [],
                "friends_count": 0,
                "message": "No friends have completed this activity yet"
            }
    
    # Get completions
    completions = await global_activity_completions_collection.find(
        completions_query
    ).sort("completed_at", -1).limit(limit).to_list(length=None)
    
    # Clean up MongoDB data
    for completion in completions:
        completion.pop('_id', None)
        if 'completed_at' in completion and hasattr(completion['completed_at'], 'isoformat'):
            completion['completed_at'] = completion['completed_at'].isoformat()
    
    return {
        "status": "unlocked",
        "activity": daily_activity,
        "completions": completions,
        "friends_count": len(completions),
        "user_has_completed": True
    }

@api_router.post("/groups/{group_id}/complete-daily-activity")
async def complete_group_daily_activity(
    group_id: str,
    user_id: str = Form(...),
    description: str = Form(...),
    photo: Optional[UploadFile] = File(None)
):
    """Submit completion of today's group activity"""
    # Get group info
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id not in group["members"]:
        raise HTTPException(status_code=403, detail="User not in group")
    
    # Get today's revealed activity for this group
    current_day_activity = group.get("current_day_activity")
    if not current_day_activity:
        raise HTTPException(status_code=400, detail="No activity revealed for today")
    
    # Check if user already completed today's group activity
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    existing_completion = await db.daily_activity_completions.find_one({
        "group_id": group_id,
        "completed_by": user_id,
        "completed_at": {"$gte": today_start, "$lt": today_end}
    })
    
    if existing_completion:
        raise HTTPException(status_code=400, detail="Already completed today's group activity")
    
    # Get user info
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Process photo if provided
    photo_url = None
    if photo:
        content = await photo.read()
        photo_url = f"data:image/jpeg;base64,{base64.b64encode(content).decode('utf-8')}"
    
    # Calculate points (3 points for 1st, 2 for 2nd, 1 for 3rd+)
    completion_count = await db.daily_activity_completions.count_documents({
        "group_id": group_id,
        "activity_id": current_day_activity.get("activity_id"),
        "completed_at": {"$gte": today_start, "$lt": today_end}
    })
    
    if completion_count == 0:
        points_earned = 3
    elif completion_count == 1:
        points_earned = 2
    else:
        points_earned = 1
    
    # Create completion record
    completion_doc = {
        "id": str(uuid.uuid4()),
        "group_id": group_id,
        "activity_id": current_day_activity.get("activity_id"),
        "completed_by": user_id,
        "completion_description": description,
        "photo_url": photo_url,
        "points_earned": points_earned,
        "completed_at": datetime.utcnow(),
        "day_number": current_day_activity.get("day_number", 1)
    }
    
    await db.daily_activity_completions.insert_one(completion_doc)
    
    # Update user's points in the group
    current_points = group.get("current_week_points", {}).get(user_id, 0)
    new_points = current_points + points_earned
    
    await db.groups.update_one(
        {"id": group_id},
        {"$set": {f"current_week_points.{user_id}": new_points}}
    )
    
    # Remove MongoDB ObjectId for response
    completion_doc.pop('_id', None)
    if 'completed_at' in completion_doc and hasattr(completion_doc['completed_at'], 'isoformat'):
        completion_doc['completed_at'] = completion_doc['completed_at'].isoformat()
    
    return {
        "success": True,
        "completion": completion_doc,
        "points_earned": points_earned,
        "message": f"Group activity completed! You earned {points_earned} points. You can now view members' posts."
    }

@api_router.get("/groups/{group_id}/daily-activity-feed")
async def get_group_daily_activity_feed(
    group_id: str,
    user_id: str,
    limit: int = 50
):
    """Get feed of today's group activity completions"""
    # Get group info
    group = await db.groups.find_one({"id": group_id})
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    if user_id not in group["members"]:
        raise HTTPException(status_code=403, detail="User not in group")
    
    # Get today's revealed activity for this group
    current_day_activity = group.get("current_day_activity")
    if not current_day_activity:
        return {
            "status": "no_activity",
            "message": "No activity revealed for today"
        }
    
    # Check if user has completed today's group activity
    # For now, we'll use a simple approach - check if user has any completion for today
    # In a full implementation, you'd track daily completions separately
    
    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    
    user_completion = await db.daily_activity_completions.find_one({
        "group_id": group_id,
        "completed_by": user_id,
        "completed_at": {"$gte": today_start, "$lt": today_end}
    })
    
    if not user_completion:
        return {
            "status": "locked",
            "activity": current_day_activity,
            "message": "Submit your group activity to view members' posts"
        }
    
    # Get group members' completions for today
    group_completions = await db.daily_activity_completions.find({
        "group_id": group_id,
        "completed_at": {"$gte": today_start, "$lt": today_end}
    }).sort("completed_at", -1).limit(limit).to_list(length=None)
    
    # Get user info for each completion
    for completion in group_completions:
        completion.pop('_id', None)
        if 'completed_at' in completion and hasattr(completion['completed_at'], 'isoformat'):
            completion['completed_at'] = completion['completed_at'].isoformat()
        
        # Get user info
        user_info = await db.users.find_one({"id": completion["completed_by"]})
        if user_info:
            completion["user_info"] = {
                "username": user_info["username"],
                "full_name": user_info["full_name"],
                "avatar_color": user_info["avatar_color"]
            }
    
    return {
        "status": "unlocked",
        "activity": current_day_activity,
        "completions": group_completions,
        "group_name": group["name"],
        "members_completed": len(group_completions),
        "user_has_completed": True
    }

# Achievement Routes
@api_router.get("/achievements/{user_id}", response_model=List[Achievement])
async def get_user_achievements(user_id: str):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Calculate achievements based on user stats
    achievements = []
    stats = user.get("stats", {})
    
    if stats.get("total_activities", 0) >= 1:
        achievements.append({
            "id": "first_activity",
            "name": "First Step",
            "description": "Completed your first activity",
            "icon": "🎯",
            "unlocked_at": datetime.utcnow()
        })
    
    if stats.get("total_activities", 0) >= 10:
        achievements.append({
            "id": "activity_master",
            "name": "Activity Master",
            "description": "Completed 10 activities",
            "icon": "🏆",
            "unlocked_at": datetime.utcnow()
        })
    
    if stats.get("total_groups_joined", 0) >= 1:
        achievements.append({
            "id": "team_player",
            "name": "Team Player",
            "description": "Joined your first group",
            "icon": "🤝",
            "unlocked_at": datetime.utcnow()
        })
    
    if stats.get("current_streak", 0) >= 7:
        achievements.append({
            "id": "week_warrior",
            "name": "Week Warrior",
            "description": "7 day activity streak",
            "icon": "🔥",
            "unlocked_at": datetime.utcnow()
        })
    
    return achievements

# Include the router in the main app
app.include_router(api_router)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()

# NEW: Follow/Unfollow Endpoints
@app.post("/api/users/{user_id}/follow")
async def follow_user(
    user_id: str,
    follower_id: str = Form(...),
):
    """Follow a user"""
    try:
        # Check if users exist
        user = await users_collection.find_one({"id": user_id})
        follower = await users_collection.find_one({"id": follower_id})
        
        if not user or not follower:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user_id == follower_id:
            raise HTTPException(status_code=400, detail="Cannot follow yourself")
        
        # Check if already following
        existing_follow = await follows_collection.find_one({
            "follower_id": follower_id,
            "following_id": user_id
        })
        
        if existing_follow:
            raise HTTPException(status_code=400, detail="Already following this user")
        
        # Create follow relationship
        follow_data = {
            "id": str(uuid.uuid4()),
            "follower_id": follower_id,
            "following_id": user_id,
            "created_at": datetime.utcnow().isoformat()
        }
        
        await follows_collection.insert_one(follow_data)
        
        # Create notification for the followed user
        notification_data = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": "new_follower",
            "message": f"{follower['username']} started following you!",
            "read": False,
            "created_at": datetime.utcnow().isoformat()
        }
        await notifications_collection.insert_one(notification_data)
        
        return {"success": True, "message": "Successfully followed user"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/unfollow")
async def unfollow_user(
    user_id: str,
    follower_id: str = Form(...),
):
    """Unfollow a user"""
    try:
        # Remove follow relationship
        result = await follows_collection.delete_one({
            "follower_id": follower_id,
            "following_id": user_id
        })
        
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Follow relationship not found")
        
        return {"success": True, "message": "Successfully unfollowed user"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/following")
async def get_following(user_id: str):
    """Get list of users that user_id is following"""
    try:
        follows = await follows_collection.find({"follower_id": user_id}).to_list(None)
        following_ids = [follow["following_id"] for follow in follows]
        
        if not following_ids:
            return []
        
        # Get user details for each followed user
        following_users = await users_collection.find(
            {"id": {"$in": following_ids}},
            {"_id": 0, "password": 0, "email": 0}
        ).to_list(None)
        
        return following_users
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/followers")
async def get_followers(user_id: str):
    """Get list of users following user_id"""
    try:
        follows = await follows_collection.find({"following_id": user_id}).to_list(None)
        follower_ids = [follow["follower_id"] for follow in follows]
        
        if not follower_ids:
            return []
        
        # Get user details for each follower
        followers = await users_collection.find(
            {"id": {"$in": follower_ids}},
            {"_id": 0, "password": 0, "email": 0}
        ).to_list(None)
        
        return followers
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/follow-status/{target_user_id}")
async def get_follow_status(user_id: str, target_user_id: str):
    """Check if user_id is following target_user_id"""
    try:
        follow = await follows_collection.find_one({
            "follower_id": user_id,
            "following_id": target_user_id
        })
        
        return {"is_following": follow is not None}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/global-challenges")
async def create_scheduled_challenge(
    prompt: str = Form(...),
    start_time: Optional[str] = Form(None),  # ISO format datetime
    promptness_window_minutes: int = Form(5),
    duration_hours: int = Form(6),
    send_notifications: bool = Form(True)  # Whether to send notifications to users
):
    """Create a global challenge (admin function)"""
    try:
        challenge_id = str(uuid.uuid4())
        now = datetime.now()
        
        # Parse start time or use now
        if start_time:
            start_datetime = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        else:
            start_datetime = now
            
        # Calculate expiration time
        expires_at = start_datetime + timedelta(hours=duration_hours)
        
        challenge_data = {
            "id": challenge_id,
            "prompt": prompt,
            "created_at": start_datetime.isoformat(),
            "expires_at": expires_at.isoformat(),
            "promptness_window_minutes": promptness_window_minutes,
            "is_active": start_datetime <= now <= expires_at
        }
        
        global_challenges_collection.insert_one(challenge_data)
        
        # Deactivate any other active challenges
        if challenge_data["is_active"]:
            global_challenges_collection.update_many(
                {"id": {"$ne": challenge_id}, "is_active": True},
                {"$set": {"is_active": False}}
            )
        
        # Send notifications to all users about the new global challenge
        if send_notifications and challenge_data["is_active"]:
            send_global_challenge_notifications(challenge_id, prompt)
        
        # Remove MongoDB ObjectId for JSON response
        challenge_data.pop('_id', None)
        
        return {"success": True, "challenge": challenge_data, "message": "Challenge created successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def send_global_challenge_notifications(challenge_id: str, prompt: str):
    """Send notifications to all users about a new global challenge"""
    try:
        # Get all active users (you might want to limit this or batch it for scale)
        users = list(users_collection.find({}, {"id": 1, "username": 1}).limit(1000))
        
        notifications_to_insert = []
        for user in users:
            notification_data = {
                "id": str(uuid.uuid4()),
                "user_id": user["id"],
                "type": "global_challenge_drop",
                "challenge_id": challenge_id,  # Important for deep linking
                "message": f"🌍 New Global Challenge: {prompt[:50]}{'...' if len(prompt) > 50 else ''}",
                "title": "New Global Challenge!",
                "read": False,
                "created_at": datetime.now().isoformat(),
                "action_url": "/feed",  # Deep link to home/today screen
                "metadata": {
                    "challenge_id": challenge_id,
                    "challenge_prompt": prompt,
                    "notification_category": "global_challenge"
                }
            }
            notifications_to_insert.append(notification_data)
        
        # Batch insert notifications
        if notifications_to_insert:
            notifications_collection.insert_many(notifications_to_insert)
            print(f"Sent {len(notifications_to_insert)} global challenge notifications")
        
    except Exception as e:
        print(f"Failed to send global challenge notifications: {e}")

# Enhanced notification endpoint with metadata
@app.get("/api/notifications/{user_id}")
def get_user_notifications(user_id: str, limit: int = 50):
    """Get notifications for a user with enhanced metadata"""
    try:
        notifications = list(notifications_collection.find(
            {"user_id": user_id}
        ).sort("created_at", -1).limit(limit))
        
        # Remove MongoDB ObjectId
        for notification in notifications:
            notification.pop('_id', None)
        
        return notifications
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/notifications/{notification_id}/read")
def mark_notification_read(notification_id: str):
    """Mark a notification as read"""
    try:
        result = notifications_collection.update_one(
            {"id": notification_id},
            {"$set": {"read": True, "read_at": datetime.now().isoformat()}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Notification not found")
        
        return {"success": True, "message": "Notification marked as read"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/admin/global-challenges")
async def list_all_challenges():
    """List all global challenges (admin function)"""
    try:
        challenges = list(global_challenges_collection.find({}, {"_id": 0}).sort("created_at", -1))
        return challenges
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/global-challenges/{challenge_id}/activate")
def activate_challenge(challenge_id: str):
    """Manually activate a challenge (admin function)"""
    try:
        # Deactivate all other challenges
        global_challenges_collection.update_many(
            {"is_active": True},
            {"$set": {"is_active": False}}
        )
        
        # Activate the specified challenge
        result = global_challenges_collection.update_one(
            {"id": challenge_id},
            {"$set": {"is_active": True}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        return {"success": True, "message": "Challenge activated"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/global-challenges/auto-schedule")
def auto_schedule_challenges():
    """Auto-schedule predefined challenges for the next week"""
    try:
        # Predefined challenge prompts
        challenge_prompts = [
            "Take a photo of your morning workout setup! 💪",
            "Share a picture of your healthy meal today! 🥗",
            "Show us your favorite exercise spot! 🏃‍♀️",
            "Capture a moment of stretching or yoga! 🧘‍♀️",
            "Photo of you staying hydrated! 💧",
            "Share your post-workout feeling! 😊",
            "Take a photo of something that motivates you to stay active! 🔥",
            "Show us your workout gear! 👟",
            "Capture yourself trying a new activity! 🆕",
            "Photo of you enjoying movement outdoors! 🌳"
        ]
        
        now = datetime.now()
        created_challenges = []
        
        # Create challenges for the next 7 days (one per day)
        for i in range(7):
            start_time = now + timedelta(days=i, hours=6)  # Start at 6 AM each day
            prompt = challenge_prompts[i % len(challenge_prompts)]
            
            challenge_id = str(uuid.uuid4())
            expires_at = start_time + timedelta(hours=18)  # 18-hour duration
            
            challenge_data = {
                "id": challenge_id,
                "prompt": prompt,
                "created_at": start_time.isoformat(),
                "expires_at": expires_at.isoformat(),
                "promptness_window_minutes": 5,
                "is_active": False,  # Will be activated when the time comes
                "auto_scheduled": True
            }
            
            global_challenges_collection.insert_one(challenge_data)
            created_challenges.append({k: v for k, v in challenge_data.items() if k != '_id'})  # Remove ObjectId
        
        return {
            "success": True, 
            "challenges_created": len(created_challenges),
            "challenges": created_challenges,
            "message": f"Successfully scheduled {len(created_challenges)} challenges"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/admin/update-challenge-status")
async def update_challenge_status():
    """Update challenge status based on current time (called periodically)"""
    try:
        now = datetime.now()
        now_iso = now.isoformat()
        
        # Deactivate expired challenges
        expired_result = global_challenges_collection.update_many(
            {
                "is_active": True,
                "expires_at": {"$lt": now_iso}
            },
            {"$set": {"is_active": False}}
        )
        
        # Activate challenges that should start now
        activated_result = global_challenges_collection.update_many(
            {
                "is_active": False,
                "created_at": {"$lte": now_iso},
                "expires_at": {"$gt": now_iso}
            },
            {"$set": {"is_active": True}}
        )
        
        # Get current active challenge
        active_challenge = global_challenges_collection.find_one({"is_active": True})
        
        return {
            "success": True,
            "expired_challenges": expired_result.modified_count,
            "activated_challenges": activated_result.modified_count,
            "current_active_challenge": active_challenge["prompt"] if active_challenge else None,
            "timestamp": now_iso
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# NEW: Challenge Statistics Endpoint
@app.get("/api/global-challenges/{challenge_id}/stats")
async def get_challenge_stats(challenge_id: str):
    """Get statistics for a specific challenge"""
    try:
        challenge = global_challenges_collection.find_one({"id": challenge_id})
        if not challenge:
            raise HTTPException(status_code=404, detail="Challenge not found")
        
        # Get submission stats
        total_submissions = global_submissions_collection.count_documents({"challenge_id": challenge_id})
        total_votes = global_votes_collection.count_documents({"submission_id": {"$in": [
            sub["id"] for sub in global_submissions_collection.find({"challenge_id": challenge_id}, {"id": 1})
        ]}})
        
        # Get top submissions
        top_submissions = list(global_submissions_collection.find(
            {"challenge_id": challenge_id}
        ).sort("votes", -1).limit(3))
        
        return {
            "challenge": challenge,
            "stats": {
                "total_submissions": total_submissions,
                "total_votes": total_votes,
                "participation_rate": f"{total_submissions} users participated",
                "top_submissions": top_submissions
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
