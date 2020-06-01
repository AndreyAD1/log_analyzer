#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] '$request' '
#                     '$status $body_bytes_sent '$http_referer' '
#                     ''$http_user_agent' '$http_x_forwarded_for' '$http_X_REQUEST_ID' '$http_X_RB_USER' '
#                     '$request_time';

import argparse
from collections import namedtuple
from datetime import datetime
import json
import logging
import os
from os.path import splitext
import sys
from typing import Any, List, Mapping, Union

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
        input_filepath: str or None,
        default_configuration: Mapping[str, Union[str, int]]
) -> Mapping[str, Any] or None:
    """
    Return the script configuration.

    :param input_filepath: a path to configuration file;
    :param default_configuration: a dict containing default script parameters;
    :return: a dict {config_param_name: config_param_value, ...}.
    """
    custom_configuration = {}

    if input_filepath is not None:
        try:
            with open(input_filepath) as config_file:
                custom_configuration = json.load(config_file)
        except OSError:
            logging.error(f'Invalid configuration file path: {input_filepath}')
            return None

    configuration = {**default_configuration, **custom_configuration}
    return configuration


def verify_log_file(file_name: str) -> bool:
    pass


def get_log_date(file_name: str) -> datetime:
    pass


def get_log_properties(log_dir_path: str) -> LogProperties or None:
    """
    Return the properties of new log file or None if no log file found.

    :param log_dir_path: a directory to search a log file;
    :return: namedtuple containing a log file path, a log date and
    a log file extension. Function returns None if it found no valid log file
    or found log file had been already processed.
    """
    err_msg = None
    if not os.path.exists(log_dir_path):
        err_msg = f'Can not find the directory {log_dir_path}.'

    if not os.path.isdir(log_dir_path):
        err_msg = f'The entered path {log_dir_path} is not a directory path.'

    if err_msg:
        logging.error(err_msg)
        return

    newest_log_path = None
    log_date = datetime(1, 1, 1)
    for path, _, file_names in os.walk(log_dir_path):
        for file_name in file_names:
            file_is_valid_log = verify_log_file(file_name)
            if not file_is_valid_log:
                continue

            file_log_date = get_log_date(file_name)
            if file_log_date > log_date:
                log_date = file_log_date
                newest_log_path = os.path.join(path, file_name)

    if newest_log_path is None:
        return

    # TODO check if newest log file had already been processed.
    _, log_extension = splitext(newest_log_path)
    log_properties = LogProperties(newest_log_path, log_date, log_extension)
    return log_properties


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
