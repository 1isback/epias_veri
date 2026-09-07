from typing import Dict, Any

class MetricsCollector:
    def __init__(self):
        self.api_request_count = 0
        self.failed_imports = 0
        self.auth_renewals = 0
        self.scheduler_executions = 0
        self.total_request_duration_ms = 0.0

    def inc_api_request(self, duration_ms: float = 0.0):
        self.api_request_count += 1
        self.total_request_duration_ms += duration_ms

    def inc_auth_renewal(self):
        self.auth_renewals += 1

    def inc_failed_import(self):
        self.failed_imports += 1

    def inc_scheduler_execution(self):
        self.scheduler_executions += 1

    def get_metrics(self) -> Dict[str, Any]:
        avg_duration = 0.0
        if self.api_request_count > 0:
            avg_duration = self.total_request_duration_ms / self.api_request_count
            
        return {
            "api_request_count": self.api_request_count,
            "auth_renewals": self.auth_renewals,
            "failed_imports": self.failed_imports,
            "scheduler_executions": self.scheduler_executions,
            "avg_api_duration_ms": round(avg_duration, 2)
        }

metrics = MetricsCollector()
