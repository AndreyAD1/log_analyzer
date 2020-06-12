import json
import os
import shutil
import subprocess
import unittest

TEST_REPORTS_DIR = './tests/test_data/test_reports'
TEST_CONFIG_PATH = './tests/test_data/test_config.json'
EXPECTED_REPORT_NAME = 'report-2019.09.30.html'
EXPECTED_REPORT_PATH = os.path.join(TEST_REPORTS_DIR, EXPECTED_REPORT_NAME)
CORRECT_REPORT_PATH = './tests/test_data/correct_report-2019.09.30.html'
SHELL_ARGS = ['python', 'log_analyzer.py', '--config', TEST_CONFIG_PATH]


class PositiveTestCase(unittest.TestCase):
    def setUp(self) -> None:
        with open(TEST_CONFIG_PATH, 'w') as config_file:
            config = {
                "REPORT_SIZE": 10,
                "REPORT_DIR": TEST_REPORTS_DIR,
                "LOG_DIR": "./tests/test_data/"
            }
            json.dump(config, config_file)
        os.mkdir(TEST_REPORTS_DIR)

    def test_config_argument(self):
        result = subprocess.run(SHELL_ARGS)
        self.assertEqual(result.returncode, 0)

    def test_report_file(self):
        subprocess.run(SHELL_ARGS)
        err_msg = f'The script doesn`t output a report {EXPECTED_REPORT_PATH}.'
        self.assertTrue(os.path.exists(EXPECTED_REPORT_PATH), msg=err_msg)
        self.assertTrue(os.path.isfile(EXPECTED_REPORT_PATH), msg=err_msg)

    def test_report_content(self):
        subprocess.run(SHELL_ARGS)
        with open(EXPECTED_REPORT_PATH, 'r') as report_file:
            report = report_file.read()

        with open(CORRECT_REPORT_PATH, 'r') as expected_report_file:
            expected_report = expected_report_file.read()

        self.assertEqual(report, expected_report, msg='Invalid report.')

    def tearDown(self) -> None:
        shutil.rmtree(TEST_REPORTS_DIR)
        os.remove(TEST_CONFIG_PATH)


if __name__ == '__main__':
    unittest.main()
