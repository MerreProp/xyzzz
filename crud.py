"""
Database CRUD operations for HMO Analyser
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, or_, func, text
from models import Property, PropertyAnalysis, AnalysisTask, AnalyticsLog, PropertyChange, PropertyTrend, PropertyURL, RoomChange, Room, RoomAvailabilityPeriod, RoomPriceHistory, get_price_trend_direction
from typing import List, Optional, Dict, Any, Tuple
import uuid
import statistics
from datetime import datetime, timedelta
from decimal import Decimal


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
        city: str = None,  # NEW: Add city filter
        area: str = None,  # NEW: Add area filter
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
        
        # NEW: City filter
        if city and city != 'all':
            query = query.filter(Property.city == city)
        
        # NEW: Area filter
        if area and area != 'all':
            query = query.filter(Property.area == area)
        
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
    
    @staticmethod
    def get_cities_with_properties(db: Session) -> List[str]:
        """Get list of cities that have properties, sorted alphabetically"""
        cities = (db.query(Property.city)
                .filter(Property.city.isnot(None))
                .filter(Property.city != '')
                .distinct()
                .order_by(Property.city)
                .all())
        
        # Extract city names from query result tuples
        city_list = [city[0] for city in cities if city[0]]
        return city_list

    @staticmethod
    def get_areas_for_city(db: Session, city: str) -> List[str]:
        """Get list of areas/suburbs for a specific city"""
        areas = (db.query(Property.area)
                .filter(Property.city == city)
                .filter(Property.area.isnot(None))
                .filter(Property.area != '')
                .distinct()
                .order_by(Property.area)
                .all())
        
        # Extract area names from query result tuples
        area_list = [area[0] for area in areas if area[0]]
        return area_list


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

# crud.py - Updated TaskCRUD class

class TaskCRUD:
    @staticmethod
    def create_task(db: Session, task_id: str, property_id=None, task_type: str = "individual") -> AnalysisTask:
        """Create a new analysis task - handles both individual and bulk updates"""
        # Handle both UUID and string formats for property_id
        if property_id and isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        task = AnalysisTask(
            task_id=task_id, 
            property_id=property_id,
            task_type=task_type
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        return task
    
    @staticmethod
    def create_bulk_update_task(db: Session, task_id: str) -> AnalysisTask:
        """Create a bulk update task (no specific property)"""
        return TaskCRUD.create_task(db, task_id, property_id=None, task_type="bulk_update")
    
    @staticmethod
    def create_property_task(db: Session, task_id: str, property_id) -> AnalysisTask:
        """Create an individual property analysis task"""
        return TaskCRUD.create_task(db, task_id, property_id=property_id, task_type="individual")
    
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
    def get_bulk_update_tasks(db: Session, limit: int = 50) -> List[AnalysisTask]:
        """Get recent bulk update tasks"""
        return (db.query(AnalysisTask)
                .filter(AnalysisTask.task_type == "bulk_update")
                .order_by(desc(AnalysisTask.started_at))
                .limit(limit)
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
    
# Add this new CRUD class to your crud.py file
class PropertyChangeCRUD:
    @staticmethod
    def create_change(
        db: Session, 
        property_id, 
        change_type: str,
        field_name: str,
        old_value: str,
        new_value: str,
        change_summary: str,
        analysis_id=None,
        room_details: dict = None
    ) -> PropertyChange:
        """Create a new property change record"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        if isinstance(analysis_id, uuid.UUID):
            analysis_id = str(analysis_id)
            
        change = PropertyChange(
            property_id=property_id,
            change_type=change_type,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_summary=change_summary,
            analysis_id=analysis_id,
            room_details=room_details
        )
        db.add(change)
        db.commit()
        db.refresh(change)
        return change
    
    @staticmethod
    def get_property_changes(
        db: Session, 
        property_id, 
        limit: int = 50
    ) -> List[PropertyChange]:
        """Get all changes for a specific property"""
        # Handle both UUID and string formats
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        return (db.query(PropertyChange)
                .filter(PropertyChange.property_id == property_id)
                .order_by(desc(PropertyChange.detected_at))
                .limit(limit)
                .all())
    
    @staticmethod
    def get_recent_changes(
        db: Session, 
        since_date: datetime, 
        limit: int = 100,
        change_type: str = None
    ) -> List[PropertyChange]:
        """Get recent changes across all properties"""
        query = (db.query(PropertyChange)
                .join(Property)
                .filter(PropertyChange.detected_at >= since_date))
        
        if change_type:
            query = query.filter(PropertyChange.change_type == change_type)
        
        return (query.order_by(desc(PropertyChange.detected_at))
                .limit(limit)
                .all())
    
    @staticmethod
    def get_changes_by_type(
        db: Session, 
        change_type: str, 
        days: int = 30,
        limit: int = 100
    ) -> List[PropertyChange]:
        """Get changes of a specific type"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        return (db.query(PropertyChange)
                .filter(
                    PropertyChange.change_type == change_type,
                    PropertyChange.detected_at >= cutoff_date
                )
                .order_by(desc(PropertyChange.detected_at))
                .limit(limit)
                .all())
    
    @staticmethod
    def get_change_stats(db: Session, days: int = 30) -> Dict[str, Any]:
        """Get statistics about changes"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total changes
        total_changes = (db.query(PropertyChange)
                        .filter(PropertyChange.detected_at >= cutoff_date)
                        .count())
        
        # Changes by type
        change_types = (db.query(PropertyChange.change_type, func.count(PropertyChange.id))
                       .filter(PropertyChange.detected_at >= cutoff_date)
                       .group_by(PropertyChange.change_type)
                       .all())
        
        # Properties with changes
        properties_with_changes = (db.query(PropertyChange.property_id)
                                  .filter(PropertyChange.detected_at >= cutoff_date)
                                  .distinct()
                                  .count())
        
        return {
            "total_changes": total_changes,
            "change_types": dict(change_types),
            "properties_affected": properties_with_changes,
            "period_days": days
        }
    
    @staticmethod
    def delete_old_changes(db: Session, days_old: int = 90) -> int:
        """Delete change records older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        
        deleted_count = (db.query(PropertyChange)
                        .filter(PropertyChange.detected_at < cutoff_date)
                        .delete())
        
        db.commit()
        return deleted_count
    
# ADD THIS CLASS to crud.py:
class RoomPriceHistoryCRUD:
    """CRUD operations for room price history tracking"""
    
    @staticmethod
    def track_price_change(
        db: Session,
        room_id,
        property_id,
        previous_price: Decimal,
        new_price: Decimal,
        previous_price_text: str,
        new_price_text: str,
        analysis_id = None,
        change_reason: str = "period_start"
    ) -> 'RoomPriceHistory':
        """Track a price change for a room"""
        
        # Handle UUID formats
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        if isinstance(analysis_id, uuid.UUID):
            analysis_id = str(analysis_id)
        
        # Calculate change metrics
        price_change_amount = new_price - previous_price if (new_price and previous_price) else None
        price_change_percentage = None
        
        if previous_price and previous_price > 0:
            price_change_percentage = Decimal(str(round(((new_price - previous_price) / previous_price) * 100, 2)))
        
        # Create price history record
        price_history = RoomPriceHistory(
            room_id=room_id,
            property_id=property_id,
            analysis_id=analysis_id,
            previous_price=previous_price,
            new_price=new_price,
            previous_price_text=previous_price_text,
            new_price_text=new_price_text,
            price_change_amount=price_change_amount,
            price_change_percentage=price_change_percentage,
            change_reason=change_reason,
            effective_date=datetime.utcnow()
        )
        
        db.add(price_history)
        db.commit()
        db.refresh(price_history)
        return price_history
    
    @staticmethod
    def get_room_price_history(
        db: Session,
        room_id,
        limit: int = 50
    ) -> List['RoomPriceHistory']:
        """Get price history for a specific room"""
        
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        
        return (db.query(RoomPriceHistory)
                .filter(RoomPriceHistory.room_id == room_id)
                .order_by(desc(RoomPriceHistory.effective_date))
                .limit(limit)
                .all())
    
    @staticmethod
    def get_property_price_trends(
        db: Session,
        property_id,
        days: int = 90
    ) -> Dict[str, Any]:
        """Get price trends for all rooms in a property"""
        
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get all price changes for this property
        price_changes = (db.query(RoomPriceHistory)
                        .filter(
                            RoomPriceHistory.property_id == property_id,
                            RoomPriceHistory.effective_date >= cutoff_date
                        )
                        .order_by(desc(RoomPriceHistory.effective_date))
                        .all())
        
        if not price_changes:
            return {
                "total_changes": 0,
                "average_change_amount": 0,
                "average_change_percentage": 0,
                "trend_direction": "stable",
                "price_volatility": 0,
                "changes_by_room": {}
            }
        
        # Calculate metrics
        change_amounts = [float(change.price_change_amount) for change in price_changes if change.price_change_amount]
        change_percentages = [float(change.price_change_percentage) for change in price_changes if change.price_change_percentage]
        
        # Group by room
        changes_by_room = {}
        for change in price_changes:
            room_id = change.room_id
            if room_id not in changes_by_room:
                changes_by_room[room_id] = []
            changes_by_room[room_id].append({
                "date": change.effective_date.isoformat(),
                "previous_price": float(change.previous_price) if change.previous_price else None,
                "new_price": float(change.new_price) if change.new_price else None,
                "change_amount": float(change.price_change_amount) if change.price_change_amount else None,
                "change_percentage": float(change.price_change_percentage) if change.price_change_percentage else None,
                "reason": change.change_reason
            })
        
        return {
            "total_changes": len(price_changes),
            "average_change_amount": round(statistics.mean(change_amounts), 2) if change_amounts else 0,
            "average_change_percentage": round(statistics.mean(change_percentages), 2) if change_percentages else 0,
            "trend_direction": get_price_trend_direction(change_amounts) if change_amounts else "stable",
            "price_volatility": round(statistics.stdev(change_amounts), 2) if len(change_amounts) > 1 else 0,
            "changes_by_room": changes_by_room,
            "period_days": days
        }

# ADD THIS CLASS to crud.py:
class PropertyTrendCRUD:
    """CRUD operations for property trend analysis"""
    
    @staticmethod
    def calculate_and_store_trends(
        db: Session,
        property_id,
        trend_period: str = "monthly"
    ) -> 'PropertyTrend':
        """Calculate and store comprehensive trends for a property - FIXED VERSION"""
        
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        
        # Define period duration
        period_durations = {
            "weekly": 7,
            "monthly": 30,
            "quarterly": 90
        }
        
        days = period_durations.get(trend_period, 30)
        period_start = datetime.utcnow() - timedelta(days=days)
        period_end = datetime.utcnow()
        
        # FIXED QUERY 1: Get availability periods without ambiguous join
        availability_periods = (db.query(RoomAvailabilityPeriod)
                               .filter(
                                   RoomAvailabilityPeriod.room_id.in_(
                                       db.query(Room.id).filter(Room.property_id == property_id)
                                   ),
                                   RoomAvailabilityPeriod.period_start_date >= period_start
                               )
                               .all())
        
        # FIXED QUERY 2: Get price history without joins
        price_history = (db.query(RoomPriceHistory)
                        .filter(
                            RoomPriceHistory.property_id == property_id,
                            RoomPriceHistory.effective_date >= period_start
                        )
                        .all())
        
        # Calculate availability metrics
        avg_availability_duration = None
        availability_turnover_rate = None
        
        if availability_periods:
            completed_periods = [p for p in availability_periods if p.duration_days is not None]
            if completed_periods:
                durations = [p.duration_days for p in completed_periods]
                avg_availability_duration = Decimal(str(round(statistics.mean(durations), 2)))
                
                # Calculate turnover rate (periods per month)
                periods_per_month = (len(completed_periods) / days) * 30
                availability_turnover_rate = Decimal(str(round(periods_per_month, 2)))
        
        # Calculate price metrics
        avg_room_price = None
        price_volatility = None
        price_trend_direction = "stable"
        price_change_percentage = None
        
        if price_history:
            prices = [float(p.new_price) for p in price_history if p.new_price]
            if prices:
                avg_room_price = Decimal(str(round(statistics.mean(prices), 2)))
                price_volatility = Decimal(str(round(statistics.stdev(prices), 2))) if len(prices) > 1 else Decimal('0')
                
                # Calculate trend direction
                price_changes = [float(p.price_change_amount) for p in price_history if p.price_change_amount]
                if price_changes:
                    total_change = sum(price_changes)
                    first_price = prices[-1] if prices else 0  # oldest price
                    if first_price > 0:
                        price_change_percentage = Decimal(str(round((total_change / first_price) * 100, 2)))
                    
                    price_trend_direction = get_price_trend_direction(price_changes)
        
        # Calculate income metrics
        property_obj = PropertyCRUD.get_property_by_id(db, property_id)
        latest_analysis = AnalysisCRUD.get_latest_analysis(db, property_id)
        
        estimated_monthly_income = None
        income_stability_score = None
        vacancy_impact = None
        
        if latest_analysis and latest_analysis.monthly_income:
            estimated_monthly_income = latest_analysis.monthly_income
            
            # Calculate stability score based on availability consistency
            if availability_periods:
                # Higher score = more stable (less turnover)
                turnover_factor = min(availability_turnover_rate or 0, 5) / 5  # normalize to 0-1
                income_stability_score = Decimal(str(round(1 - turnover_factor, 2)))
                
                # Estimate vacancy impact
                if avg_availability_duration:
                    # Assume each vacancy costs 1 month of lost income on average
                    monthly_vacancy_rate = (availability_turnover_rate or 0) / 30
                    vacancy_impact = estimated_monthly_income * Decimal(str(monthly_vacancy_rate))
        
        # Create trend record
        trend = PropertyTrend(
            property_id=property_id,
            trend_period=trend_period,
            period_start=period_start,
            period_end=period_end,
            avg_availability_duration=avg_availability_duration,
            total_availability_periods=len(availability_periods),
            availability_turnover_rate=availability_turnover_rate,
            avg_room_price=avg_room_price,
            price_volatility=price_volatility,
            price_trend_direction=price_trend_direction,
            price_change_percentage=price_change_percentage,
            estimated_monthly_income=estimated_monthly_income,
            income_stability_score=income_stability_score,
            vacancy_impact=vacancy_impact,
            data_points_used=len(availability_periods) + len(price_history),
            confidence_score=Decimal('0.8') if len(availability_periods) > 3 else Decimal('0.5')
        )
        
        db.add(trend)
        db.commit()
        db.refresh(trend)
        return trend
    
    @staticmethod
    def get_property_trends(
        db: Session,
        property_id,
        trend_period: str = "monthly",
        limit: int = 12
    ) -> List['PropertyTrend']:
        """Get historical trends for a property"""
        
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        
        return (db.query(PropertyTrend)
                .filter(
                    PropertyTrend.property_id == property_id,
                    PropertyTrend.trend_period == trend_period
                )
                .order_by(desc(PropertyTrend.period_start))
                .limit(limit)
                .all())
    
    @staticmethod
    def get_market_comparison(
        db: Session,
        property_id,
        comparison_radius_km: float = 5.0
    ) -> Dict[str, Any]:
        """Compare property trends to nearby properties"""
        
        # This is a simplified version - in production you'd use PostGIS for geo queries
        property_obj = PropertyCRUD.get_property_by_id(db, property_id)
        if not property_obj or not property_obj.latitude or not property_obj.longitude:
            return {"error": "Property location data not available"}
        
        # Get recent trends for all properties (simplified - normally you'd filter by location)
        recent_trends = (db.query(PropertyTrend)
                        .filter(
                            PropertyTrend.trend_period == "monthly",
                            PropertyTrend.period_start >= datetime.utcnow() - timedelta(days=60)
                        )
                        .all())
        
        if not recent_trends:
            return {"error": "Insufficient market data"}
        
        # Calculate market averages
        market_avg_price = statistics.mean([
            float(t.avg_room_price) for t in recent_trends 
            if t.avg_room_price and t.property_id != property_id
        ]) if recent_trends else 0
        
        market_avg_duration = statistics.mean([
            float(t.avg_availability_duration) for t in recent_trends 
            if t.avg_availability_duration and t.property_id != property_id
        ]) if recent_trends else 0
        
        # Get this property's latest trend
        property_trend = (db.query(PropertyTrend)
                         .filter(
                             PropertyTrend.property_id == property_id,
                             PropertyTrend.trend_period == "monthly"
                         )
                         .order_by(desc(PropertyTrend.period_start))
                         .first())
        
        if not property_trend:
            return {"error": "No trend data for this property"}
        
        return {
            "property_avg_price": float(property_trend.avg_room_price) if property_trend.avg_room_price else 0,
            "market_avg_price": round(market_avg_price, 2),
            "price_vs_market": round(((float(property_trend.avg_room_price or 0) - market_avg_price) / market_avg_price) * 100, 2) if market_avg_price > 0 else 0,
            "property_avg_duration": float(property_trend.avg_availability_duration) if property_trend.avg_availability_duration else 0,
            "market_avg_duration": round(market_avg_duration, 2),
            "duration_vs_market": round(((float(property_trend.avg_availability_duration or 0) - market_avg_duration) / market_avg_duration) * 100, 2) if market_avg_duration > 0 else 0,
            "sample_size": len(recent_trends)
        }

# Add these classes to your crud.py file

import re
from decimal import Decimal

class RoomCRUD:
    @staticmethod
    def parse_room_string(room_string: str) -> Dict[str, Any]:
        """Parse a room string to extract components with proper status detection"""
        
        # Extract room number/identifier
        room_number_match = re.match(r'^(Room\s+\w+|Bedroom\s+\w+|\w+|\d+)', room_string)
        room_number = room_number_match.group(1) if room_number_match else "Unknown"
        
        # Extract price with pw/pcm detection
        price_match = re.search(r'£(\d+(?:,\d{3})*(?:\.\d{2})?)\s*(pw|pcm)?', room_string)
        price_text_match = re.search(r'£\d+[^(]*', room_string)
        
        price = None
        price_text = ""
        is_per_week = False
        
        if price_match:
            price_str = price_match.group(1).replace(',', '')
            period_suffix = price_match.group(2)  # 'pw' or 'pcm' or None
            
            # Determine if it's per week
            if period_suffix == 'pw':
                is_per_week = True
            elif period_suffix is None:
                # Check if 'pw' appears elsewhere in the string
                is_per_week = bool(re.search(r'\bpw\b', room_string.lower()))
            
            try:
                price = Decimal(price_str)
                
                # Convert weekly to monthly
                if is_per_week:
                    original_price = price
                    price = price * Decimal('4.33')  # 4.33 weeks per month
                    print(f"💰 Room price converted: £{original_price} pw → £{price:.0f} pcm")
                    
            except:
                price = None
        
        if price_text_match:
            price_text = price_text_match.group(0).strip(' -')
            
            # Keep price_text clean - just show the monthly price
            if is_per_week and price:
                price_text = f"£{price:.0f} pcm"
        
        # Extract room type (text in parentheses)
        room_type_match = re.search(r'\(([^)]+)\)', room_string)
        room_type = room_type_match.group(1) if room_type_match else ""
        
        # FIXED: Determine status - check for all taken indicators
        room_string_upper = room_string.upper()
        
        # List of all possible "taken" indicators
        taken_indicators = [
            "(NOW LET)",
            "(TAKEN)", 
            "(RESERVED)",
            "(PENDING)",
            "(UNAVAILABLE)",
            "(NOT AVAILABLE)",
            "(OCCUPIED)",
            "(LET AGREED)",
            "(EXPIRED)"
        ]
    
        # Check if any taken indicator is present
        is_taken = any(indicator in room_string_upper for indicator in taken_indicators)
        
        status = "taken" if is_taken else "available"
        
        # Debug logging to verify status detection
        if is_taken:
            print(f"🔴 Room detected as TAKEN: '{room_string}' → status: '{status}'")
        else:
            print(f"🟢 Room detected as AVAILABLE: '{room_string}' → status: '{status}'")
        
        return {
            "room_number": room_number,
            "price": price,
            "price_text": price_text,
            "room_type": room_type,
            "status": status,  # Now correctly set to "taken" for rooms with (TAKEN)
            "identifier": room_string,
            "was_converted_from_weekly": is_per_week
        }
    
    @staticmethod
    def debug_room_parsing(room_string: str):
        """Debug helper to see how room strings are being parsed"""
        result = RoomCRUD.parse_room_string(room_string)
        print(f"🔍 ROOM PARSE DEBUG:")
        print(f"   Input: '{room_string}'")
        print(f"   Output: {result}")
        return result

    
    @staticmethod
    def create_or_update_room(
        db: Session,
        property_id,
        room_string: str,
        analysis_id=None
    ) -> tuple:
        """Create a new room or update existing room with improved duplicate prevention"""
        
        # Handle UUID format
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        if isinstance(analysis_id, uuid.UUID):
            analysis_id = str(analysis_id)
            
        # Parse room details
        room_data = RoomCRUD.parse_room_string(room_string)
        
        print(f"\n🏠 Processing room: '{room_string}'")
        print(f"   Parsed data: {room_data}")
        
        # ✅ IMPROVED: Use stable key matching instead of exact string matching
        existing_room = RoomCRUD.find_existing_room_by_stable_key(db, property_id, room_string)
        
        current_time = datetime.utcnow()
        
        if existing_room:
            # Update existing room - prevent duplication
            changes = []
            print(f"📝 Updating existing room: {existing_room.room_number} (ID: {existing_room.id})")
            
            # Check for status changes
            old_status = existing_room.current_status
            new_status = room_data["status"]
            
            if old_status != new_status:
                changes.append({
                    "type": "status_change",
                    "old": old_status,
                    "new": new_status,
                    "summary": f"Status changed from {old_status} to {new_status}"
                })
                
                existing_room.current_status = new_status
                print(f"   🔄 Status change: {old_status} → {new_status}")
                
                # Handle availability period transitions
                if old_status != 'available' and new_status == 'available':
                    # Room became available - start new period
                    RoomAvailabilityPeriodCRUD.create_availability_period(
                        db,
                        room_id=existing_room.id,
                        period_start_date=current_time,
                        price_at_start=room_data["price"],
                        price_text_at_start=room_data["price_text"],
                        room_type_at_start=room_data["room_type"],
                        room_identifier_at_start=room_string,
                        discovery_analysis_id=analysis_id
                    )
                    print(f"   🟢 Started new availability period")
                    
                elif old_status == 'available' and new_status != 'available':
                    # Room became unavailable - end current period
                    RoomAvailabilityPeriodCRUD.end_current_period(
                        db,
                        room_id=existing_room.id,
                        end_date=current_time,
                        end_analysis_id=analysis_id
                    )
                    print(f"   🔴 Ended current availability period")
            
            # ✅ IMPORTANT: Update the room_identifier to the latest version
            if existing_room.room_identifier != room_string:
                print(f"   🔄 Updating room identifier:")
                print(f"     Old: '{existing_room.room_identifier}'")
                print(f"     New: '{room_string}'")
                existing_room.room_identifier = room_string
            
            # Check for price changes within the same availability period
            if (room_data["price"] and existing_room.current_price != room_data["price"] 
                and new_status == 'available'):
                changes.append({
                    "type": "price_change",
                    "old": str(existing_room.current_price) if existing_room.current_price else None,
                    "new": str(room_data["price"]),
                    "summary": f"Price changed from £{existing_room.current_price} to £{room_data['price']}"
                })
                existing_room.current_price = room_data["price"]
                print(f"   💰 Price change: £{existing_room.current_price} → £{room_data['price']}")
            
            # Update tracking info
            existing_room.last_seen_date = current_time
            existing_room.times_seen += 1
            existing_room.is_currently_listed = True
            
            if changes:
                existing_room.times_changed += 1
                # Log room changes
                for change in changes:
                    RoomCRUD.create_room_change(
                        db, existing_room.id, property_id, analysis_id,
                        change["type"], change["old"], change["new"], change["summary"]
                    )
            
            db.commit()
            db.refresh(existing_room)
            print(f"   ✅ Updated existing room successfully")
            return existing_room, False  # Not new
        
        else:
            # Create new room - only if we truly couldn't find a match
            print(f"🆕 Creating new room: {room_data['room_number']}")
            new_room = Room(
                property_id=property_id,
                room_identifier=room_string,
                room_number=room_data["room_number"],
                price_text=room_data["price_text"],
                room_type=room_data["room_type"],
                current_price=room_data["price"],
                original_price=room_data["price"],
                current_status=room_data["status"],
                first_seen_date=current_time,
                last_seen_date=current_time,
                is_currently_listed=True
            )
            
            db.add(new_room)
            db.commit()
            db.refresh(new_room)
            
            # If room is available, create initial availability period
            if room_data["status"] == 'available':
                RoomAvailabilityPeriodCRUD.create_availability_period(
                    db,
                    room_id=new_room.id,
                    period_start_date=current_time,
                    price_at_start=room_data["price"],
                    price_text_at_start=room_data["price_text"],
                    room_type_at_start=room_data["room_type"],
                    room_identifier_at_start=room_string,
                    discovery_analysis_id=analysis_id
                )
            
            # Log room discovery
            RoomCRUD.create_room_change(
                db, new_room.id, property_id, analysis_id,
                "discovered", None, room_string, f"Room first discovered: {room_data['room_number']}"
            )
            
            print(f"   ✅ Created new room successfully (ID: {new_room.id})")
            return new_room, True  # Is new
        
    @staticmethod
    def generate_room_base_key(room_string: str) -> str:
        """Generate a stable identifier for a room that doesn't change with status"""
        # Parse the room to extract core identifying information
        room_data = RoomCRUD.parse_room_string(room_string)
        
        # Create a base key using room number and price (the stable elements)
        room_number = room_data.get("room_number", "Unknown")
        price = room_data.get("price")
        
        # Create stable key: "Room1_795" or "Room1_unknown" if no price
        price_key = str(int(price)) if price else "unknown"
        base_key = f"{room_number.replace(' ', '')}_{price_key}"
        
        return base_key

    @staticmethod
    def find_existing_room_by_stable_key(db: Session, property_id, room_string: str):
        """Find existing room using stable characteristics instead of exact string match"""
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        
        # Generate the stable key for the new room
        new_room_base_key = RoomCRUD.generate_room_base_key(room_string)
        room_data = RoomCRUD.parse_room_string(room_string)
        
        print(f"🔍 Looking for existing room with base key: '{new_room_base_key}'")
        
        # Get all rooms for this property and check their base keys
        all_property_rooms = (db.query(Room)
                             .filter(Room.property_id == property_id)
                             .all())
        
        for existing_room in all_property_rooms:
            existing_base_key = RoomCRUD.generate_room_base_key(existing_room.room_identifier)
            
            print(f"   Comparing with existing room:")
            print(f"     Existing: '{existing_room.room_identifier}' → Base: '{existing_base_key}'")
            print(f"     New: '{room_string}' → Base: '{new_room_base_key}'")
            
            if existing_base_key == new_room_base_key:
                print(f"   ✅ MATCH FOUND! Using existing room ID: {existing_room.id}")
                return existing_room
        
        print(f"   ❌ No existing room found - will create new")
        return None
    
    @staticmethod
    def process_rooms_list(
        db: Session,
        property_id,
        rooms_list: List[str],
        analysis_id=None
    ) -> Dict[str, Any]:
        """Process a complete rooms list and update room tracking"""
        # Handle UUID format
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        results = {
            "new_rooms": [],
            "updated_rooms": [],
            "disappeared_rooms": [],
            "total_changes": 0
        }
        
        # Get all current rooms for this property
        current_rooms = (db.query(Room)
                        .filter(Room.property_id == property_id)
                        .all())
        
        # Track which rooms we've seen in this update
        seen_room_identifiers = set()
        
        # Process each room in the current list
        for room_string in rooms_list:
            seen_room_identifiers.add(room_string)
            room, is_new = RoomCRUD.create_or_update_room(db, property_id, room_string, analysis_id)
            
            if is_new:
                results["new_rooms"].append(room)
            else:
                results["updated_rooms"].append(room)
        
        # Check for rooms that have disappeared
        for room in current_rooms:
            if room.room_identifier not in seen_room_identifiers and room.is_currently_listed:
                # Room has disappeared
                room.is_currently_listed = False
                room.current_status = "offline"
                results["disappeared_rooms"].append(room)
                results["total_changes"] += 1
                
                # Log room disappearance
                RoomCRUD.create_room_change(
                    db, room.id, property_id, analysis_id,
                    "disappeared", room.room_identifier, None,
                    f"Room no longer listed: {room.room_number}"
                )
        
        db.commit()
        
        results["total_changes"] = len(results["new_rooms"]) + len(results["disappeared_rooms"])
        return results
    
    @staticmethod
    def get_property_rooms_with_history(db: Session, property_id) -> List[Dict[str, Any]]:
        """Get all rooms for a property with their discovery dates, period history, and date gone"""
        
        # Handle UUID format
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
            
        rooms = (db.query(Room)
                .filter(Room.property_id == property_id)
                .order_by(Room.first_seen_date, Room.room_number)
                .all())
        
        result = []
        for room in rooms:
            # Get availability periods for this room
            periods = RoomAvailabilityPeriodCRUD.get_room_periods(db, room.id)
            
            room_data = {
                "room_id": str(room.id),
                "room_identifier": room.room_identifier,
                "room_number": room.room_number,
                "price_text": room.price_text,
                "room_type": room.room_type,
                "current_price": float(room.current_price) if room.current_price else None,
                "original_price": float(room.original_price) if room.original_price else None,
                "current_status": room.current_status,
                "is_currently_listed": room.is_currently_listed,
                "first_seen_date": room.first_seen_date.strftime('%d/%m/%y') if room.first_seen_date else None,
                "last_seen_date": room.last_seen_date.strftime('%d/%m/%y') if room.last_seen_date else None,
                "times_seen": room.times_seen,
                "times_changed": room.times_changed,
                "days_since_discovered": (datetime.utcnow() - room.first_seen_date).days if room.first_seen_date else None,
                
                # PHASE 1 ADDITIONS:
                "date_gone": room.date_gone.strftime('%d/%m/%y') if room.date_gone else None,
                "date_returned": room.date_returned.strftime('%d/%m/%y') if room.date_returned else None,
                "total_availability_periods": room.total_availability_periods or 0,
                "average_availability_duration": float(room.average_availability_duration) if room.average_availability_duration else None,
                
                # Period history
                "availability_periods": [
                    {
                        "period_id": str(period.id),
                        "start_date": period.period_start_date.strftime('%d/%m/%y'),
                        "end_date": period.period_end_date.strftime('%d/%m/%y') if period.period_end_date else None,
                        "duration_days": period.duration_days,
                        "price_at_start": float(period.price_at_start) if period.price_at_start else None,
                        "price_text_at_start": period.price_text_at_start,
                        "is_current": period.is_current_period,
                        "status": "ongoing" if period.is_current_period else "completed"
                    }
                    for period in periods
                ]
            }
            
            result.append(room_data)
        
        return result
    
    @staticmethod
    def create_room_change(
        db: Session,
        room_id,
        property_id,
        analysis_id,
        change_type: str,
        old_value: str,
        new_value: str,
        change_summary: str
    ) -> 'RoomChange':
        """Create a room change record"""
        # Handle UUID formats
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        if isinstance(analysis_id, uuid.UUID):
            analysis_id = str(analysis_id)
            
        change = RoomChange(
            room_id=room_id,
            property_id=property_id,
            analysis_id=analysis_id,
            change_type=change_type,
            old_value=old_value,
            new_value=new_value,
            change_summary=change_summary
        )
        
        db.add(change)
        db.commit()
        db.refresh(change)
        return change
    
    @staticmethod
    def get_room_changes(db: Session, room_id=None, property_id=None, limit: int = 50) -> List['RoomChange']:
        """Get room change history"""
        query = db.query(RoomChange)
        
        if room_id:
            if isinstance(room_id, uuid.UUID):
                room_id = str(room_id)
            query = query.filter(RoomChange.room_id == room_id)
        
        if property_id:
            if isinstance(property_id, uuid.UUID):
                property_id = str(property_id)
            query = query.filter(RoomChange.property_id == property_id)
        
        return (query.order_by(desc(RoomChange.detected_at))
                .limit(limit)
                .all())
    @staticmethod
    def create_or_update_room_with_price_tracking(
        db: Session,
        property_id,
        room_string: str,
        analysis_id=None
    ) -> tuple:
        """Enhanced room creation with price tracking for Phase 2"""
        
        # Call existing method
        room, is_new = RoomCRUD.create_or_update_room(db, property_id, room_string, analysis_id)
        
        # Phase 2 Enhancement: Track price changes
        if not is_new:  # Only for existing rooms
            room_data = RoomCRUD.parse_room_string(room_string)
            new_price = room_data.get("price")
            
            if new_price and room.current_price and new_price != room.current_price:
                # Price changed - track it
                RoomPriceHistoryCRUD.track_price_change(
                    db,
                    room_id=room.id,
                    property_id=property_id,
                    previous_price=room.current_price,
                    new_price=new_price,
                    previous_price_text=room.price_text or "",
                    new_price_text=room_data.get("price_text", ""),
                    analysis_id=analysis_id,
                    change_reason="analysis_update"
                )
                
                print(f"💰 Price change tracked: £{room.current_price} → £{new_price}")
        
        return room, is_new
    
    @staticmethod
    def extract_base_room_identifier(room_string: str) -> str:
        """Extract the base room identifier without status markers for consistent matching"""
        # Remove common status markers that change over time
        base_identifier = room_string
        
        # Remove status markers in parentheses
        status_markers = ['(NOW LET)', '(TAKEN)', '(EXPIRED)', '(AVAILABLE)']
        for marker in status_markers:
            base_identifier = base_identifier.replace(marker, '').strip()
        
        # Remove trailing dashes and extra spaces
        base_identifier = base_identifier.rstrip(' -').strip()
        
        return base_identifier

    @staticmethod
    def generate_room_base_key(room_string: str) -> str:
        """Generate a stable identifier for a room that doesn't change with status"""
        # Parse the room to extract core identifying information
        room_data = RoomCRUD.parse_room_string(room_string)
        
        # Create a base key using room number and price (the stable elements)
        room_number = room_data.get("room_number", "Unknown")
        price = room_data.get("price")
        
        # Create stable key: "Room1_795" or "Room1_unknown" if no price
        price_key = str(int(price)) if price else "unknown"
        base_key = f"{room_number.replace(' ', '')}_{price_key}"
        
        return base_key

    @staticmethod
    def find_existing_room_by_stable_key(db: Session, property_id, room_string: str):
        """Find existing room using stable characteristics instead of exact string match"""
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        
        # Generate the stable key for the new room
        new_room_base_key = RoomCRUD.generate_room_base_key(room_string)
        room_data = RoomCRUD.parse_room_string(room_string)
        
        print(f"🔍 Looking for existing room with base key: '{new_room_base_key}'")
        
        # Get all rooms for this property and check their base keys
        all_property_rooms = (db.query(Room)
                             .filter(Room.property_id == property_id)
                             .all())
        
        for existing_room in all_property_rooms:
            existing_base_key = RoomCRUD.generate_room_base_key(existing_room.room_identifier)
            
            print(f"   Comparing with existing room:")
            print(f"     Existing: '{existing_room.room_identifier}' → Base: '{existing_base_key}'")
            print(f"     New: '{room_string}' → Base: '{new_room_base_key}'")
            
            if existing_base_key == new_room_base_key:
                print(f"   ✅ MATCH FOUND! Using existing room ID: {existing_room.id}")
                return existing_room
        
        print(f"   ❌ No existing room found - will create new")
        return None

    @staticmethod  
    def mark_all_property_rooms_as_taken(db: Session, property_id, analysis_id=None):
        """Mark all rooms for a property as taken (for expired listings)"""
        # Handle UUID format
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        if isinstance(analysis_id, uuid.UUID):
            analysis_id = str(analysis_id)
        
        current_time = datetime.utcnow()
        
        # Get all rooms for this property
        rooms = (db.query(Room)
                .filter(Room.property_id == property_id)
                .all())
        
        updated_rooms = []
        
        for room in rooms:
            # Only update if the room is currently available
            if room.current_status == 'available':
                old_status = room.current_status
                room.current_status = 'taken'
                room.last_seen_date = current_time
                room.times_changed += 1
                
                # Log the status change
                RoomCRUD.create_room_change(
                    db, room.id, property_id, analysis_id,
                    "status_change", old_status, "taken",
                    f"Room marked as taken due to expired listing"
                )
                
                # End current availability period
                RoomAvailabilityPeriodCRUD.end_current_period(
                    db,
                    room_id=room.id,
                    end_date=current_time,
                    end_analysis_id=analysis_id
                )
                
                updated_rooms.append(room)
                print(f"🔄 Updated room {room.room_number} from {old_status} to taken")
        
        db.commit()
        
        return {
            "updated_rooms": updated_rooms,
            "total_changes": len(updated_rooms)
        }
    

