from __future__ import annotations

import contextlib
import os
import sys
import typing
from typing import IO, List, Optional, cast

from loguru import logger as _loguru_logger
if typing.TYPE_CHECKING:
    from loguru import Record
__all__ = ['DEFAULT_LOG_PATH', 'logger']

# 获取当前文件的绝对路径
current_file_path = os.path.abspath(__file__)
# 获取当前文件所在的目录
current_dir = os.path.dirname(current_file_path)
# 获取当前目录的上一级目录
parent_dir = os.path.dirname(current_dir)
parent_dir = os.path.dirname(parent_dir)
path = os.path.join(parent_dir, 'log')

DEFAULT_LOG_PATH = path
_LOG_ROTATION_TIME_SPAN = '1 day'
_LOG_RETENTION_TIME_SPAN = '7 days'


class _ErrorStreamToLogger:

    def __init__(self, *, name: Optional[str] = None) -> None:
        self._name = name
        self._buffer: List[str] = []

    def write(self, buffer: Optional[str]) -> None:
        if buffer is not None:
            self._buffer.append(buffer)

    def flush(self) -> None:
        if len(self._buffer) == 0:
            return
        pre_buffer = f'From {self._name}: ' if self._name is not None else ''
        info_str = pre_buffer + ''.join(self._buffer)
        info_level = 'ERROR' if ('error' in info_str or 'ERROR' in info_str or 'Error' in info_str) else 'INFO'
        try:
            _loguru_logger.opt(depth=1).log(info_level, info_str)
        except ValueError:
            # See https://loguru.readthedocs.io/en/stable/resources/recipes.html#using-loguru-s-logger-within-a-cython-module  # noqa: E501
            # and https://github.com/Delgan/loguru/issues/88
            _loguru_logger.patch(lambda record: record.update({
                'name': 'N/A',
                'function': '',
                'line': 0
            })).log(info_level, info_str)

        self._buffer = []

def _log_format(_: Record) -> str:
    # add the thread name and the task id to log messages
    format_with_tid = ('<green>[{time:YYYY-MM-DD HH:mm:ss.SSS}]</green>'
                       '<level>[{level}]</level>'
                       '<magenta>[{thread.name}]</magenta>'
                       '<cyan>[{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}]</cyan> - <level>{message}</level>\n')

    return format_with_tid


class _Logger:

    def __init__(self, log_path: Optional[str] = None) -> None:
        # determine log file path and name
        if not log_path:
            log_path = DEFAULT_LOG_PATH
        os.makedirs(log_path, exist_ok=True)

        _debug_file_pathname = os.path.join(log_path,  f'debug.log')
        _info_file_pathname = os.path.join(log_path,  f'info.log')

        _loguru_logger.remove()
        _loguru_logger.add(sys.__stdout__, format=_log_format)

        # add debug- and info-level loggers
        _loguru_logger.add(_debug_file_pathname,
                           level='DEBUG',
                           rotation=_LOG_ROTATION_TIME_SPAN,
                           retention=_LOG_RETENTION_TIME_SPAN,
                           format=_log_format)
        _loguru_logger.add(_info_file_pathname,
                           level='INFO',
                           rotation=_LOG_ROTATION_TIME_SPAN,
                           retention=_LOG_RETENTION_TIME_SPAN,
                           format=_log_format)

        _loguru_logger.info(f'Log files {_debug_file_pathname} and {_info_file_pathname} created.')

        # add stderr output to log.error (for third party packages' output)
        redirection = cast(IO[str], _ErrorStreamToLogger())
        contextlib.redirect_stderr(redirection).__enter__()

        self.logger = _loguru_logger


_logger_object = _Logger()
logger = _logger_object.logger
