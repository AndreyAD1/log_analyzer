#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] '$request' '
#                     '$status $body_bytes_sent '$http_referer' '
#                     ''$http_user_agent' '$http_x_forwarded_for' '$http_X_REQUEST_ID' '$http_X_RB_USER' '
#                     '$request_time';

import argparse
from collections import namedtuple
import sys
from typing import List, Mapping, Union

default_config = {
    'REPORT_SIZE': 1000,
    'REPORT_DIR': './reports',
    'LOG_DIR': './log'
}
PARSE_ERROR_THRESHOLD = 0.5
DEFAULT_CONFIG_PATH = 'log_analyzer_config.json'
LogProperties = namedtuple(
    'LogProperties',
    ['log_path', 'log_date', 'file_extension']
)


def get_console_arguments() -> argparse.Namespace:
    """Process the script arguments."""
    argument_parser = argparse.ArgumentParser()
    default_config_help = f'Default: {DEFAULT_CONFIG_PATH}'
    argument_parser.add_argument(
        '--config',
        nargs='?',
        const=DEFAULT_CONFIG_PATH,
        default=None,
        help=f'A path to a script configuration file. {default_config_help}',
        type=str
    )
    return argument_parser.parse_args()


def get_configuration(
        filepath: str,
        default_config: Mapping[str, Union[str, int]]
) -> Mapping[str, Union[str, int]]:
    """
    Вернуть конфигурацию скрипта.

    :param filepath:
    :param default_config:
    :return:
    """
    pass


def get_log_properties(log_dir_path: str) -> LogProperties:
    """

    :param log_dir_path:
    :return:
    """
    pass


def get_request_times_per_url(
        log_path: str,
        file_extension: str,
        parse_error_threshold: float
) -> Mapping[str, List[float]]:
    """

    :param log_path:
    :param file_extension:
    :param parse_error_threshold:
    :return:
    """
    pass


def get_statistics(
        request_times_per_url: Mapping[str, List[float]]
) -> Mapping[str, float]:
    """

    :param request_times_per_url:
    :return:
    """
    pass


def render_report(statistics, report_dir, log_date, report_size):
    pass


def main():
    console_arguments = get_console_arguments()
    config_file_path = console_arguments.config
    configuration = get_configuration(config_file_path, default_config)
    if not configuration:
        sys.exit(f'Invalid configuration file {config_file_path}')

    log_properties = get_log_properties(configuration['LOG_DIR'])
    if not log_properties:
        sys.exit(f'No new log file is in {configuration["LOG_DIR"]}')

    request_times_per_url = get_request_times_per_url(
        log_properties.log_path,
        log_properties.file_extension,
        PARSE_ERROR_THRESHOLD
    )
    if not request_times_per_url:
        sys.exit(f'Parse error threshold {PARSE_ERROR_THRESHOLD} is exceeded.')

    statistics = get_statistics(request_times_per_url)
    render_report(
        statistics,
        configuration['REPORT_DIR'],
        log_properties.log_date,
        configuration['REPORT_SIZE']
    )


if __name__ == '__main__':
    main()
