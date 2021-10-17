import logging
import threading

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
    class scope_indent_filter(logging.Filter):
        def filter(self, record):
            record.indentation = line_indent()
            return True

    thread_local = threading.local()
    thread_local.depth = 0

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

    @staticmethod
    def get_logger(name=f"debug_{threading.get_ident()}"):
        thread_logger = logging.getLogger(name)
        return thread_logger

    def __call__(self, *args, **kwargs):
        desc = calldescr(self, *args, **kwargs)
        logger.thread_local.depth += 1
        logger.write(desc.step_in(include_args=True))

        ret = self.func(*args, **kwargs)

        logger.write(desc.step_out(ret, include_args=False))
        logger.thread_local.depth -= 1
        return ret

    @staticmethod
    def write(message: str):
        logline = f"{line_indent(logger.thread_local.depth)}{message}"
        thread_logger = logger.get_logger()
        thread_logger.debug(logline[logger.line_truncate_slice])
        for handle in thread_logger.handlers:
            handle.flush()

        return logline


def line_indent(depth=None, spacing=3):
    if depth is None:
        depth = logger.thread_local.depth
    return (spacing * " ") * depth


@force_single_call
def init_logging():
    logfilter = logger.scope_indent_filter()
    logformatter = logging.Formatter("[%(asctime)s] %(indentation)s %(message)s")

    logfilehandler = logging.FileHandler("debug.log", mode="w")
    logfilehandler.setFormatter(logformatter)
    logfilehandler.addFilter(logfilter)
    logfilehandler.setLevel(logging.DEBUG)

    logstreamhandler = logging.StreamHandler()
    logstreamhandler.setFormatter(logformatter)
    logstreamhandler.addFilter(logfilter)
    logstreamhandler.setLevel(logging.DEBUG)

    rootlogger = logging.getLogger()
    rootlogger.setLevel(logging.DEBUG)
    rootlogger.addHandler(logfilehandler)
    rootlogger.addHandler(logstreamhandler)
