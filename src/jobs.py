import uuid
import threading
import time
import logging
from typing import Dict, Any, List, Callable, Optional

logger = logging.getLogger("QuickCart.Jobs")

class BackgroundJobManager:
    """
    Manages asynchronous background processing for time-consuming jobs.
    Uses native threads for daemon execution and memory maps for state tracking.
    """
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(BackgroundJobManager, cls).__new__(cls)
                cls._instance._jobs = {}
                cls._instance._jobs_lock = threading.Lock()
            return cls._instance

    def submit_job(self, job_type: str, target_func: Callable, *args, **kwargs) -> str:
        """
        Submits a function for background execution.
        Returns a unique job_id.
        """
        job_id = f"JOB_{uuid.uuid4().hex[:8].upper()}"
        
        job_info = {
            "job_id": job_id,
            "job_type": job_type,
            "status": "Queued",
            "progress": 0,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "completed_at": None,
            "result": None,
            "error": None
        }
        
        with self._jobs_lock:
            self._jobs[job_id] = job_info
            
        # Spawn thread
        t = threading.Thread(
            target=self._run_job,
            args=(job_id, target_func, args, kwargs),
            daemon=True
        )
        t.start()
        
        logger.info(f"Submitted background job {job_id} (Type: {job_type})")
        return job_id

    def _run_job(self, job_id: str, func: Callable, args: tuple, kwargs: dict):
        """
        Thread execution wrapper. Updates state throughout run.
        """
        self.update_job(job_id, status="Running", progress=10)
        
        try:
            # Inject a mechanism for jobs to report progress if they accept a progress_callback
            if "progress_callback" in func.__code__.co_varnames:
                def progress_cb(pct: int):
                    self.update_job(job_id, progress=min(max(pct, 10), 95))
                kwargs["progress_callback"] = progress_cb
                
            result = func(*args, **kwargs)
            
            self.update_job(
                job_id, 
                status="Completed", 
                progress=100, 
                result=result, 
                completed_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            logger.info(f"Background job {job_id} completed successfully.")
        except Exception as e:
            logger.exception(f"Background job {job_id} failed: {e}")
            self.update_job(
                job_id, 
                status="Failed", 
                progress=100, 
                error=str(e), 
                completed_at=time.strftime("%Y-%m-%d %H:%M:%S")
            )

    def update_job(self, job_id: str, **kwargs):
        """
        Updates the key/values of a job record in a thread-safe manner.
        """
        with self._jobs_lock:
            if job_id in self._jobs:
                for k, v in kwargs.items():
                    self._jobs[job_id][k] = v

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves a job by its ID.
        """
        with self._jobs_lock:
            return self._jobs.get(job_id)

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """
        Returns all jobs sorted by creation time descending.
        """
        with self._jobs_lock:
            return sorted(self._jobs.values(), key=lambda j: j["created_at"], reverse=True)

    def clear_jobs(self):
        """
        Clears completed/failed jobs from history.
        """
        with self._jobs_lock:
            active_jobs = {
                jid: jinfo for jid, jinfo in self._jobs.items() 
                if jinfo["status"] in ["Queued", "Running"]
            }
            self._jobs = active_jobs
            logger.info("Cleared completed background jobs history.")
