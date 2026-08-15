import os
import pytest
from utils.fs import temporary_directory
from utils.network import get_session
from config.settings import settings

def test_temporary_directory_cleanup():
    # Test normal cleanup
    with temporary_directory() as temp_dir:
        assert os.path.exists(temp_dir)
        test_file = os.path.join(temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("hello")
            
    assert not os.path.exists(temp_dir)
    assert not os.path.exists(test_file)

def test_temporary_directory_exception_cleanup():
    # Test cleanup on exception
    temp_path = None
    try:
        with temporary_directory() as temp_dir:
            temp_path = temp_dir
            assert os.path.exists(temp_dir)
            raise ValueError("Test Exception")
    except ValueError:
        pass
        
    assert temp_path is not None
    assert not os.path.exists(temp_path)

def test_network_session_timeout(mocker):
    # Verify the configured session injects the correct timeout
    session = get_session()
    
    mock_super_request = mocker.patch("requests.Session.request")
    session.get("http://example.com")
    
    mock_super_request.assert_called_once()
    kwargs = mock_super_request.call_args[1]
    
    assert "timeout" in kwargs
    assert kwargs["timeout"] == settings.network_timeout_seconds
