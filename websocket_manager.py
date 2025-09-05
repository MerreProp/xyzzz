"""
WebSocket Manager for Real-Time Task Updates
Provides live progress updates to frontend during property analysis
"""

import asyncio
import json
from typing import Dict, Set, Optional
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""
    
    def __init__(self):
        # Store active connections by task_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Store connection metadata
        self.connection_metadata: Dict[WebSocket, Dict] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """Accept a new WebSocket connection for a specific task"""
        await websocket.accept()
        
        if task_id not in self.active_connections:
            self.active_connections[task_id] = set()
        
        self.active_connections[task_id].add(websocket)
        self.connection_metadata[websocket] = {
            'task_id': task_id,
            'connected_at': datetime.now(),
            'last_message_at': None
        }
        
        logger.info(f"WebSocket connected for task {task_id}. Total connections: {len(self.active_connections[task_id])}")
        
        # Send initial connection confirmation
        await self.send_to_connection(websocket, {
            'type': 'connection_established',
            'task_id': task_id,
            'timestamp': datetime.now().isoformat(),
            'message': 'Connected to task updates'
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.connection_metadata:
            task_id = self.connection_metadata[websocket]['task_id']
            
            # Remove from active connections
            if task_id in self.active_connections:
                self.active_connections[task_id].discard(websocket)
                
                # Clean up empty task sets
                if not self.active_connections[task_id]:
                    del self.active_connections[task_id]
            
            # Remove metadata
            del self.connection_metadata[websocket]
            
            logger.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_to_connection(self, websocket: WebSocket, data: dict):
        """Send data to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(data))
            
            # Update last message timestamp
            if websocket in self.connection_metadata:
                self.connection_metadata[websocket]['last_message_at'] = datetime.now()
                
        except Exception as e:
            logger.error(f"Error sending message to WebSocket: {e}")
            self.disconnect(websocket)
    
    async def broadcast_to_task(self, task_id: str, data: dict):
        """Broadcast data to all connections listening to a specific task"""
        if task_id not in self.active_connections:
            logger.debug(f"No active connections for task {task_id}")
            return
        
        # Add task_id and timestamp to the data
        data.update({
            'task_id': task_id,
            'timestamp': datetime.now().isoformat()
        })
        
        # Send to all connections for this task
        connections = self.active_connections[task_id].copy()  # Copy to avoid modification during iteration
        
        for websocket in connections:
            await self.send_to_connection(websocket, data)
        
        logger.debug(f"Broadcasted message to {len(connections)} connections for task {task_id}")
    
    async def send_progress_update(self, task_id: str, stage: str, progress_percent: int, details: Optional[str] = None):
        """Send a progress update for a task"""
        await self.broadcast_to_task(task_id, {
            'type': 'progress_update',
            'stage': stage,
            'progress_percent': progress_percent,
            'details': details,
            'status': 'running'
        })
    
    async def send_stage_complete(self, task_id: str, stage: str, result_data: Optional[dict] = None):
        """Send notification that a stage is complete"""
        await self.broadcast_to_task(task_id, {
            'type': 'stage_complete',
            'stage': stage,
            'result_data': result_data,
            'status': 'stage_complete'
        })
    
    async def send_task_complete(self, task_id: str, result_data: dict):
        """Send notification that entire task is complete"""
        await self.broadcast_to_task(task_id, {
            'type': 'task_complete',
            'result_data': result_data,
            'status': 'completed'
        })
    
    async def send_task_error(self, task_id: str, error_message: str, stage: Optional[str] = None):
        """Send error notification"""
        await self.broadcast_to_task(task_id, {
            'type': 'task_error',
            'error_message': error_message,
            'stage': stage,
            'status': 'failed'
        })
    
    def get_connection_stats(self) -> dict:
        """Get statistics about active connections"""
        total_connections = sum(len(connections) for connections in self.active_connections.values())
        
        return {
            'total_connections': total_connections,
            'active_tasks': len(self.active_connections),
            'tasks': {
                task_id: len(connections) 
                for task_id, connections in self.active_connections.items()
            }
        }

# Global connection manager instance
connection_manager = ConnectionManager()

# WebSocket endpoint functions for FastAPI
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """Main WebSocket endpoint for task updates"""
    await connection_manager.connect(websocket, task_id)
    
    try:
        while True:
            # Keep connection alive by waiting for messages
            # In practice, this will mostly receive ping messages
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping messages
                message = json.loads(data)
                if message.get('type') == 'ping':
                    await connection_manager.send_to_connection(websocket, {
                        'type': 'pong',
                        'timestamp': datetime.now().isoformat()
                    })
            
            except asyncio.TimeoutError:
                # Send periodic heartbeat to keep connection alive
                await connection_manager.send_to_connection(websocket, {
                    'type': 'heartbeat',
                    'timestamp': datetime.now().isoformat()
                })
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for task {task_id}")
    except Exception as e:
        logger.error(f"WebSocket error for task {task_id}: {e}")
    finally:
        connection_manager.disconnect(websocket)

# Helper functions for use in background tasks
async def notify_progress(task_id: str, stage: str, progress_percent: int, details: str = None):
    """Helper function to send progress updates from background tasks"""
    await connection_manager.send_progress_update(task_id, stage, progress_percent, details)

async def notify_stage_complete(task_id: str, stage: str, result_data: dict = None):
    """Helper function to notify stage completion from background tasks"""
    await connection_manager.send_stage_complete(task_id, stage, result_data)

async def notify_task_complete(task_id: str, result_data: dict):
    """Helper function to notify task completion from background tasks"""
    await connection_manager.send_task_complete(task_id, result_data)

async def notify_task_error(task_id: str, error_message: str, stage: str = None):
    """Helper function to notify task errors from background tasks"""
    await connection_manager.send_task_error(task_id, error_message, stage)