class RoomAvailabilityPeriodCRUD:
    """CRUD operations for room availability periods"""
    
    @staticmethod
    def create_availability_period(
        db: Session,
        room_id,
        period_start_date: datetime,
        price_at_start: Decimal = None,
        price_text_at_start: str = None,
        room_type_at_start: str = None,
        room_identifier_at_start: str = None,
        discovery_analysis_id = None
    ) -> RoomAvailabilityPeriod:
        """Create a new availability period for a room"""
        
        # Handle UUID format
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        if isinstance(discovery_analysis_id, uuid.UUID):
            discovery_analysis_id = str(discovery_analysis_id)
        
        # End any existing current period for this room
        RoomAvailabilityPeriodCRUD.end_current_period(db, room_id, period_start_date)
        
        # Create new period
        period = RoomAvailabilityPeriod(
            room_id=room_id,
            period_start_date=period_start_date,
            price_at_start=price_at_start,
            price_text_at_start=price_text_at_start,
            room_type_at_start=room_type_at_start,
            room_identifier_at_start=room_identifier_at_start,
            discovery_analysis_id=discovery_analysis_id,
            is_current_period=True
        )
        
        db.add(period)
        db.commit()
        db.refresh(period)
        
        # Update room's current period reference
        room = db.query(Room).filter(Room.id == room_id).first()
        if room:
            room.current_availability_period_id = period.id
            room.date_returned = period_start_date  # Room became available
            room.date_gone = None  # Clear date gone
            db.commit()
        
        return period
    
    @staticmethod
    def end_current_period(
        db: Session,
        room_id,
        end_date: datetime,
        end_analysis_id = None
    ) -> Optional[RoomAvailabilityPeriod]:
        """End the current availability period for a room"""
        
        # Handle UUID format
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        if isinstance(end_analysis_id, uuid.UUID):
            end_analysis_id = str(end_analysis_id)
        
        # Find current period
        current_period = db.query(RoomAvailabilityPeriod).filter(
            RoomAvailabilityPeriod.room_id == room_id,
            RoomAvailabilityPeriod.is_current_period == True
        ).first()
        
        if current_period:
            # Calculate duration
            duration = (end_date - current_period.period_start_date).days
            
            # Update period
            current_period.period_end_date = end_date
            current_period.duration_days = max(0, duration)
            current_period.is_current_period = False
            current_period.end_analysis_id = end_analysis_id
            
            # Update room
            room = db.query(Room).filter(Room.id == room_id).first()
            if room:
                room.current_availability_period_id = None
                room.date_gone = end_date  # Room became unavailable
                room.date_returned = None  # Clear date returned
            
            db.commit()
            db.refresh(current_period)
            
            return current_period
        
        return None
    
    @staticmethod
    def get_room_periods(
        db: Session,
        room_id,
        limit: int = 50
    ) -> List[RoomAvailabilityPeriod]:
        """Get all availability periods for a room"""
        
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        
        return (db.query(RoomAvailabilityPeriod)
                .filter(RoomAvailabilityPeriod.room_id == room_id)
                .order_by(desc(RoomAvailabilityPeriod.period_start_date))
                .limit(limit)
                .all())
    
    @staticmethod
    def get_current_period(db: Session, room_id) -> Optional[RoomAvailabilityPeriod]:
        """Get the current availability period for a room"""
        
        if isinstance(room_id, uuid.UUID):
            room_id = str(room_id)
        
        return db.query(RoomAvailabilityPeriod).filter(
            RoomAvailabilityPeriod.room_id == room_id,
            RoomAvailabilityPeriod.is_current_period == True
        ).first()
    
    @staticmethod
    def get_property_period_summary(db: Session, property_id) -> Dict[str, Any]:
        """Get availability period summary for all rooms in a property"""
        
        if isinstance(property_id, uuid.UUID):
            property_id = str(property_id)
        
        # Get all rooms for the property
        rooms = db.query(Room).filter(Room.property_id == property_id).all()
        
        summary = {
            "total_rooms": len(rooms),
            "rooms_with_periods": 0,
            "total_periods": 0,
            "current_available_rooms": 0,
            "rooms_currently_gone": 0,
            "property_date_gone": None,
            "room_summaries": []
        }
        
        property_date_gone_candidates = []
        
        for room in rooms:
            # Get periods for this room
            periods = RoomAvailabilityPeriodCRUD.get_room_periods(db, room.id)
            
            room_summary = {
                "room_id": str(room.id),
                "room_number": room.room_number,
                "current_status": room.current_status,
                "date_gone": room.date_gone.isoformat() if room.date_gone else None,
                "date_returned": room.date_returned.isoformat() if room.date_returned else None,
                "total_periods": len(periods),
                "is_currently_available": room.current_status == 'available' and room.is_currently_listed
            }
            
            if periods:
                summary["rooms_with_periods"] += 1
                summary["total_periods"] += len(periods)
                
                # Calculate room statistics
                completed_periods = [p for p in periods if p.duration_days is not None]
                if completed_periods:
                    durations = [p.duration_days for p in completed_periods]
                    room_summary.update({
                        "average_duration": sum(durations) / len(durations),
                        "shortest_period": min(durations),
                        "longest_period": max(durations)
                    })
            
            # Track availability for property-level calculations
            if room_summary["is_currently_available"]:
                summary["current_available_rooms"] += 1
            elif room.date_gone:
                summary["rooms_currently_gone"] += 1
                property_date_gone_candidates.append(room.date_gone)
            
            summary["room_summaries"].append(room_summary)
        
        # Calculate property date gone
        # Property is "gone" when NO rooms are currently available
        if summary["current_available_rooms"] == 0 and property_date_gone_candidates:
            # Property went offline when the last room became unavailable
            summary["property_date_gone"] = max(property_date_gone_candidates).isoformat()
        
        return summary
    

