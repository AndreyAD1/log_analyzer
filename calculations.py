"""Functions to calculate statistics."""

import logging
from typing import List, Mapping, Union

from log_processing import log_reader_generator


def get_updated_median(
        sample: float,
        median: float,
        sample_sum: float,
        sample_number: int
) -> Union[float, None]:
    """
    Update and return median value.

    Use algorithm suggested here: https://habr.com/ru/post/228575/

    :param sample: a sample;
    :param median: a current median estimation;
    :param sample_sum: current sum of all samples;
    :param sample_number: current sample number;
    :return: new median estimation
    """
    logging.debug(f'Begin to update a median estimation {median}.')
    if sample_number == 0:
        logging.error('Sample number is 0.')
        return None
    delta = sample_sum / sample_number / sample_number
    if median <= sample:
        updated_median = median + delta
    else:
        updated_median = median - delta
    return updated_median


def get_statistics(
        log_path: str,
        file_extension: str,
        parse_error_threshold: float,
) -> List[Mapping[str, Union[str, float]]] or None:
    """
    Parse a log file and return statistics for each URL.

    :param log_path: a path of log file;
    :param file_extension: an extension of log file;
    :param parse_error_threshold: if parsing error ration exceeded this limit
    scripts returns an error;
    """
    log_reader = log_reader_generator(log_path, file_extension)
    statistics_per_url = {}
    error_number, total_request_number, total_request_time = 0, 0, 0
    log_note_number = 0

    for log_note_number, (url, request_time) in enumerate(log_reader):
        logging.debug(f'Begin to process the row {log_note_number}')
        if url is None or request_time is None:
            logging.error(f'Parsing error in the row {log_note_number}.')
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
            msg_template = 'Encounter {} for the first time in the row {}.'
            logging.debug(msg_template.format(url, log_note_number))
        else:
            url_info = statistics_per_url[url]
            url_info['count'] += 1
            url_info['time_sum'] += request_time
            url_info['time_avg'] = url_info['time_sum'] / url_info['count']

            if request_time > url_info['time_max']:
                statistics_per_url[url]['time_max'] = request_time

            updated_median = get_updated_median(
                request_time,
                url_info['time_med'],
                url_info['time_sum'],
                url_info['count']
            )
            if updated_median is None:
                logging.error('Can not update a median estimation.')
            statistics_per_url[url]['time_med'] = updated_median
            logging.debug(f'Successfully processed the row {log_note_number}')

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
        logging.debug(f'Calculate the statistic set: {dict_for_report}')
        report_list.append(dict_for_report)

    return report_list
