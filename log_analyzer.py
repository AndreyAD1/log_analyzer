#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] '$request' '
#                     '$status $body_bytes_sent '$http_referer' '
#                     ''$http_user_agent' '$http_x_forwarded_for' '$http_X_REQUEST_ID' '$http_X_RB_USER' '
#                     '$request_time';

import argparse
from collections import namedtuple
from datetime import date
import gzip
import json
import logging
import os
from os.path import splitext
import re
from string import Template
import sys
from typing import Any, List, Mapping, Tuple, Union

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
REPORT_NAME_TEMPLATE = 'report-{}.{}.{}.html'
SPLITTED_LINE_LENGTH = 18
logging.basicConfig(level=logging.DEBUG)


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


def verify_directory_path(directory_path: str) -> bool:
    """

    :param directory_path:
    :return:
    """
    err_msg = ''
    if not os.path.exists(directory_path):
        err_msg = f'Can not find the directory {directory_path}.'

    if not os.path.isdir(directory_path):
        err_msg = f'The entered path {directory_path} is not a directory path.'

    if err_msg:
        logging.error(err_msg)

    return not bool(err_msg)


def get_new_log_path_and_date(
        direcrory_path: str
) -> Tuple[str, str] or Tuple[None, None]:
    """

    :param direcrory_path:
    :return:
    """
    log_pattern = re.compile(
        '(?<=^nginx-access-ui\.log-)(20\d{2})(\d{2})(\d{2})(?=$|\.gz)'
    )
    newest_log_path = None
    log_date = date(1, 1, 1)
    for path, _, file_names in os.walk(direcrory_path):
        for file_name in file_names:
            log_date_match = log_pattern.search(file_name)
            if not log_date_match:
                continue
            log_year = int(log_date_match.group(1))
            log_month = int(log_date_match.group(2))
            log_day = int(log_date_match.group(3))
            try:
                file_log_date = date(log_year, log_month, log_day)
            except ValueError:
                continue
            if file_log_date > log_date:
                log_date = file_log_date
                newest_log_path = os.path.join(path, file_name)

    log_date = log_date if newest_log_path else None
    return newest_log_path, log_date


def search_in_reports(report_dir_path: str, log_date: date) -> bool or None:
    """

    :param report_dir_path:
    :param log_date:
    :return:
    """
    # TODO BUG! If month or date is less than 10 the script will not add a prefix 0.
    expected_report_name = REPORT_NAME_TEMPLATE.format(
        log_date.year,
        log_date.month,
        log_date.day
    )
    expected_report_path = os.path.join(report_dir_path, expected_report_name)
    path_exists = os.path.exists(expected_report_path)
    report_is_ready = False
    if path_exists:
        report_is_ready = os.path.isfile(expected_report_path)
    return report_is_ready


def get_log_properties(
        log_dir_path: str,
        report_dir_path: str
) -> LogProperties or None:
    """
    Return the properties of new log file or None if no log file found.

    :param log_dir_path: a directory to search a log file;
    :param report_dir_path: a directory containing the script reports;
    :return: namedtuple containing a log file path, a log date and
    a log file extension. Function returns None if it found no valid log file
    or found a log file which had been already processed.
    """

    newest_log_path, log_date = get_new_log_path_and_date(log_dir_path)
    report_is_ready = False
    if newest_log_path:
        report_is_ready = search_in_reports(report_dir_path, log_date)

    unprocessed_log_is_found = newest_log_path and not report_is_ready
    if unprocessed_log_is_found:
        logging.info(f'Find the log to process {newest_log_path}')
        _, log_ext = splitext(newest_log_path)
        log_properties = LogProperties(newest_log_path, log_date, log_ext)
    else:
        logging.info(f'Do not find a suitable log file in {log_dir_path}.')
        log_properties = None

    return log_properties


def log_reader_generator(
        log_path: str,
        file_extension: str,
):
    """

    :param log_path:
    :param file_extension:
    :return:
    """
    read_line_number = 0
    url_pattern = re.compile('(?<=\s)(\S+)(?= HTTP/1.)')
    request_time_pattern = re.compile('\S+$')
    log_file_reader = gzip.open if file_extension == 'gz' else open
    with log_file_reader(log_path, 'r') as log_file:
        for line in log_file:
            read_line_number += 1
            url_match = url_pattern.search(line)
            req_time_match = request_time_pattern.search(line)
            url = None if url_match is None else url_match.group()
            req_time = None if req_time_match is None else req_time_match.group()

            if not url or not req_time:
                err_msg = 'Parsing error. Invalid line with number {}: {}'
                logging.error(err_msg.format(read_line_number, line))

            yield url, float(req_time)


