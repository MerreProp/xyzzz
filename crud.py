"""
Database CRUD operations for HMO Analyser
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_
from models import Property, PropertyAnalysis, AnalysisTask, AnalyticsLog
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timedelta

class PropertyCRUD:
    @staticmethod
    def create_property(db: Session, url: str, **kwargs) -> Property:
        """Create a new property record"""
        # For SQLite, ensure ID is string if provided
        if 'id' in kwargs:
            if isinstance(kwargs['id'], uuid.UUID):
                kwargs['id'] = str(kwargs['id'])
            
        property_obj = Property(url=url, **kwargs)
        db.add(property_obj)
        db.commit()
        db.refresh(property_obj)
        return property_obj
    
    @staticmethod
    def get_property_by_url(db: Session, url: str) -> Optional[Property]:
        """Get property by URL"""
        return db.query(Property).filter(Property.url == url).first()
    
    @staticmethod
    def get_property_by_id(db: Session, property_id) -> Optional[Property]:
        """Get property by ID - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        return db.query(Property).filter(Property.id == property_id).first()
    
    @staticmethod
    def get_all_properties(db: Session, limit: int = 100, offset: int = 0) -> List[Property]:
        """Get all properties with pagination"""
        return (db.query(Property)
                .order_by(desc(Property.created_at))
                .limit(limit)
                .offset(offset)
                .all())
    
    @staticmethod
    def search_properties(
        db: Session, 
        search_term: str = None,
        min_income: float = None,
        max_income: float = None,
        min_rooms: int = None,
        bills_included: str = None,
        meets_requirements: str = None,
        limit: int = 100
    ) -> List[Property]:
        """Search properties with filters"""
        query = db.query(Property).join(PropertyAnalysis)
        
        if search_term:
            search_filter = or_(
                Property.address.ilike(f"%{search_term}%"),
                Property.postcode.ilike(f"%{search_term}%"),
                PropertyAnalysis.advertiser_name.ilike(f"%{search_term}%")
            )
            query = query.filter(search_filter)
        
        if min_income is not None:
            query = query.filter(PropertyAnalysis.monthly_income >= min_income)
        
        if max_income is not None:
            query = query.filter(PropertyAnalysis.monthly_income <= max_income)
        
        if min_rooms is not None:
            query = query.filter(PropertyAnalysis.total_rooms >= min_rooms)
        
        if bills_included:
            query = query.filter(PropertyAnalysis.bills_included.ilike(f"%{bills_included}%"))
        
        if meets_requirements:
            query = query.filter(PropertyAnalysis.meets_requirements.ilike(f"%{meets_requirements}%"))
        
        return query.order_by(desc(Property.created_at)).limit(limit).all()
    
    @staticmethod
    def update_property(db: Session, property_id, **kwargs) -> Optional[Property]:
        """Update property record - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if property_obj:
            for key, value in kwargs.items():
                setattr(property_obj, key, value)
            property_obj.updated_at = datetime.utcnow()
            db.commit()
            db.refresh(property_obj)
        return property_obj
    
    @staticmethod
    def delete_property(db: Session, property_id) -> bool:
        """Delete property and all related records - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        property_obj = db.query(Property).filter(Property.id == property_id).first()
        if property_obj:
            db.delete(property_obj)
            db.commit()
            return True
        return False

