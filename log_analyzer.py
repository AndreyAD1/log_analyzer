#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] '$request' '
#                     '$status $body_bytes_sent '$http_referer' '
#                     ''$http_user_agent' '$http_x_forwarded_for' '$http_X_REQUEST_ID' '$http_X_RB_USER' '
#                     '$request_time';

import argparse
import json
from inspect import getsourcefile
import logging
from logging import FileHandler, StreamHandler
import os
from string import Template
import sys
from typing import Any, Mapping, Union

from calculations import get_statistics
from constants import DEFAULT_CONFIG_PATH, PARSE_ERROR_THRESHOLD
from constants import REPORT_NAME_TEMPLATE
from log_processing import get_log_properties

default_config = {
    'REPORT_SIZE': 1000,
    'REPORT_DIR': './reports',
    'LOG_DIR': './log',
    'SCRIPT_LOG_PATH': 'script.log'
}


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
        logging.debug(f'Load configuration from the file {input_filepath}')
        try:
            with open(input_filepath) as config_file:
                try:
                    custom_configuration = json.load(config_file)
                except json.JSONDecodeError as ex:
                    err_msg = 'Can not parse JSON in the configuration file {}'
                    logging.exception(err_msg.format(input_filepath))
        except (OSError, FileNotFoundError):
            err_msg = f'Invalid configuration file path: {input_filepath}'
            logging.exception(err_msg)
            return None

    configuration = {**default_configuration, **custom_configuration}
    logging.debug('Built result configuration.')
    return configuration


def verify_directory_path(directory_path: str) -> bool:
    """
    Verify a configured directory.

    :param directory_path:
    :return: True if the directory path is valid.
    """
    logger = logging.getLogger()
    err_msg = ''
    if not os.path.exists(directory_path):
        err_msg = f'Can not find the directory {directory_path}.'

    if not os.path.isdir(directory_path):
        err_msg = f'The entered path {directory_path} is not a directory path.'

    if err_msg:
        logger.error(err_msg)

    return not bool(err_msg)


def verify_configuration(config: Mapping[str, Union[str, int]],) -> str:
    """Verify configured parameters."""
    for param_name in ['LOG_DIR', 'REPORT_DIR', 'REPORT_SIZE']:
        err_template = 'Required parameter {} is not configured.'
        param_value = config.get(param_name)
        error_message = '' if param_value else err_template.format(param_name)

    if not error_message:
        for dir_path in (config['LOG_DIR'], config['REPORT_DIR']):
            dir_path_is_valid = verify_directory_path(dir_path)
            if not dir_path_is_valid:
                err_template = 'The invalid path in the configuration: {}.'
                error_message = err_template.format(dir_path)

    if not error_message and config['REPORT_SIZE'] <= 0:
        err_template = 'The configured REPORT_SIZE is less than 1: {}.'
        error_message = err_template.format(config['REPORT_SIZE'])

    return error_message


def render_report(
        statistics,
        report_dir,
        log_date,
        report_size: int,
):
    """
    Render the script report.

    :param statistics: a list containing statistics;
    :param report_dir: a directory path to report saving;
    :param log_date: a report date;
    :param report_size: a number of rows which report should contain;
    """
    logger = logging.getLogger()
    assert report_size > 0
    dict_to_report = {'table_json': statistics[:report_size]}
    script_dir = os.path.dirname(os.path.abspath(getsourcefile(lambda: 0)))
    report_template_path = os.path.join(script_dir, 'data', 'report.html')
    with open(report_template_path, 'r') as report_template_file:
        report_template_str = report_template_file.read()

    template = Template(report_template_str)
    report = template.safe_substitute(dict_to_report)
    report_file_name = REPORT_NAME_TEMPLATE.format(
        str(log_date).replace("-", ".")
    )
    report_file_path = os.path.join(report_dir, report_file_name)
    with open(report_file_path, 'w') as report_file:
        report_file.write(report)
    logger.info(f'Successfully render the report: {report_file_path}')


def configure_logger(log_path: Union[str, None]):
    """
    Configure a logger.

    :param log_path: a path to script log file. None if script should output
    log to the stdout.
    """
    logger = logging.getLogger()
    for handler in logger.handlers:
        logger.removeHandler(handler)

    log_handler = FileHandler(log_path) if log_path else StreamHandler()
    formatter = logging.Formatter(
        fmt='[%(asctime)s] %(levelname).1s %(message)s',
        datefmt='%Y.%m.%d %H:%M:%S'
    )
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)


def main():
    # logging.basicConfig(level=logging.DEBUG)
    console_arguments = get_console_arguments()
    config_file_path = console_arguments.config
    configuration = get_configuration(config_file_path, default_config)
    if not configuration:
        sys.exit(f'Invalid configuration file {config_file_path}')

    configure_logger(configuration.get('SCRIPT_LOG_PATH'))

    error = verify_configuration(configuration)
    if error:
        sys.exit(error)

    log_properties = get_log_properties(
        configuration['LOG_DIR'],
        configuration['REPORT_DIR'],
    )
    if not log_properties:
        sys.exit(f'No new log file is in {configuration["LOG_DIR"]}')

    statistics = get_statistics(
        log_properties.log_path,
        log_properties.file_extension,
        PARSE_ERROR_THRESHOLD,
    )
    if statistics is None:
        sys.exit(f'Can not parse the log file {log_properties.log_path}.')

    statistics.sort(key=lambda x: x['time_sum'], reverse=True)
    render_report(
        statistics,
        configuration['REPORT_DIR'],
        log_properties.log_date,
        configuration['REPORT_SIZE'],
    )


if __name__ == '__main__':
    main()
