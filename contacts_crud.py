"""
CRUD operations for contacts
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc
from typing import List, Optional, Dict, Any
from models import Contact, ContactList, ContactFavorite, ContactCategory
from datetime import datetime
import uuid

class ContactListCRUD:
    """CRUD operations for contact lists"""
    
    @staticmethod
    def create_list(db: Session, name: str, description: str = None, created_by: str = None) -> ContactList:
        """Create a new contact list"""
        contact_list = ContactList(
            name=name,
            description=description,
            created_by=created_by
        )
        db.add(contact_list)
        db.commit()
        db.refresh(contact_list)
        return contact_list
    
    @staticmethod
    def get_lists(db: Session, skip: int = 0, limit: int = 100) -> List[ContactList]:
        """Get all contact lists"""
        return db.query(ContactList).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_list_by_id(db: Session, list_id: str) -> Optional[ContactList]:
        """Get a contact list by ID"""
        return db.query(ContactList).filter(ContactList.id == list_id).first()
    
    @staticmethod
    def get_or_create_default_list(db: Session) -> ContactList:
        """Get or create the default contact list"""
        default_list = db.query(ContactList).filter(ContactList.is_default == True).first()
        if not default_list:
            default_list = ContactList(
                name="Default Contacts",
                description="Default contact list for property management",
                is_default=True
            )
            db.add(default_list)
            db.commit()
            db.refresh(default_list)
        return default_list

class ContactCRUD:
    """CRUD operations for contacts"""
    
    @staticmethod
    def create_contact(db: Session, contact_data: Dict[str, Any], contact_list_id: str = None) -> Contact:
        """Create a new contact with proper date handling"""
        if not contact_list_id:
            # Use default list if none specified
            default_list = ContactListCRUD.get_or_create_default_list(db)
            contact_list_id = default_list.id
        
        # Handle last_contact_date properly
        last_contact_date = contact_data.get("last_contact_date")
        if last_contact_date:
            if isinstance(last_contact_date, str):
                # Parse ISO date string
                try:
                    parsed_date = datetime.fromisoformat(last_contact_date.replace('Z', '+00:00'))
                except ValueError:
                    # If parsing fails, try just the date part
                    try:
                        parsed_date = datetime.strptime(last_contact_date.split('T')[0], '%Y-%m-%d')
                    except ValueError:
                        # If all parsing fails, use current date
                        parsed_date = datetime.utcnow()
            else:
                parsed_date = last_contact_date
        else:
            # Default to current date if not provided
            parsed_date = datetime.utcnow()
            
        contact = Contact(
            name=contact_data["name"],
            email=contact_data["email"],
            phone=contact_data["phone"],
            company=contact_data["company"],
            category=ContactCategory(contact_data.get("category", "other")),
            address=contact_data.get("address"),
            notes=contact_data.get("notes"),
            contact_list_id=contact_list_id,
            last_contact_date=parsed_date
        )
        db.add(contact)
        db.commit()
        db.refresh(contact)
        return contact
    
    @staticmethod
    def get_contacts(
        db: Session, 
        contact_list_id: str = None,
        category: str = None,
        search: str = None,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Contact]:
        """Get contacts with optional filtering"""
        query = db.query(Contact)
        
        if contact_list_id:
            query = query.filter(Contact.contact_list_id == contact_list_id)
        
        if category and category != "all":
            query = query.filter(Contact.category == ContactCategory(category))
        
        if search:
            search_filter = or_(
                Contact.name.ilike(f"%{search}%"),
                Contact.email.ilike(f"%{search}%"),
                Contact.company.ilike(f"%{search}%"),
                Contact.phone.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        return query.order_by(Contact.name).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_contact_by_id(db: Session, contact_id: str) -> Optional[Contact]:
        """Get a contact by ID"""
        return db.query(Contact).filter(Contact.id == contact_id).first()
    
    @staticmethod
    def update_contact(db: Session, contact_id: str, contact_data: Dict[str, Any]) -> Optional[Contact]:
        """Update a contact"""
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return None
            
        for key, value in contact_data.items():
            if key == "category":
                value = ContactCategory(value)
            elif key == "last_contact_date":
                value = datetime.fromisoformat(value) if isinstance(value, str) else value
            setattr(contact, key, value)
        
        contact.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(contact)
        return contact
    
    @staticmethod
    def delete_contact(db: Session, contact_id: str) -> bool:
        """Delete a contact"""
        contact = db.query(Contact).filter(Contact.id == contact_id).first()
        if not contact:
            return False
        
        db.delete(contact)
        db.commit()
        return True
    
    @staticmethod
    def get_contact_counts_by_category(db: Session, contact_list_id: str = None) -> Dict[str, int]:
        """Get contact counts grouped by category"""
        query = db.query(Contact.category, func.count(Contact.id))
        
        if contact_list_id:
            query = query.filter(Contact.contact_list_id == contact_list_id)
        
        results = query.group_by(Contact.category).all()
        
        counts = {category.value: 0 for category in ContactCategory}
        for category, count in results:
            counts[category.value] = count
        
        return counts

class ContactFavoriteCRUD:
    """CRUD operations for contact favorites"""
    
    @staticmethod
    def toggle_favorite(db: Session, contact_id: str, session_id: str) -> bool:
        """Toggle favorite status for a contact"""
        favorite = db.query(ContactFavorite).filter(
            and_(
                ContactFavorite.contact_id == contact_id,
                ContactFavorite.session_id == session_id
            )
        ).first()
        
        if favorite:
            # Remove from favorites
            db.delete(favorite)
            db.commit()
            return False
        else:
            # Add to favorites
            favorite = ContactFavorite(
                contact_id=contact_id,
                session_id=session_id
            )
            db.add(favorite)
            db.commit()
            return True
    
    @staticmethod
    def get_favorites(db: Session, session_id: str) -> List[str]:
        """Get list of favorite contact IDs for a session"""
        favorites = db.query(ContactFavorite.contact_id).filter(
            ContactFavorite.session_id == session_id
        ).all()
        return [str(fav.contact_id) for fav in favorites]
    
    @staticmethod
    def is_favorite(db: Session, contact_id: str, session_id: str) -> bool:
        """Check if a contact is favorited"""
        favorite = db.query(ContactFavorite).filter(
            and_(
                ContactFavorite.contact_id == contact_id,
                ContactFavorite.session_id == session_id
            )
        ).first()
        return favorite is not None