def get_updated_median(request_time: float, median: float, sum, number) -> float:
    """
    Update and return median value.

    Use algorithm suggested here: https://habr.com/ru/post/228575/

    :param request_time:
    :param median:
    :param sum:
    :param number:
    :return:
    """
    delta = sum / number / number
    if median <= request_time:
        updated_median = median + delta
    else:
        updated_median = median - delta
    return updated_median


def get_statistics(
        log_path: str,
        file_extension: str,
        parse_error_threshold: float
) -> List[Mapping[str, Union[str, float]]] or None:
    """

    """
    log_reader = log_reader_generator(log_path, file_extension)
    statistics_per_url = {}
    error_number, total_request_number, total_request_time = 0, 0, 0
    log_note_number = 0

    for log_note_number, (url, request_time) in enumerate(log_reader):
        if url is None or request_time is None:
            error_number += 1
            continue

        total_request_number += 1
        total_request_time += request_time

        if url not in statistics_per_url:
            statistics_per_url[url] = {
                'count': 1,
                'time_sum': request_time,
                'time_avg': request_time,
                'time_max': request_time,
                'time_med': request_time
            }
        else:
            url_info = statistics_per_url[url]
            url_info['count'] += 1
            url_info['time_sum'] += request_time
            url_info['time_avg'] = url_info['time_sum'] / url_info['count']

            if request_time > url_info['time_max']:
                statistics_per_url[url]['time_max'] = request_time

            statistics_per_url[url]['time_med'] = get_updated_median(
                request_time,
                url_info['time_med'],
                url_info['time_sum'],
                url_info['count']
            )

    if not any([log_note_number, total_request_number, total_request_time]):
        logging.error(f'Can not parse any request info in {log_path}')
        return

    error_ratio = error_number / log_note_number
    too_many_errors = error_ratio > parse_error_threshold
    if too_many_errors:
        err_ratio_msg = f'Errors per log lines ratio is {error_ratio}'
        logging.error(f'Too many parsing errors. {err_ratio_msg}')
        return

    report_list = []
    for url, statistics in statistics_per_url.items():
        dict_for_report = {
            'url': url,
            'count_perc': statistics['count'] / total_request_number,
            'time_perc': statistics['time_sum'] / total_request_time,
            **statistics
        }
        report_list.append(dict_for_report)

    return report_list


def render_report(statistics, report_dir, log_date, report_size: int):
    assert report_size > 0
    dict_to_report = {'table_json': statistics[:report_size]}
    with open('./data/report.html', 'r') as report_template_file:
        report_template_str = report_template_file.read()

    template = Template(report_template_str)
    report = template.safe_substitute(dict_to_report)
    report_file_name = REPORT_NAME_TEMPLATE.format(
        log_date.year,
        log_date.month,
        log_date.day
    )
    report_file_path = os.path.join(report_dir, report_file_name)
    with open(report_file_path, 'w') as report_file:
        report_file.write(report)


def verify_configuration(config: Mapping[str, Union[str, int]]) -> str:
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


def main():
    console_arguments = get_console_arguments()
    config_file_path = console_arguments.config

    configuration = get_configuration(config_file_path, default_config)
    if not configuration:
        sys.exit(f'Invalid configuration file {config_file_path}')

    error = verify_configuration(configuration)
    if error:
        sys.exit(error)

    log_properties = get_log_properties(
        configuration['LOG_DIR'],
        configuration['REPORT_DIR']
    )
    if not log_properties:
        sys.exit(f'No new log file is in {configuration["LOG_DIR"]}')

    statistics = get_statistics(
        log_properties.log_path,
        log_properties.file_extension,
        PARSE_ERROR_THRESHOLD
    )
    if statistics is None:
        sys.exit(f'Can not parse the log file {log_properties.log_path}.')

    statistics.sort(key=lambda x: x['time_sum'], reverse=True)
    render_report(
        statistics,
        configuration['REPORT_DIR'],
        log_properties.log_date,
        configuration['REPORT_SIZE']
    )


if __name__ == '__main__':
    main()
