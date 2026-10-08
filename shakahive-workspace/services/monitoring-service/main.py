"""
Monitoring Service - Security and Operations (E10)
Provides metrics, logging, and monitoring for all services
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import os
import sys
import hashlib
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

app = FastAPI(
    title="Monitoring Service",
    description="Security and operations monitoring",
    version="2.0.0"
)

# Prometheus Metrics
request_counter = Counter('novarai_requests_total', 'Total requests', ['service', 'endpoint', 'method'])
request_duration = Histogram('novarai_request_duration_seconds', 'Request duration', ['service'])
active_connections = Gauge('novarai_active_connections', 'Active connections', ['service'])
error_counter = Counter('novarai_errors_total', 'Total errors', ['service', 'error_type'])
screening_duration = Histogram('novarai_screening_duration_seconds', 'Screening duration')
service_health = Gauge('novarai_service_health', 'Service health status', ['service'])


class ServiceHealth(BaseModel):
    """Service health status"""
    service_name: str
    status: str  # healthy, degraded, unhealthy
    uptime_seconds: float
    last_check: datetime
    metrics: Dict[str, Any] = {}


class Alert(BaseModel):
    """Alert model"""
    alert_id: str
    severity: str  # critical, warning, info
    service: str
    message: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class SecurityEvent(BaseModel):
    """Security event model"""
    event_id: str
    event_type: str  # unauthorized_access, cross_tenant_attempt, rate_limit_exceeded
    service: str
    user_id: Optional[str] = None
    tenant_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)


# In-memory storage
service_healths = {}
alerts = {}
security_events = {}


@app.get("/")
async def root():
    return {
        "service": "Monitoring Service",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    from fastapi.responses import Response
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/services/{service_name}/health")
async def report_service_health(
    service_name: str,
    status: str,
    uptime_seconds: float,
    metrics: Optional[Dict[str, Any]] = None
):
    """Report health status from a service"""
    health = ServiceHealth(
        service_name=service_name,
        status=status,
        uptime_seconds=uptime_seconds,
        last_check=datetime.utcnow(),
        metrics=metrics or {}
    )
    
    service_healths[service_name] = health.dict()
    
    # Update Prometheus gauge
    service_health.labels(service=service_name).set(
        1 if status == "healthy" else 0.5 if status == "degraded" else 0
    )
    
    return {"message": "Health status recorded"}


@app.get("/services/{service_name}/health")
async def get_service_health(service_name: str):
    """Get health status of a service"""
    if service_name not in service_healths:
        raise HTTPException(status_code=404, detail="Service health not found")
    
    return service_healths[service_name]


@app.get("/services/health")
async def get_all_service_healths():
    """Get health status of all services"""
    return {
        "services": service_healths,
        "total": len(service_healths),
        "healthy": sum(1 for s in service_healths.values() if s["status"] == "healthy"),
        "degraded": sum(1 for s in service_healths.values() if s["status"] == "degraded"),
        "unhealthy": sum(1 for s in service_healths.values() if s["status"] == "unhealthy")
    }


@app.post("/alerts", response_model=Alert)
async def create_alert(
    severity: str,
    service: str,
    message: str
):
    """Create an alert"""
    import hashlib
    alert_id = f"ALERT-{hashlib.md5(message.encode()).hexdigest()[:8].upper()}"
    
    alert = Alert(
        alert_id=alert_id,
        severity=severity,
        service=service,
        message=message
    )
    
    alerts[alert_id] = alert.dict()
    
    # Increment error counter
    if severity == "critical":
        error_counter.labels(service=service, error_type="critical").inc()
    
    return alert


@app.get("/alerts")
async def list_alerts(
    severity: Optional[str] = None,
    service: Optional[str] = None,
    resolved: Optional[bool] = None
):
    """List alerts"""
    filtered_alerts = list(alerts.values())
    
    if severity:
        filtered_alerts = [a for a in filtered_alerts if a["severity"] == severity]
    
    if service:
        filtered_alerts = [a for a in filtered_alerts if a["service"] == service]
    
    if resolved is not None:
        filtered_alerts = [a for a in filtered_alerts if a["resolved"] == resolved]
    
    return {
        "alerts": filtered_alerts,
        "total": len(filtered_alerts)
    }


@app.put("/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """Resolve an alert"""
    if alert_id not in alerts:
        raise HTTPException(status_code=404, detail="Alert not found")
    
    alerts[alert_id]["resolved"] = True
    alerts[alert_id]["resolved_at"] = datetime.utcnow()
    
    return {"message": "Alert resolved", "alert_id": alert_id}


@app.post("/security-events", response_model=SecurityEvent)
async def log_security_event(
    event_type: str,
    service: str,
    user_id: Optional[str] = None,
    tenant_id: Optional[str] = None,
    ip_address: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None
):
    """Log a security event"""
    import hashlib
    event_id = f"SEC-{hashlib.md5(f'{event_type}{service}{datetime.utcnow()}'.encode()).hexdigest()[:8].upper()}"
    
    event = SecurityEvent(
        event_id=event_id,
        event_type=event_type,
        service=service,
        user_id=user_id,
        tenant_id=tenant_id,
        ip_address=ip_address,
        details=details or {}
    )
    
    security_events[event_id] = event.dict()
    
    # Increment security event counter
    error_counter.labels(service=service, error_type=f"security_{event_type}").inc()
    
    return event


@app.get("/security-events")
async def list_security_events(
    event_type: Optional[str] = None,
    service: Optional[str] = None,
    tenant_id: Optional[str] = None,
    limit: int = 100
):
    """List security events"""
    filtered_events = list(security_events.values())
    
    if event_type:
        filtered_events = [e for e in filtered_events if e["event_type"] == event_type]
    
    if service:
        filtered_events = [e for e in filtered_events if e["service"] == service]
    
    if tenant_id:
        filtered_events = [e for e in filtered_events if e["tenant_id"] == tenant_id]
    
    # Sort by created_at descending
    filtered_events.sort(key=lambda x: x["created_at"], reverse=True)
    
    return {
        "events": filtered_events[:limit],
        "total": len(filtered_events)
    }


@app.get("/dashboard")
async def get_dashboard():
    """Get monitoring dashboard summary"""
    total_alerts = len(alerts)
    critical_alerts = sum(1 for a in alerts.values() if a["severity"] == "critical" and not a["resolved"])
    security_events_count = len(security_events)
    
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "total": len(service_healths),
            "healthy": sum(1 for s in service_healths.values() if s["status"] == "healthy"),
            "degraded": sum(1 for s in service_healths.values() if s["status"] == "degraded"),
            "unhealthy": sum(1 for s in service_healths.values() if s["status"] == "unhealthy")
        },
        "alerts": {
            "total": total_alerts,
            "critical": critical_alerts,
            "unresolved": sum(1 for a in alerts.values() if not a["resolved"])
        },
        "security": {
            "total_events": security_events_count,
            "recent_events": len([e for e in security_events.values() if e["created_at"] > datetime.utcnow() - timedelta(hours=24)])
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8013)
