"""
Stage Registry and Cache Management.

This module provides thread-safe registry and caching functionality for USD stages.
"""

from pxr import Usd
import os
import threading
import time
import uuid
import logging
from typing import Dict, Optional, List, Any, Set

logger = logging.getLogger(__name__)

# Global variables for stage management
stage_cache = {}
stage_access_times = {}
stage_modified = {}
MAX_CACHE_SIZE = 10
CACHE_MAINTENANCE_INTERVAL = 300  # 5 minutes

class StageRegistry:
    """Thread-safe registry for managing USD stages.
    
    This registry:
    1. Maintains a map of stage_id → Usd.Stage objects
    2. Tracks file paths associated with each stage
    3. Tracks modification status for each stage
    4. Implements LRU cache functionality with access times
    """
    
    def __init__(self, max_cache_size=10):
        """Initialize the stage registry with specified cache size.
        
        Args:
            max_cache_size: Maximum number of stages to keep in memory
        """
        self._stages = {}  # Map of stage_id → Usd.Stage
        self._stage_file_paths = {}  # Map of stage_id → file_path
        self._stage_access_times = {}  # Map of stage_id → last_access_time
        self._stage_modified = {}  # Map of stage_id → is_modified
        self._lock = threading.Lock()
        self.max_cache_size = max_cache_size
    
    def register_stage(self, file_path, stage):
        """Register a stage with the registry and return its unique ID.
        
        Args:
            file_path: Path to the USD file associated with this stage
            stage: The Usd.Stage object to register
            
        Returns:
            str: A unique stage_id for this stage
        """
        with self._lock:
            stage_id = str(uuid.uuid4())
            self._stages[stage_id] = stage
            self._stage_file_paths[stage_id] = file_path
            self._stage_access_times[stage_id] = time.time()
            self._stage_modified[stage_id] = False
            
            # Check if we need to clean up the cache
            if len(self._stages) > self.max_cache_size:
                self.perform_cache_cleanup()
                
            return stage_id
    
    def get_stage(self, stage_id):
        """Get a stage by its ID and update its access time.
        
        Args:
            stage_id: The unique ID of the stage to retrieve
            
        Returns:
            Usd.Stage or None: The stage if found, None otherwise
        """
        with self._lock:
            if stage_id in self._stages:
                # Update access time
                self._stage_access_times[stage_id] = time.time()
                return self._stages[stage_id]
            return None
    
    def get_stage_path(self, stage_id):
        """Get the file path associated with a stage.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            str or None: The file path if found, None otherwise
        """
        with self._lock:
            return self._stage_file_paths.get(stage_id)
    
    def mark_as_modified(self, stage_id):
        """Mark a stage as having unsaved modifications.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            bool: True if the stage was found and marked, False otherwise
        """
        with self._lock:
            if stage_id in self._stages:
                self._stage_modified[stage_id] = True
                return True
            return False
    
    def is_modified(self, stage_id):
        """Check if a stage has unsaved modifications.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            bool: True if the stage has unsaved modifications, False otherwise
        """
        with self._lock:
            return self._stage_modified.get(stage_id, False)
    
    def save_stage(self, stage_id):
        """Save a stage if it has been modified.
        
        Args:
            stage_id: The unique ID of the stage
            
        Returns:
            bool: True if the stage was saved, False otherwise
        """
        with self._lock:
            if stage_id in self._stages and self._stage_modified.get(stage_id, False):
                try:
                    self._stages[stage_id].GetRootLayer().Save()
                    self._stage_modified[stage_id] = False
                    return True
                except Exception as e:
                    logger.exception(f"Error saving stage {stage_id}: {str(e)}")
                    return False
            return False
    
    def unregister_stage(self, stage_id, save_if_modified=True):
        """Unregister a stage and optionally save it if modified.
        
        Args:
            stage_id: The unique ID of the stage
            save_if_modified: Whether to save the stage if it has been modified
            
        Returns:
            bool: True if the stage was found and unregistered, False otherwise
        """
        with self._lock:
            if stage_id in self._stages:
                stage = self._stages[stage_id]
                
                # Save if modified and requested
                if save_if_modified and self._stage_modified.get(stage_id, False):
                    try:
                        stage.GetRootLayer().Save()
                    except Exception as e:
                        logger.exception(f"Error saving stage during unregister: {str(e)}")
                
                # Unload stage and remove from registry
                stage.Unload()
                del self._stages[stage_id]
                del self._stage_file_paths[stage_id]
                del self._stage_access_times[stage_id]
                del self._stage_modified[stage_id]
                
                return True
            return False
    
    def perform_cache_cleanup(self):
        """Clean up the stage cache based on LRU policy.
        
        This will unload and unregister the least recently used stages.
        
        Returns:
            int: Number of stages removed
        """
        with self._lock:
            # No cleanup needed if under size limit
            if len(self._stages) <= self.max_cache_size:
                return 0
            
            # Sort stages by access time (oldest first)
            sorted_ids = sorted(self._stage_access_times.keys(), 
                              key=lambda k: self._stage_access_times[k])
            
            # Calculate how many stages to remove
            num_to_remove = len(self._stages) - self.max_cache_size
            stages_to_remove = sorted_ids[:num_to_remove]
            
            # Remove the oldest stages
            for stage_id in stages_to_remove:
                self.unregister_stage(stage_id, save_if_modified=True)
            
            return len(stages_to_remove)
    
    def get_all_stage_ids(self):
        """Get a list of all registered stage IDs.
        
        Returns:
            list: List of all stage IDs in the registry
        """
        with self._lock:
            return list(self._stages.keys())
    
    def get_stats(self):
        """Get statistics about the stage registry.
        
        Returns:
            dict: Statistics about the registry
        """
        with self._lock:
            return {
                "total_stages": len(self._stages),
                "max_cache_size": self.max_cache_size,
                "modified_stages": sum(1 for v in self._stage_modified.values() if v),
                "stage_ids": list(self._stages.keys())
            }

