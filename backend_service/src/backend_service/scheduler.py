"""
Background scheduler for periodic flood status checks.
Uses APScheduler with AsyncIOScheduler for FastAPI compatibility.
"""
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from typing import Optional

from .logger import logger
from . import config
from .camera_service import get_camera_service
from .flood_state import get_flood_state_manager
from .ai_service import check_flood_status_for_all

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


async def check_all_cameras_flood_status() -> None:
    """
    Background job to check flood status for all cameras.
    Updates the FloodStateManager with results.
    """
    flood_manager = get_flood_state_manager()
    
    # Skip if in test mode
    if flood_manager.test_mode:
        logger.info("Skipping flood check - test mode is active")
        return
    
    logger.info("Starting scheduled flood status check for all cameras")
    start_time = datetime.now()
    
    try:
        camera_service = get_camera_service()
        all_camera_ids = list(camera_service.cameras.keys())
        
        logger.info(f"Checking {len(all_camera_ids)} cameras...")
        
        # Call AI service to check all cameras
        results = await check_flood_status_for_all(all_camera_ids)
        
        # Update flood state manager
        for cam_id, result in results.items():
            flood_manager.update_camera_state(
                camera_id=cam_id,
                is_flooded=result.get('is_flooded', False),
                confidence=result.get('confidence', 0.0)
            )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        flooded_count = flood_manager.get_flooded_count()
        logger.info(
            f"Flood check completed in {elapsed:.1f}s: "
            f"{flooded_count}/{len(all_camera_ids)} cameras flooded"
        )
        
    except Exception as e:
        logger.error(f"Error during scheduled flood check: {e}", exc_info=True)


def get_scheduler() -> Optional[AsyncIOScheduler]:
    """Get the global scheduler instance."""
    return _scheduler


def init_scheduler() -> AsyncIOScheduler:
    """
    Initialize and configure the background scheduler.
    
    Returns:
        Configured AsyncIOScheduler instance
    """
    global _scheduler
    
    if _scheduler is not None:
        return _scheduler
    
    _scheduler = AsyncIOScheduler()
    
    # Add the flood check job
    _scheduler.add_job(
        check_all_cameras_flood_status,
        trigger=IntervalTrigger(minutes=config.FLOOD_CHECK_INTERVAL_MINUTES),
        id='flood_check_job',
        name='Check flood status for all cameras',
        replace_existing=True
    )
    
    logger.info(
        f"Scheduler configured: flood check every {config.FLOOD_CHECK_INTERVAL_MINUTES} minutes"
    )
    
    return _scheduler


async def trigger_immediate_flood_check() -> None:
    """Trigger an immediate flood check (for startup or manual trigger)."""
    logger.info("Triggering immediate flood status check")
    await check_all_cameras_flood_status()


def start_scheduler() -> None:
    """Start the scheduler."""
    global _scheduler
    if _scheduler and not _scheduler.running:
        _scheduler.start()
        logger.info("Scheduler started")


def stop_scheduler() -> None:
    """Stop the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler stopped")
