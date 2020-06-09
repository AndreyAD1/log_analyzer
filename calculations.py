"""Функции для расчёта статистик."""

import logging
from typing import List, Mapping, Union

from log_processing import log_reader_generator


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
        parse_error_threshold: float,
        logger: logging
) -> List[Mapping[str, Union[str, float]]] or None:
    """

    """
    log_reader = log_reader_generator(log_path, file_extension, logger)
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
        logger.error(f'Can not parse any request info in {log_path}')
        return

    error_ratio = error_number / log_note_number
    too_many_errors = error_ratio > parse_error_threshold
    if too_many_errors:
        err_ratio_msg = f'Errors per log lines ratio is {error_ratio}'
        logger.error(f'Too many parsing errors. {err_ratio_msg}')
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
