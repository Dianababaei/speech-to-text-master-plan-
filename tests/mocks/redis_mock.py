"""
Mock Redis and RQ (Redis Queue) services for testing.

Provides in-memory mock implementations of Redis and RQ functionality
without requiring an actual Redis server.
"""
from typing import Optional, Dict, Any, List
from unittest.mock import MagicMock
from datetime import datetime
import uuid


class MockRedisConnection:
    """Mock Redis connection for testing."""
    
    def __init__(self):
        """Initialize mock Redis with in-memory storage."""
        self._data: Dict[str, Any] = {}
        self._connected = True
    
    def ping(self) -> bool:
        """Mock ping command."""
        if not self._connected:
            raise ConnectionError("Redis connection lost")
        return True
    
    def get(self, key: str) -> Optional[str]:
        """Mock get command."""
        return self._data.get(key)
    
    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """Mock set command."""
        self._data[key] = value
        return True
    
    def delete(self, *keys: str) -> int:
        """Mock delete command."""
        count = 0
        for key in keys:
            if key in self._data:
                del self._data[key]
                count += 1
        return count
    
    def exists(self, *keys: str) -> int:
        """Mock exists command."""
        return sum(1 for key in keys if key in self._data)
    
    def keys(self, pattern: str = "*") -> List[str]:
        """Mock keys command."""
        # Simple pattern matching (only supports * wildcard)
        if pattern == "*":
            return list(self._data.keys())
        # Basic pattern matching
        prefix = pattern.replace("*", "")
        return [k for k in self._data.keys() if k.startswith(prefix)]
    
    def flushdb(self) -> bool:
        """Mock flushdb command."""
        self._data.clear()
        return True
    
    def disconnect(self):
        """Mock disconnect."""
        self._connected = False
    
    @classmethod
    def from_url(cls, url: str, **kwargs):
        """Mock from_url class method."""
        return cls()


class MockRQJob:
    """Mock RQ Job for testing."""
    
    def __init__(
        self,
        job_id: str,
        func_name: str = "process_transcription_job",
        status: str = "queued",
        result: Optional[Any] = None,
        exc_info: Optional[str] = None,
        meta: Optional[Dict] = None
    ):
        """Initialize mock job."""
        self.id = job_id
        self.func_name = func_name
        self._status = status
        self.result = result
        self.exc_info = exc_info
        self.meta = meta or {}
        self.created_at = datetime.utcnow()
        self.started_at = datetime.utcnow() if status in ["started", "finished", "failed"] else None
        self.ended_at = datetime.utcnow() if status in ["finished", "failed"] else None
        self.is_finished = status == "finished"
        self.is_failed = status == "failed"
        self.is_queued = status == "queued"
        self.is_started = status == "started"
    
    def get_status(self) -> str:
        """Get current job status."""
        return self._status
    
    def set_status(self, status: str):
        """Set job status."""
        self._status = status
        self.is_finished = status == "finished"
        self.is_failed = status == "failed"
        self.is_queued = status == "queued"
        self.is_started = status == "started"
        
        if status == "started" and not self.started_at:
            self.started_at = datetime.utcnow()
        if status in ["finished", "failed"] and not self.ended_at:
            self.ended_at = datetime.utcnow()
    
    def cancel(self):
        """Cancel the job."""
        self._status = "canceled"
    
    def delete(self):
        """Delete the job."""
        pass
    
    @classmethod
    def fetch(cls, job_id: str, connection=None):
        """Mock fetch method."""
        # This will be overridden by the queue mock
        raise Exception(f"Job {job_id} not found")


