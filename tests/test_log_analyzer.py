import os
import shutil
import subprocess
import unittest

TEST_REPORTS_DIR = './tests/test_data/test_reports'


class ConfigTestCase(unittest.TestCase):
    def setUp(self) -> None:
        print(os.getcwd())
        os.mkdir(TEST_REPORTS_DIR)

    def test_config_argument(self):
        test_config_path = './tests/test_data/test_config.json'
        arguments = ['--config', test_config_path]
        result = subprocess.run(['python', 'log_analyzer.py', *arguments])
        self.assertEqual(result.returncode, 0)

    def tearDown(self) -> None:
        shutil.rmtree(TEST_REPORTS_DIR)


if __name__ == '__main__':
    unittest.main()
