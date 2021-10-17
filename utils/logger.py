import logging
import threading

from glob import glob
from os import path, makedirs, remove, get_terminal_size
from collections import defaultdict
from utils.decorator import base_decorator
from utils.decorator import force_single_call


class calldescr:
    def __init__(self, logdec, *args, **kwargs):
        func_name = f"{logdec.__name__}"
        type_name = f"{logdec.cls.__name__}" if logdec.cls else None

        arg_vals = [
            f"self={logdec}" if logdec else None,
            f"args={args}" if args else None,
            f"kwargs={kwargs}" if kwargs else None,
        ]

        self.func = f"{type_name}.{func_name}" if type_name else func_name
        self.args = ", ".join(filter(None, arg_vals))
        self.ret = None

    def func_call(self, include_args=True):
        func_args = f"{self.args if include_args else str()}"
        return f"{self.func}({func_args})"

    def step_in(self, include_args=True):
        return f"-> {self.func_call(include_args)}"

    def step_out(self, ret, include_args=True):
        self.ret = f"[{ret}]"
        return f"<- {self.func_call(include_args)} ==> {ret}"


class logger(base_decorator):
    """
        This class is both a logging decorator and log handle manager.    \\
        Any function decorated with @logger will have every call made to  \\
        it logged, including params and return values. If nested funciton \\
        calls are decorated, the logfile will show the scope of each call \\
        by indenting the logfile lines according to the callstack depth. 

        This class writes to both a single global logfile, as well as to  \\
        thread local logs
    """

    object_functions = [
        "__init__",
        "__get__",
        "__call__",
        "__getattribute__",
        "func",
        "obj",
        "cls",
        "method_type",
    ]

    _file_max_line_len = 1024
    _strm_max_line_len = get_terminal_size()[0] + 15
    _line_format = "[%(asctime)s] %(threadName)-11s | %(levelname)-7s | %(indentation)s%(message)"
    file_line_format = f"{_line_format}.{_file_max_line_len - len(_line_format)}s"
    strm_line_format = f"{_line_format}.{_strm_max_line_len - len(_line_format)}s"

    thread_loggers = defaultdict(dict)

    class thread_scoped_filter(logging.Filter):
        def __init__(self, thread_name, *args, **kwargs):
            logging.Filter.__init__(self, *args, **kwargs)
            self.thread_name = thread_name

        def filter(self, record):
            record.indentation = logger.get_line_depth()
            return record.threadName == self.thread_name

    def __call__(self, *args, **kwargs):
        desc = calldescr(self, *args, **kwargs)

        logger.update_line_depth(+1)
        logger.write(desc.step_in(include_args=True))
        logger.update_line_depth(+2)

        ret = self.func(*args, **kwargs)

        logger.update_line_depth(-2)
        logger.write(desc.step_out(ret, include_args=False))
        logger.update_line_depth(-1)

        return ret

    @staticmethod
    def get_line_depth(spacing=3):
        id = threading.get_ident()
        if id not in logger.thread_loggers:
            handler = init_thread_logging()
            logger.thread_loggers[id]["handler"] = handler
            logger.thread_loggers[id]["data"] = threading.local()
            logger.thread_loggers[id]["data"].depth = -1

        thread_info = logger.thread_loggers[id]
        depth = thread_info["data"].depth
        return (spacing * " ") * depth

    @staticmethod
    def update_line_depth(increment: int):
        id = threading.get_ident()
        if id not in logger.thread_loggers:
            handler = init_thread_logging()
            logger.thread_loggers[id]["handler"] = handler
            logger.thread_loggers[id]["data"] = threading.local()
            logger.thread_loggers[id]["data"].depth = -1

        logger.thread_loggers[id]["data"].depth += increment

    @staticmethod
    def write(message: str, level=logging.DEBUG):
        root_logger = logging.getLogger()
        root_logger.log(level, message)
        for handle in root_logger.handlers:
            handle.flush()


def init_thread_logging():
    thread_name = threading.Thread.getName(threading.current_thread())
    log_file = f"log/debug.thread.{thread_name}.log"

    log_handler = logging.FileHandler(log_file, mode="w")
    log_handler.setLevel(logging.DEBUG)
    log_formatter = logging.Formatter(logger.file_line_format)
    log_handler.setFormatter(log_formatter)
    log_filter = logger.thread_scoped_filter(thread_name)
    log_handler.addFilter(log_filter)

    rootlogger = logging.getLogger()
    rootlogger.addHandler(log_handler)
    return log_handler


def stop_thread_logging(log_handler):
    root_logger = logging.getLogger()
    root_logger.removeHandler(log_handler)
    log_handler.close()


@force_single_call
def init_logging():
    log_file_path = path.join("log", "debug.all.log")
    log_file_path = path.abspath(log_file_path)

    log_dir_path = path.dirname(log_file_path)
    if not path.exists(log_dir_path):
        makedirs(log_dir_path)
    else:
        old_logfiles = glob(path.join(log_dir_path, "*.log"))
        for old_log in old_logfiles:
            remove(old_log)

    thread_name = threading.Thread.getName(threading.current_thread())
    file_log_filter = logger.thread_scoped_filter(thread_name)
    stream_log_filter = logger.thread_scoped_filter(thread_name)

    log_file_formatter = logging.Formatter(logger.file_line_format)
    log_filehandler = logging.FileHandler(log_file_path, mode="w")
    log_filehandler.setFormatter(log_file_formatter)
    log_filehandler.addFilter(file_log_filter)
    log_filehandler.setLevel(logging.DEBUG)

    log_strm_formatter = logging.Formatter(logger.strm_line_format)
    log_streamhandler = logging.StreamHandler()
    log_streamhandler.setFormatter(log_strm_formatter)
    log_streamhandler.addFilter(stream_log_filter)
    log_streamhandler.setLevel(logging.INFO)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(log_filehandler)
    root_logger.addHandler(log_streamhandler)

    logger.write("Logging initialized", logging.INFO)