class MockRQQueue:
    """Mock RQ Queue for testing."""
    
    def __init__(self, name: str = "transcription_jobs", connection=None, default_timeout: int = 300):
        """Initialize mock queue."""
        self.name = name
        self.connection = connection or MockRedisConnection()
        self.default_timeout = default_timeout
        self._jobs: Dict[str, MockRQJob] = {}
        self._job_order: List[str] = []
    
    def enqueue(
        self,
        func,
        args=None,
        kwargs=None,
        job_id: Optional[str] = None,
        timeout: Optional[int] = None,
        result_ttl: Optional[int] = None,
        failure_ttl: Optional[int] = None,
        retry=None,
        meta: Optional[Dict] = None
    ) -> MockRQJob:
        """Mock enqueue method."""
        if job_id is None:
            job_id = str(uuid.uuid4())
        
        job = MockRQJob(
            job_id=job_id,
            func_name=func.__name__ if hasattr(func, "__name__") else str(func),
            status="queued",
            meta=meta
        )
        
        self._jobs[job_id] = job
        self._job_order.append(job_id)
        
        return job
    
    def fetch_job(self, job_id: str) -> Optional[MockRQJob]:
        """Fetch a job by ID."""
        return self._jobs.get(job_id)
    
    def get_jobs(self, status: Optional[str] = None) -> List[MockRQJob]:
        """Get all jobs, optionally filtered by status."""
        if status:
            return [job for job in self._jobs.values() if job.get_status() == status]
        return list(self._jobs.values())
    
    def __len__(self) -> int:
        """Get count of queued jobs."""
        return sum(1 for job in self._jobs.values() if job.is_queued)
    
    @property
    def finished_job_registry(self):
        """Mock finished job registry."""
        mock_registry = MagicMock()
        mock_registry.get_job_ids.return_value = [
            job_id for job_id, job in self._jobs.items() if job.is_finished
        ]
        return mock_registry
    
    @property
    def failed_job_registry(self):
        """Mock failed job registry."""
        mock_registry = MagicMock()
        mock_registry.get_job_ids.return_value = [
            job_id for job_id, job in self._jobs.items() if job.is_failed
        ]
        return mock_registry


def create_mock_redis() -> MockRedisConnection:
    """
    Create a mock Redis connection.
    
    Returns:
        MockRedisConnection instance
    """
    return MockRedisConnection()


def create_mock_queue(name: str = "transcription_jobs") -> MockRQQueue:
    """
    Create a mock RQ queue.
    
    Args:
        name: Queue name
    
    Returns:
        MockRQQueue instance
    """
    return MockRQQueue(name=name)


def create_mock_job(
    job_id: Optional[str] = None,
    status: str = "queued",
    result: Optional[Any] = None,
    error: Optional[str] = None
) -> MockRQJob:
    """
    Create a mock RQ job.
    
    Args:
        job_id: Job ID (generates random UUID if not provided)
        status: Job status (queued, started, finished, failed)
        result: Job result (for finished jobs)
        error: Error message (for failed jobs)
    
    Returns:
        MockRQJob instance
    """
    if job_id is None:
        job_id = str(uuid.uuid4())
    
    return MockRQJob(
        job_id=job_id,
        status=status,
        result=result,
        exc_info=error
    )


# Preset mock configurations for common scenarios
def get_empty_queue() -> MockRQQueue:
    """Get an empty mock queue."""
    return create_mock_queue()


def get_queue_with_jobs(count: int = 5) -> MockRQQueue:
    """Get a mock queue with test jobs."""
    queue = create_mock_queue()
    for i in range(count):
        job_id = f"test-job-{i+1}"
        queue.enqueue(
            func=lambda: None,
            job_id=job_id,
            meta={"test": True}
        )
    return queue


def get_queue_with_failed_jobs(count: int = 3) -> MockRQQueue:
    """Get a mock queue with failed jobs."""
    queue = create_mock_queue()
    for i in range(count):
        job_id = f"failed-job-{i+1}"
        job = MockRQJob(
            job_id=job_id,
            status="failed",
            exc_info="Test error"
        )
        queue._jobs[job_id] = job
    return queue


def get_connected_redis() -> MockRedisConnection:
    """Get a connected mock Redis instance."""
    return create_mock_redis()


def get_disconnected_redis() -> MockRedisConnection:
    """Get a disconnected mock Redis instance."""
    redis = create_mock_redis()
    redis.disconnect()
    return redis
