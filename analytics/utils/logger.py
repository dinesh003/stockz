import sys
import time
import json

def log_info(stage, symbol=None, provider=None, status="SUCCESS", elapsed_ms=None, warning_count=0, message=""):
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "INFO",
        "stage": stage,
        "symbol": symbol,
        "provider": provider,
        "status": status,
        "elapsed_ms": elapsed_ms,
        "warning_count": warning_count,
        "message": message
    }
    print(json.dumps(log_data), file=sys.stdout, flush=True)

def log_error(stage, symbol=None, provider=None, status="FAILED", elapsed_ms=None, error_message=""):
    log_data = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": "ERROR",
        "stage": stage,
        "symbol": symbol,
        "provider": provider,
        "status": status,
        "elapsed_ms": elapsed_ms,
        "error_message": error_message
    }
    print(json.dumps(log_data), file=sys.stderr, flush=True)
