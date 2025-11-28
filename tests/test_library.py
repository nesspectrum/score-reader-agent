import unittest
import os
import shutil
import json
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.library_agent import LibraryAgent

class TestLibraryAgent(unittest.TestCase):
    def setUp(self):
        self.test_lib_dir = "test_library"
        if os.path.exists(self.test_lib_dir):
            shutil.rmtree(self.test_lib_dir)
        self.agent = LibraryAgent(library_dir=self.test_lib_dir)
        
        # Create a dummy file to hash
        self.test_file = "dummy_sheet.txt"
        with open(self.test_file, "w") as f:
            f.write("test content")

    def tearDown(self):
        if os.path.exists(self.test_lib_dir):
            shutil.rmtree(self.test_lib_dir)
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_save_and_get(self):
        data = {"key": "C Major"}
        
        # Save
        success = self.agent.save_to_library(self.test_file, data)
        self.assertTrue(success)
        
        # Verify file exists
        files = os.listdir(self.test_lib_dir)
        self.assertEqual(len(files), 1)
        self.assertTrue(files[0].endswith(".json"))
        
        # Get
        cached_data = self.agent.get_cached_data(self.test_file)
        self.assertEqual(cached_data, data)
        
    def test_cache_miss(self):
        cached_data = self.agent.get_cached_data("non_existent_file.txt")
        self.assertIsNone(cached_data)

if __name__ == '__main__':
    unittest.main()
