import pytest
from core.cost_guard import CostGuard
from core.exceptions import CostGuardError
from config.settings import settings

def test_cost_guard_limits():
    guard = CostGuard()
    
    # Test Groq limit
    for _ in range(settings.max_groq_requests_per_run):
        guard.increment_groq_requests()
        
    with pytest.raises(CostGuardError):
        guard.increment_groq_requests()

    # Test Visual search limit
    for _ in range(settings.max_visual_searches_per_run):
        guard.increment_visual_searches()
        
    with pytest.raises(CostGuardError):
        guard.increment_visual_searches()

    # Test Visual download limit
    for _ in range(settings.max_visual_downloads_per_run):
        guard.increment_visual_downloads()
        
    with pytest.raises(CostGuardError):
        guard.increment_visual_downloads()