class PropertyURLCRUD:
    @staticmethod
    def create_property_url(
        db: Session, 
        property_id: str, 
        url: str, 
        is_primary: bool = False,
        confidence_score: float = None
    ) -> PropertyURL:
        """Create a new property URL mapping"""
        from models import PropertyURL
        
        property_url = PropertyURL(
            property_id=property_id,
            url=url,
            is_primary=is_primary,
            confidence_score=confidence_score
        )
        db.add(property_url)
        db.commit()
        db.refresh(property_url)
        return property_url
    
    @staticmethod
    def get_property_urls(db: Session, property_id: str) -> List[PropertyURL]:
        """Get all URLs for a property"""
        return db.query(PropertyURL).filter(PropertyURL.property_id == property_id).all()
    
    @staticmethod
    def get_property_by_any_url(db: Session, url: str) -> Optional[Property]:
        """Find property by any of its URLs (primary or additional)"""
        # First check the main property table (primary URLs)
        property = db.query(Property).filter(Property.url == url).first()
        if property:
            return property
        
        # Then check additional URLs in property_urls table
        property_url = db.query(PropertyURL).filter(PropertyURL.url == url).first()
        if property_url:
            return db.query(Property).filter(Property.id == property_url.property_id).first()
        
        return None
    
    @staticmethod
    def link_url_to_property(
        db: Session, 
        property_id: str, 
        new_url: str, 
        confidence_score: float
    ) -> PropertyURL:
        """Link a new URL to an existing property"""
        # Check if URL already exists
        existing = db.query(PropertyURL).filter(PropertyURL.url == new_url).first()
        if existing:
            raise ValueError("URL already exists in database")
        
        # Create new URL mapping
        return PropertyURLCRUD.create_property_url(
            db, property_id, new_url, is_primary=False, confidence_score=confidence_score
        )

def calculate_property_date_gone(db: Session, property_id) -> Optional[str]:
    """Calculate when a property went offline (all rooms became unavailable)"""
    
    summary = RoomAvailabilityPeriodCRUD.get_property_period_summary(db, property_id)
    return summary.get("property_date_gone")

def get_property_availability_summary(db: Session, property_id) -> Dict[str, Any]:
    """Get a comprehensive availability summary for a property"""
    
    return RoomAvailabilityPeriodCRUD.get_property_period_summary(db, property_id)

def get_price_trend_direction(price_changes: List[float]) -> str:
    """Determine overall price trend direction from a list of changes"""
    if not price_changes:
        return 'stable'
    
    positive_changes = sum(1 for change in price_changes if change > 0)
    negative_changes = sum(1 for change in price_changes if change < 0)
    
    if positive_changes > negative_changes * 1.5:
        return 'increasing'
    elif negative_changes > positive_changes * 1.5:
        return 'decreasing'
    else:
        return 'stable'
    