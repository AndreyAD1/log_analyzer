"""Functions to find and process a log file."""

from datetime import datetime, date
import gzip
import logging
import os.path
import re
from typing import Generator, Tuple

from constants import REPORT_NAME_TEMPLATE


def get_new_log_path_and_date(
        directory_path: str
) -> Tuple[str, date] or Tuple[None, None]:
    """
    Return log file path and its date if new log was found.

    :param directory_path: a directory containing log files.
    :return: log path and log date. If no new log path and date found -
    (None, None).
    """
    log_pattern = re.compile(
        '(?<=^nginx-access-ui\.log-)\d{8}(?=$|\.gz)'
    )
    newest_log_path = None
    log_datetime = datetime(1, 1, 1)
    for entry_name in os.listdir(directory_path):
        entry_path = os.path.join(directory_path, entry_name)
        entry_is_file = os.path.isfile(entry_path)
        if entry_is_file:
            log_date_match = log_pattern.search(entry_name)
            if not log_date_match:
                continue

            log_date_string = log_date_match.group()
            try:
                file_log_date = datetime.strptime(log_date_string, '%Y%m%d')
            except ValueError:
                continue

            if file_log_date > log_datetime:
                log_datetime = file_log_date
                newest_log_path = entry_path

    log_date = log_datetime.date() if newest_log_path else None
    return newest_log_path, log_date


def search_in_reports(report_dir_path: str, log_date: date) -> bool:
    """
    Check if report with given date is in a directory containing reports.

    :param report_dir_path: directory containing script results;
    :param log_date: a report date;
    :return: True if searched report is found in report directory.
    """
    logging.info(f'Search for reports in {report_dir_path}.')
    expected_report_name = REPORT_NAME_TEMPLATE.format(
        str(log_date).replace("-", ".")
    )
    expected_report_path = os.path.join(report_dir_path, expected_report_name)
    report_is_ready = os.path.exists(expected_report_path)
    return report_is_ready


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
    logger = logging.getLogger()
    read_line_number = 0
    url_pattern = re.compile('(?<=\s)(\S+)(?= HTTP/1.)')
    request_time_pattern = re.compile('\S+$')
    log_file_reader = gzip.open if file_extension == '.gz' else open
    read_param = 'rt' if file_extension == '.gz' else 'r'
    with log_file_reader(log_path, read_param) as log_file:
        successful_parsing = False
        for line in log_file:
            read_line_number += 1
            url_match = url_pattern.search(line)
            req_time_match = request_time_pattern.search(line)
            url = None if url_match is None else url_match.group()
            req_time = None if req_time_match is None else req_time_match.group()
            try:
                req_time = float(req_time)
            except ValueError:
                req_time = None

            if url is None or req_time is None:
                err_msg = 'Parsing error. Invalid line number {}: {}'
                logger.error(err_msg.format(read_line_number, line))
                url = req_time = None
            else:
                successful_parsing = True

            yield url, req_time

        if not successful_parsing:
            raise Exception(f'Can not parse any request info in {log_path}')
