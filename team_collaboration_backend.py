# team_collaboration_backend.py
# Team Collaboration API Endpoints for Contact Book Phase 2

from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from pydantic import BaseModel

# Import your existing modules
from database import get_db
from models import TeamInvitation, ContactListPermission, ContactList, User, PermissionLevel
from auth import get_current_active_user, check_list_permission, get_user_by_email

# Pydantic models for team management
class InviteUserRequest(BaseModel):
    email: str
    permission_level: str  # "owner", "editor", "viewer"
    message: Optional[str] = None

class TeamMemberResponse(BaseModel):
    user_id: str
    username: str
    full_name: str
    email: str
    permission_level: str
    added_at: str
    can_manage: bool  # Can current user manage this member's permissions

class InvitationResponse(BaseModel):
    id: str
    email: str
    permission_level: str
    is_accepted: bool
    is_expired: bool
    created_at: str
    expires_at: str
    invited_by: str

class UpdatePermissionRequest(BaseModel):
    user_id: str
    permission_level: str

# Team management router
team_router = APIRouter(prefix="/api/team", tags=["Team Management"])

@team_router.get("/lists/{list_id}/members", response_model=List[TeamMemberResponse])
async def get_list_members(
    list_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get all members of a contact list"""
    # Check if user has access to this list
    if not check_list_permission(db, current_user, list_id, PermissionLevel.VIEWER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this contact list"
        )
    
    # Check if current user can manage permissions (owner level)
    can_manage = check_list_permission(db, current_user, list_id, PermissionLevel.OWNER)
    
    # Get all permissions for this list
    permissions = db.query(ContactListPermission).filter(
        ContactListPermission.contact_list_id == list_id
    ).all()
    
    members = []
    for perm in permissions:
        members.append(TeamMemberResponse(
            user_id=str(perm.user.id),
            username=perm.user.username,
            full_name=perm.user.full_name,
            email=perm.user.email,
            permission_level=perm.permission_level.value,
            added_at=perm.created_at.isoformat(),
            can_manage=can_manage and str(perm.user.id) != str(current_user.id)  # Can't manage self
        ))
    
    return members

@team_router.post("/lists/{list_id}/invite")
async def invite_user_to_list(
    list_id: str,
    invite_request: InviteUserRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Invite a user to a contact list"""
    # Check if user has owner permission to invite others
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can invite new members"
        )
    
    # Validate permission level
    try:
        permission_level = PermissionLevel(invite_request.permission_level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission level. Must be 'owner', 'editor', or 'viewer'"
        )
    
    # Check if contact list exists
    contact_list = db.query(ContactList).filter(ContactList.id == list_id).first()
    if not contact_list:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contact list not found"
        )
    
    # Check if user already has access
    existing_user = get_user_by_email(db, invite_request.email)
    if existing_user:
        existing_permission = db.query(ContactListPermission).filter(
            and_(
                ContactListPermission.user_id == existing_user.id,
                ContactListPermission.contact_list_id == list_id
            )
        ).first()
        
        if existing_permission:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has access to this contact list"
            )
    
    # Check if there's already a pending invitation
    existing_invitation = db.query(TeamInvitation).filter(
        and_(
            TeamInvitation.email == invite_request.email,
            TeamInvitation.contact_list_id == list_id,
            TeamInvitation.is_accepted == False,
            TeamInvitation.is_expired == False
        )
    ).first()
    
    if existing_invitation:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation already sent to this email"
        )
    
    # Create invitation
    invitation = TeamInvitation(
        email=invite_request.email,
        contact_list_id=list_id,
        permission_level=permission_level,
        invited_by=current_user.id,
        expires_at=datetime.utcnow() + timedelta(days=7),  # 7 days to accept
        created_at=datetime.utcnow()
    )
    
    db.add(invitation)
    db.commit()
    db.refresh(invitation)
    
    # If user exists, auto-accept and grant permission
    if existing_user:
        # Auto-accept for existing users
        invitation.is_accepted = True
        invitation.accepted_by = existing_user.id
        
        # Create permission
        permission = ContactListPermission(
            user_id=existing_user.id,
            contact_list_id=list_id,
            permission_level=permission_level,
            created_by=current_user.id,
            created_at=datetime.utcnow()
        )
        db.add(permission)
        db.commit()
        
        return {
            "message": f"User {invite_request.email} has been added to the contact list",
            "auto_accepted": True,
            "invitation_id": str(invitation.id)
        }
    
    return {
        "message": f"Invitation sent to {invite_request.email}",
        "auto_accepted": False,
        "invitation_id": str(invitation.id),
        "expires_at": invitation.expires_at.isoformat()
    }

@team_router.get("/lists/{list_id}/invitations", response_model=List[InvitationResponse])
async def get_pending_invitations(
    list_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Get pending invitations for a contact list"""
    # Check if user has owner permission
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can view invitations"
        )
    
    invitations = db.query(TeamInvitation).filter(
        TeamInvitation.contact_list_id == list_id
    ).all()
    
    result = []
    for inv in invitations:
        result.append(InvitationResponse(
            id=str(inv.id),
            email=inv.email,
            permission_level=inv.permission_level.value,
            is_accepted=inv.is_accepted,
            is_expired=inv.is_expired or inv.expires_at < datetime.utcnow(),
            created_at=inv.created_at.isoformat(),
            expires_at=inv.expires_at.isoformat(),
            invited_by=inv.invited_by_user.full_name
        ))
    
    return result

@team_router.put("/lists/{list_id}/members/{user_id}/permission")
async def update_member_permission(
    list_id: str,
    user_id: str,
    permission_request: UpdatePermissionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update a team member's permission level"""
    # Check if user has owner permission
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can modify permissions"
        )
    
    # Can't modify own permissions
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify your own permissions"
        )
    
    # Validate permission level
    try:
        new_permission = PermissionLevel(permission_request.permission_level)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid permission level"
        )
    
    # Find existing permission
    permission = db.query(ContactListPermission).filter(
        and_(
            ContactListPermission.user_id == user_id,
            ContactListPermission.contact_list_id == list_id
        )
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have access to this contact list"
        )
    
    # Update permission
    permission.permission_level = new_permission
    db.commit()
    
    return {"message": "Permission updated successfully"}

@team_router.delete("/lists/{list_id}/members/{user_id}")
async def remove_member(
    list_id: str,
    user_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove a member from a contact list"""
    # Check if user has owner permission
    if not check_list_permission(db, current_user, list_id, PermissionLevel.OWNER):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only list owners can remove members"
        )
    
    # Can't remove self
    if str(current_user.id) == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove yourself from the list"
        )
    
    # Find and remove permission
    permission = db.query(ContactListPermission).filter(
        and_(
            ContactListPermission.user_id == user_id,
            ContactListPermission.contact_list_id == list_id
        )
    ).first()
    
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User does not have access to this contact list"
        )
    
    db.delete(permission)
    db.commit()
    
    return {"message": "Member removed successfully"}