# Create a global instance
stage_registry = StageRegistry(max_cache_size=MAX_CACHE_SIZE)

def cleanup_stage_cache():
    """Remove least recently used stages from cache if cache exceeds maximum size"""
    global stage_cache, stage_access_times, stage_modified
    
    if len(stage_cache) <= MAX_CACHE_SIZE:
        return
    
    # Get list of stages sorted by access time (oldest first)
    sorted_stages = sorted(stage_access_times.items(), key=lambda x: x[1])
    
    # Number of stages to remove
    num_to_remove = len(stage_cache) - MAX_CACHE_SIZE
    
    # Remove oldest stages
    for i in range(num_to_remove):
        stage_path = sorted_stages[i][0]
        if stage_path in stage_cache:
            try:
                logger.info(f"Unloading stage from cache: {stage_path}")
                # Check if stage is modified
                if stage_path in stage_modified and stage_modified[stage_path]:
                    logger.warning(f"Unloading modified stage: {stage_path}")
                    # Save stage before unloading
                    stage_cache[stage_path].GetRootLayer().Save()
                # Unload the stage
                stage_cache[stage_path].Unload()
                # Remove from cache and tracking
                del stage_cache[stage_path]
                del stage_access_times[stage_path]
                if stage_path in stage_modified:
                    del stage_modified[stage_path]
            except Exception as e:
                logger.exception(f"Error unloading stage {stage_path}: {e}")

def maintain_stage_cache():
    """Background thread function to maintain the stage cache"""
    while True:
        try:
            time.sleep(CACHE_MAINTENANCE_INTERVAL)
            cleanup_stage_cache()
        except Exception as e:
            logger.exception(f"Error during cache maintenance: {e}")

def maintain_stage_registry():
    """Background thread function to periodically maintain the stage registry.
    
    This function:
    1. Performs cache cleanup based on LRU policy
    2. Saves modified stages periodically
    """
    logger.info("Stage registry maintenance thread started")
    
    while True:
        try:
            # Sleep for the maintenance interval
            time.sleep(300)  # Every 5 minutes
            
            # Perform cache cleanup if needed
            stages_removed = stage_registry.perform_cache_cleanup()
            if stages_removed > 0:
                logger.info(f"Stage registry maintenance: removed {stages_removed} stages from cache")
            
            # Get statistics
            stats = stage_registry.get_stats()
            logger.debug(f"Stage registry stats: {stats}")
            
        except Exception as e:
            logger.exception(f"Error in stage registry maintenance thread: {str(e)}")
            # Continue running even if there was an error

def start_maintenance_threads():
    """Start the maintenance threads for cache and registry"""
    # Start the cache maintenance thread
    cache_thread = threading.Thread(target=maintain_stage_cache, daemon=True)
    cache_thread.start()

    # Start the stage registry maintenance thread
    registry_thread = threading.Thread(target=maintain_stage_registry, daemon=True)
    registry_thread.start()
    
    return cache_thread, registry_thread 