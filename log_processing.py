"""Functions to find and process a log file."""

from collections import namedtuple
from datetime import date
import gzip
import logging
import os.path
import re
from typing import Generator, Tuple

from constants import REPORT_NAME_TEMPLATE


LogProperties = namedtuple(
    'LogProperties',
    ['log_path', 'log_date', 'file_extension']
)


def get_new_log_path_and_date(
        directory_path: str
) -> Tuple[str, str] or Tuple[None, None]:
    """
    Return log file path and its date if new log was found.

    :param directory_path: a directory containing log files.
    :return: log path and log date. If no new log path and date found -
    (None, None).
    """
    log_pattern = re.compile(
        '(?<=^nginx-access-ui\.log-)(20\d{2})(\d{2})(\d{2})(?=$|\.gz)'
    )
    newest_log_path = None
    log_date = date(1, 1, 1)
    for path, _, file_names in os.walk(directory_path):
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


def search_in_reports(report_dir_path: str, log_date: date) -> bool:
    """
    Check if report with given date is in a directory containing reports.

    :param report_dir_path: directory containing script results;
    :param log_date: a report date;
    :return: True if searched report is found in report directory.
    """
    expected_report_name = REPORT_NAME_TEMPLATE.format(
        str(log_date).replace("-", ".")
    )
    expected_report_path = os.path.join(report_dir_path, expected_report_name)
    path_exists = os.path.exists(expected_report_path)
    report_is_ready = False
    if path_exists:
        report_is_ready = os.path.isfile(expected_report_path)
    return report_is_ready


def get_log_properties(
        log_dir_path: str,
        report_dir_path: str,
        logger: logging
) -> LogProperties or None:
    """
    Return the properties of new log file or None if no log file found.

    :param log_dir_path: a directory to search a log file;
    :param report_dir_path: a directory containing the script reports;
    :param logger:
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
        logger.info(f'Find the log to process {newest_log_path}')
        _, log_ext = os.path.splitext(newest_log_path)
        log_properties = LogProperties(newest_log_path, log_date, log_ext)
    else:
        logger.error(f'Do not find a suitable log file in {log_dir_path}.')
        log_properties = None

    return log_properties


def log_reader_generator(
        log_path: str,
        file_extension: str,
) -> Generator[Tuple[str, float], None, None]:
    """
    Open log file, parse and yield url and request time from each file line.

    :param log_path: the path of log file;
    :param file_extension: extension of log file;
    Valid values: empty string or 'gz';
    :return: url and request processing duration.
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
                logging.info(err_msg.format(read_line_number, line))

            yield url, float(req_time)
