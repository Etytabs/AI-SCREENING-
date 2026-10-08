"""
Repository Service - Repository Synchronization (E08)
Manages synchronization with external repositories and handles diffs
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import os
import sys
import hashlib
import json
from enum import Enum

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="Repository Service",
    description="Repository synchronization and diff management",
    version="2.0.0"
)


class SyncStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_REVIEW = "requires_review"


class RepositoryType(str, Enum):
    GRANT_SYSTEM = "grant_system"
    PUBLICATION_DB = "publication_db"
    PATENT_DB = "patent_db"
    INSTITUTIONAL_REPO = "institutional_repo"


class SyncRequest(BaseModel):
    """Request to synchronize with external repository"""
    repository_type: RepositoryType
    repository_url: str
    sync_mode: str = "full"  # full, incremental, dry_run
    filters: Optional[Dict[str, Any]] = None


class SyncResult(BaseModel):
    """Result of synchronization operation"""
    sync_id: str
    repository_type: RepositoryType
    status: SyncStatus
    records_processed: int
    records_created: int
    records_updated: int
    records_deleted: int
    records_skipped: int
    errors: List[str] = []
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class DiffRecord(BaseModel):
    """Record representing a change/diff"""
    record_id: str
    record_type: str
    change_type: str  # created, updated, deleted
    old_value: Optional[Dict[str, Any]] = None
    new_value: Optional[Dict[str, Any]] = None
    changed_fields: List[str] = []
    change_hash: str
    detected_at: datetime


class ReconciliationRequest(BaseModel):
    """Request to reconcile conflicting writes"""
    sync_id: str
    conflict_records: List[str]
    resolution_strategy: str  # latest, source, target, manual


# In-memory storage (in production, use database)
sync_operations = {}
diff_records = {}


def generate_sync_id() -> str:
    """Generate unique sync operation ID"""
    return f"SYNC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{hashlib.md5(os.urandom(8)).hexdigest()[:8].upper()}"


def compute_record_hash(record: Dict) -> str:
    """Compute hash of record for change detection"""
    record_str = json.dumps(record, sort_keys=True)
    return hashlib.sha256(record_str.encode()).hexdigest()


async def perform_sync(
    sync_id: str,
    request: SyncRequest
) -> SyncResult:
    """Perform repository synchronization (mock implementation)"""
    sync_operations[sync_id]["status"] = SyncStatus.RUNNING
    sync_operations[sync_id]["started_at"] = datetime.utcnow()
    
    # Mock sync operation
    import asyncio
    await asyncio.sleep(2)  # Simulate sync work
    
    # Mock results
    result = SyncResult(
        sync_id=sync_id,
        repository_type=request.repository_type,
        status=SyncStatus.COMPLETED,
        records_processed=100,
        records_created=15,
        records_updated=45,
        records_deleted=3,
        records_skipped=37,
        errors=[],
        started_at=sync_operations[sync_id]["started_at"],
        completed_at=datetime.utcnow(),
        duration_seconds=2.0
    )
    
    sync_operations[sync_id] = result.dict()
    
    return result


@app.get("/")
async def root():
    return {
        "service": "Repository Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/sync", response_model=SyncResult)
async def start_sync(
    request: SyncRequest,
    background_tasks: BackgroundTasks
):
    """Start repository synchronization"""
    sync_id = generate_sync_id()
    
    sync_operations[sync_id] = {
        "sync_id": sync_id,
        "repository_type": request.repository_type,
        "status": SyncStatus.PENDING
    }
    
    background_tasks.add_task(perform_sync, sync_id, request)
    
    return SyncResult(
        sync_id=sync_id,
        repository_type=request.repository_type,
        status=SyncStatus.PENDING,
        records_processed=0,
        records_created=0,
        records_updated=0,
        records_deleted=0,
        records_skipped=0,
        started_at=datetime.utcnow()
    )


@app.get("/sync/{sync_id}", response_model=SyncResult)
async def get_sync_status(sync_id: str):
    """Get synchronization status"""
    if sync_id not in sync_operations:
        raise HTTPException(status_code=404, detail="Sync operation not found")
    
    return SyncResult(**sync_operations[sync_id])


@app.get("/sync")
async def list_sync_operations(
    status: Optional[SyncStatus] = None,
    repository_type: Optional[RepositoryType] = None
):
    """List synchronization operations"""
    operations = list(sync_operations.values())
    
    if status:
        operations = [op for op in operations if op.get("status") == status]
    
    if repository_type:
        operations = [op for op in operations if op.get("repository_type") == repository_type]
    
    return {
        "operations": operations,
        "total": len(operations)
    }


@app.post("/diff")
async def create_diff(
    old_record: Dict[str, Any],
    new_record: Dict[str, Any],
    record_id: str,
    record_type: str
):
    """Create a diff record between two versions"""
    old_hash = compute_record_hash(old_record)
    new_hash = compute_record_hash(new_record)
    
    if old_hash == new_hash:
        return {"message": "No changes detected", "change_type": "none"}
    
    # Detect changed fields
    changed_fields = []
    for key in set(old_record.keys()) | set(new_record.keys()):
        if old_record.get(key) != new_record.get(key):
            changed_fields.append(key)
    
    # Determine change type
    if not old_record:
        change_type = "created"
    elif not new_record:
        change_type = "deleted"
    else:
        change_type = "updated"
    
    diff = DiffRecord(
        record_id=record_id,
        record_type=record_type,
        change_type=change_type,
        old_value=old_record if change_type != "created" else None,
        new_value=new_record if change_type != "deleted" else None,
        changed_fields=changed_fields,
        change_hash=new_hash,
        detected_at=datetime.utcnow()
    )
    
    diff_id = f"{record_id}-{new_hash[:8]}"
    diff_records[diff_id] = diff.dict()
    
    return {
        "diff_id": diff_id,
        "change_type": change_type,
        "changed_fields": changed_fields,
        "change_hash": new_hash
    }


@app.get("/diff/{diff_id}")
async def get_diff(diff_id: str):
    """Get diff record"""
    if diff_id not in diff_records:
        raise HTTPException(status_code=404, detail="Diff record not found")
    
    return diff_records[diff_id]


@app.post("/reconcile")
async def reconcile_conflicts(request: ReconciliationRequest):
    """Reconcile conflicting writes"""
    if request.sync_id not in sync_operations:
        raise HTTPException(status_code=404, detail="Sync operation not found")
    
    # Mock reconciliation
    reconciliation_result = {
        "sync_id": request.sync_id,
        "conflicts_resolved": len(request.conflict_records),
        "resolution_strategy": request.resolution_strategy,
        "resolved_at": datetime.utcnow()
    }
    
    return reconciliation_result


@app.post("/sync/{sync_id}/dry-run")
async def dry_run_sync(
    sync_id: str,
    request: SyncRequest
):
    """Perform a dry-run sync without making changes"""
    return {
        "sync_id": sync_id,
        "mode": "dry_run",
        "estimated_changes": {
            "records_to_create": 15,
            "records_to_update": 45,
            "records_to_delete": 3
        },
        "warning": "No actual changes will be made"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)
