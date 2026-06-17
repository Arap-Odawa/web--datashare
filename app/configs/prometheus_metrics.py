import time
import functools
import inspect
from prometheus_client import Histogram, Counter

# Histogram to track execution durations (seconds)
FUNCTION_DURATION = Histogram(
    "dash_app_function_duration_seconds",
    "Time taken to complete specific internal functions (seconds)",
    labelnames=["category", "function_name"]
)

# Counter to track total requests and status (success/failure)
FUNCTION_REQUESTS = Counter(
    "dash_app_function_requests_total",
    "Total number of requests to specific internal functions",
    labelnames=["category", "function_name", "status"]
)

class monitor_function:
    def __init__(self, category: str, function_name: str = None):
        self.category = category
        self.function_name = function_name

    def __enter__(self):
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.perf_counter() - self.start_time
        func_name = self.function_name or "unknown"
        status = "failure" if exc_type is not None else "success"
        FUNCTION_DURATION.labels(category=self.category, function_name=func_name).observe(duration)
        FUNCTION_REQUESTS.labels(category=self.category, function_name=func_name, status=status).inc()
        return False  # Propagate exceptions

    def __call__(self, func):
        func_name = self.function_name or func.__name__

        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    res = await func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    FUNCTION_DURATION.labels(category=self.category, function_name=func_name).observe(duration)
                    FUNCTION_REQUESTS.labels(category=self.category, function_name=func_name, status="success").inc()
                    return res
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    FUNCTION_DURATION.labels(category=self.category, function_name=func_name).observe(duration)
                    FUNCTION_REQUESTS.labels(category=self.category, function_name=func_name, status="failure").inc()
                    raise e
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                start_time = time.perf_counter()
                try:
                    res = func(*args, **kwargs)
                    duration = time.perf_counter() - start_time
                    FUNCTION_DURATION.labels(category=self.category, function_name=func_name).observe(duration)
                    FUNCTION_REQUESTS.labels(category=self.category, function_name=func_name, status="success").inc()
                    return res
                except Exception as e:
                    duration = time.perf_counter() - start_time
                    FUNCTION_DURATION.labels(category=self.category, function_name=func_name).observe(duration)
                    FUNCTION_REQUESTS.labels(category=self.category, function_name=func_name, status="failure").inc()
                    raise e
            return sync_wrapper
