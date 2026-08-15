import requests
from config.settings import settings

def get_session() -> requests.Session:
    """
    Returns a requests.Session configured with a strict hard timeout for all requests,
    obeying CostGuard's NETWORK_TIMEOUT_SECONDS limit.
    """
    timeout = settings.network_timeout_seconds
    
    class TimeoutSession(requests.Session):
        def request(self, *args, **kwargs):
            kwargs.setdefault('timeout', timeout)
            return super().request(*args, **kwargs)
            
    return TimeoutSession()
