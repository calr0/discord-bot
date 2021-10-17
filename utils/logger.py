import logging
import threading

from glob import glob
from os import path, makedirs, remove
from collections import defaultdict
from utils.decorator import base_decorator
from utils.decorator import force_single_call

"""
Description:
    Stores thread local data and a logger 
    handle specific for each thread

Note:
    No lock needed around thread_loggers
    sice the GIL makes defaultdict threadsafe
    by default when reading/writing to it
"""
thread_loggers = defaultdict(dict)


def get_log_scope_indentation(spacing=3):
    id = threading.get_ident()
    if id not in thread_loggers:
        handler = start_thread_logging()
        thread_loggers[id]["handler"] = handler
        thread_loggers[id]["data"] = threading.local()
        thread_loggers[id]["data"].depth = 0

    thread_info = thread_loggers[id]
    depth = thread_info["data"].depth
    return (spacing * " ") * depth


def update_thread_scope(increment: int):
    id = threading.get_ident()
    if id not in thread_loggers:
        handler = start_thread_logging()
        thread_loggers[id]["handler"] = handler
        thread_loggers[id]["data"] = threading.local()
        thread_loggers[id]["data"].depth = 0

    thread_loggers[id]["data"].depth += increment


def get_thread_logger():
    return logger.get_logger(f"thread.{threading.get_ident()}.logger")


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
    file_format = "[%(asctime)s] %(threadName)-11s | %(levelname)-7s | %(indentation)s %(message)s"
    line_truncate_slice = slice(None, 1024)
    log_args = True

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

    class scope_indent_filter(logging.Filter):
        def filter(self, record):
            record.indentation = get_log_scope_indentation()
            return True

    class thread_scoped_filter(logging.Filter):
        def __init__(self, thread_name, *args, **kwargs):
            logging.Filter.__init__(self, *args, **kwargs)
            self.thread_name = thread_name

        def filter(self, record):
            record.indentation = get_log_scope_indentation()
            return record.threadName == self.thread_name

    @staticmethod
    def get_logger(name=f"debug_{threading.get_ident()}"):
        thread_logger = logging.getLogger(name)
        return thread_logger

    def __call__(self, *args, **kwargs):
        desc = calldescr(self, *args, **kwargs)

        update_thread_scope(+1)
        logger.write(desc.step_in(include_args=True))
        update_thread_scope(+2)

        ret = self.func(*args, **kwargs)

        update_thread_scope(-2)
        logger.write(desc.step_out(ret, include_args=False))
        update_thread_scope(-1)
        return ret

    @staticmethod
    def write(message: str):
        thread_logger = logger.get_logger()
        thread_logger.debug(message[logger.line_truncate_slice])
        for handle in thread_logger.handlers:
            handle.flush()

        return message


def start_thread_logging():
    thread_name = threading.Thread.getName(threading.current_thread())
    log_file = f"log/debug.thread.{thread_name}.log"

    log_handler = logging.FileHandler(log_file, mode="w")
    log_handler.setLevel(logging.DEBUG)

    log_formatter = logging.Formatter(logger.file_format)
    log_handler.setFormatter(log_formatter)

    log_filter = logger.thread_scoped_filter(thread_name)
    log_handler.addFilter(log_filter)

    rootlogger = logging.getLogger()
    rootlogger.addHandler(log_handler)

    return log_handler


def stop_thread_logging(log_handler):
    # Remove thread log handler from root logger
    logging.getLogger().removeHandler(log_handler)

    # Close the thread log handler so that the lock on log file can be released
    log_handler.close()


@force_single_call
def init_logging():
    log_file_path = path.join("log", "debug.all.log")
    log_file_path = path.abspath(log_file_path)
    log_dir_path = path.dirname(log_file_path)

    if not path.exists(log_file_path):
        makedirs(log_dir_path)
    else:
        old_logfiles = glob(path.join(log_dir_path, "*.log"))
        for old_log in old_logfiles:
            remove(old_log)

    log_formatter = logging.Formatter(logger.file_format)
    log_filter = logger.scope_indent_filter()
    log_filehandler = logging.FileHandler(log_file_path, mode="w")
    log_filehandler.setFormatter(log_formatter)
    log_filehandler.addFilter(log_filter)
    log_filehandler.setLevel(logging.DEBUG)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(log_filehandler)