class AnalysisCRUD:
    @staticmethod
    def create_analysis(db: Session, property_id, **analysis_data) -> PropertyAnalysis:
        """Create a new property analysis - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        analysis = PropertyAnalysis(property_id=property_id, **analysis_data)
        db.add(analysis)
        db.commit()
        db.refresh(analysis)
        return analysis
    
    @staticmethod
    def get_latest_analysis(db: Session, property_id) -> Optional[PropertyAnalysis]:
        """Get the most recent analysis for a property - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        return (db.query(PropertyAnalysis)
                .filter(PropertyAnalysis.property_id == property_id)
                .order_by(desc(PropertyAnalysis.created_at))
                .first())
    
    @staticmethod
    def get_all_analyses(db: Session, property_id=None) -> List[PropertyAnalysis]:
        """Get all analyses, optionally filtered by property - handles both UUID and string formats"""
        query = db.query(PropertyAnalysis)
        
        if property_id:
            # Handle both UUID and string formats
            if isinstance(property_id, uuid.UUID):
                property_id = str(property_id)
            query = query.filter(PropertyAnalysis.property_id == property_id)
        
        return query.order_by(desc(PropertyAnalysis.created_at)).all()
    
    @staticmethod
    def get_analysis_stats(db: Session) -> Dict[str, Any]:
        """Get analysis statistics"""
        total_properties = db.query(Property).count()
        total_analyses = db.query(PropertyAnalysis).count()
        
        viable_count = (db.query(PropertyAnalysis)
                       .filter(PropertyAnalysis.meets_requirements.ilike("%yes%"))
                       .count())
        
        avg_income = (db.query(PropertyAnalysis.monthly_income)
                     .filter(PropertyAnalysis.monthly_income.isnot(None))
                     .all())
        
        avg_monthly_income = sum(float(income[0]) for income in avg_income) / len(avg_income) if avg_income else 0
        
        total_monthly_income = sum(float(income[0]) for income in avg_income) if avg_income else 0
        
        return {
            "total_properties": total_properties,
            "total_analyses": total_analyses,
            "viable_properties": viable_count,
            "non_viable_properties": total_analyses - viable_count,
            "average_monthly_income": round(avg_monthly_income, 2),
            "total_monthly_income": round(total_monthly_income, 2),
            "total_annual_income": round(total_monthly_income * 12, 2)
        }

class TaskCRUD:
    @staticmethod
    def create_task(db: Session, task_id: str, property_id) -> AnalysisTask:
        """Create a new analysis task - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        task = AnalysisTask(task_id=task_id, property_id=property_id)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def get_task_by_id(db: Session, task_id: str) -> Optional[AnalysisTask]:
        """Get task by task ID"""
        return db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
    
    @staticmethod
    def update_task_status(
        db: Session, 
        task_id: str, 
        status: str, 
        progress: dict = None,
        error_message: str = None
    ) -> Optional[AnalysisTask]:
        """Update task status and progress"""
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if task:
            task.status = status
            if progress:
                task.progress = progress
            if error_message:
                task.error_message = error_message
            if status == "completed":
                task.completed_at = datetime.utcnow()
            db.commit()
            db.refresh(task)
        return task
    
    @staticmethod
    def get_active_tasks(db: Session) -> List[AnalysisTask]:
        """Get all active (running/pending) tasks"""
        return (db.query(AnalysisTask)
                .filter(AnalysisTask.status.in_(["pending", "running"]))
                .order_by(desc(AnalysisTask.started_at))
                .all())
    
    @staticmethod
    def cleanup_old_tasks(db: Session, days_old: int = 7) -> int:
        """Clean up old completed/failed tasks"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = (db.query(AnalysisTask)
                        .filter(
                            and_(
                                AnalysisTask.status.in_(["completed", "failed"]),
                                AnalysisTask.started_at < cutoff_date
                            )
                        )
                        .delete())
        
        db.commit()
        return deleted_count

class AnalyticsCRUD:
    @staticmethod
    def log_event(
        db: Session,
        event_type: str,
        property_id=None,
        task_id: str = None,
        event_data: dict = None,
        user_agent: str = None,
        ip_address: str = None
    ) -> AnalyticsLog:
        """Log an analytics event - handles both UUID and string formats"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        log_entry = AnalyticsLog(
            event_type=event_type,
            property_id=property_id,
            task_id=task_id,
            event_data=event_data,
            user_agent=user_agent,
            ip_address=ip_address
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        return log_entry
    
    @staticmethod
    def get_analytics_summary(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get analytics summary for the last N days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        events = (db.query(AnalyticsLog)
                 .filter(AnalyticsLog.created_at >= cutoff_date)
                 .all())
        
        event_counts = {}
        for event in events:
            event_counts[event.event_type] = event_counts.get(event.event_type, 0) + 1
        
        return {
            "period_days": days,
            "total_events": len(events),
            "event_breakdown": event_counts,
            "daily_average": round(len(events) / days, 2)
        }