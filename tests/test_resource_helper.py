"""
Kelebek Sınav Sistemi - Resource Helper Unit Tests

Tests for utils/resource_helper.py module.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock


# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.resource_helper import (
    is_frozen,
    get_base_path,
    get_resource_path,
    get_user_data_path,
    ensure_user_data_dir,
    get_app_info,
)


class TestIsFrozen(unittest.TestCase):
    """Tests for is_frozen function."""
    
    def test_is_frozen_returns_false_in_normal_mode(self):
        """In normal Python execution, is_frozen should return False."""
        self.assertFalse(is_frozen())
    
    @patch.object(sys, 'frozen', True, create=True)
    def test_is_frozen_returns_true_when_frozen(self):
        """When sys.frozen is True, is_frozen should return True."""
        self.assertTrue(is_frozen())


class TestGetBasePath(unittest.TestCase):
    """Tests for get_base_path function."""
    
    def test_get_base_path_returns_project_root(self):
        """In normal mode, should return project root directory."""
        base_path = get_base_path()
        # Should be the parent of utils directory
        self.assertTrue(os.path.isdir(base_path))
        self.assertTrue(os.path.exists(os.path.join(base_path, 'utils')))
    
    @patch.object(sys, 'frozen', True, create=True)
    @patch.object(sys, '_MEIPASS', '/tmp/test_meipass', create=True)
    def test_get_base_path_returns_meipass_when_frozen(self):
        """When frozen, should return sys._MEIPASS."""
        base_path = get_base_path()
        self.assertEqual(base_path, '/tmp/test_meipass')


class TestGetResourcePath(unittest.TestCase):
    """Tests for get_resource_path function."""
    
    def test_get_resource_path_with_relative_path(self):
        """Should return absolute path for relative resource."""
        resource = get_resource_path('assets/styles.py')
        self.assertTrue(os.path.isabs(resource))
        self.assertTrue(resource.endswith('assets/styles.py') or 
                        resource.endswith('assets\\styles.py'))
    
    def test_get_resource_path_exists_for_known_resource(self):
        """Should return path to existing resources."""
        resource = get_resource_path('utils')
        self.assertTrue(os.path.exists(resource))


class TestGetUserDataPath(unittest.TestCase):
    """Tests for get_user_data_path function."""
    
    def test_get_user_data_path_returns_project_root_on_empty(self):
        """With empty path, should return base user data directory."""
        user_path = get_user_data_path()
        self.assertTrue(os.path.isdir(user_path))
    
    def test_get_user_data_path_with_relative_path(self):
        """Should append relative path to user data directory."""
        user_path = get_user_data_path('database/kelebek.db')
        self.assertTrue(os.path.isabs(user_path))
        self.assertTrue(user_path.endswith('database/kelebek.db') or 
                        user_path.endswith('database\\kelebek.db'))
    
    @patch.object(sys, 'frozen', True, create=True)
    @patch.object(sys, 'executable', 'C:\\Program Files\\App\\app.exe', create=True)
    def test_get_user_data_path_uses_executable_dir_when_frozen(self):
        """When frozen, should use directory containing executable."""
        user_path = get_user_data_path('test.db')
        self.assertTrue('Program Files' in user_path or 'App' in user_path)


class TestEnsureUserDataDir(unittest.TestCase):
    """Tests for ensure_user_data_dir function."""
    
    def test_ensure_user_data_dir_creates_directory(self):
        """Should create directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmp:
            with patch('utils.resource_helper.get_user_data_path', 
                       return_value=os.path.join(tmp, 'new_dir')):
                result = ensure_user_data_dir('new_dir')
                # The mock makes it use tmp/new_dir
                self.assertTrue(result.endswith('new_dir'))
    
    def test_ensure_user_data_dir_returns_path(self):
        """Should return the path of the directory."""
        result = ensure_user_data_dir('database')
        self.assertTrue(os.path.isabs(result))


class TestGetAppInfo(unittest.TestCase):
    """Tests for get_app_info function."""
    
    def test_get_app_info_returns_dict(self):
        """Should return a dictionary with expected keys."""
        info = get_app_info()
        self.assertIsInstance(info, dict)
        self.assertIn('frozen', info)
        self.assertIn('base_path', info)
        self.assertIn('user_data_path', info)
        self.assertIn('executable', info)
    
    def test_get_app_info_frozen_is_bool(self):
        """frozen key should be a boolean."""
        info = get_app_info()
        self.assertIsInstance(info['frozen'], bool)
    
    def test_get_app_info_paths_are_strings(self):
        """Path values should be strings."""
        info = get_app_info()
        self.assertIsInstance(info['base_path'], str)
        self.assertIsInstance(info['user_data_path'], str)
        self.assertIsInstance(info['executable'], str)


if __name__ == '__main__':
    unittest.main()
