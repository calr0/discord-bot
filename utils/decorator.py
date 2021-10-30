class base_decorator:
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

    def __init__(self, func, obj=None, cls=None, method_type="function"):
        self.func = func
        self.obj = obj
        self.cls = cls
        self.method_type = method_type

    def __get__(self, obj=None, cls=None):
        if self.obj == obj and self.cls == cls:
            return self

        method_type = (
            "staticmethod"
            if isinstance(self.func, staticmethod)
            else "classmethod"
            if isinstance(self.func, classmethod)
            else "instancemethod"
        )

        return object.__getattribute__(self, "__class__")(self.func.__get__(obj, cls), obj, cls, method_type)

    def __call__(self, *args, **kwargs):
        """
        ### Description

        Wraps/overrides decorated function or method call.

        Derived classes must implement.

        ### Example
        ```
            # create class derived from base_decorator
            class print_func_calls(base_decorator):
                # override __call__ to print each function
                # decorated with @print_func_call.
                #
                # This will print:
                #   "Entering: <type>.<function>(<args>)"
                #   right before the decorated function is called
                #
                # and:
                #   "Exiting: <type>.<function>(<args>) -> <return value>"
                #   right after the decorated function returns
                def __call__(self, *args, **kwargs):
                    func_name = f"{self.__name__}"
                    type_name = f"{self.cls.__name__}" if self.cls else None

                    arg_vals = [
                        f"self={self}" if self else None,
                        f"args={args}" if args else None,
                        f"kwargs={kwargs}" if kwargs else None,
                    ]

                    func_descr = f"{type_name}.{func_name}" if type_name else func_name
                    args_descr = ", ".join(filter(None, arg_vals))
                    call_descr = f"{func_descr}({args_descr})"

                    print(f"Entering: {call_descr}")
                    ret = self.func(*args, **kwargs)
                    print(f"Exiting: {call_descr} -> {ret}")

                    return ret
        ```
        """
        raise NotImplementedError

    def __getattribute__(self, attr_name):
        if attr_name in base_decorator.object_functions:
            return object.__getattribute__(self, attr_name)
        return getattr(self.func, attr_name)

    def __repr__(self):
        return self.func.__repr__()


class force_single_call(base_decorator):
    called = False

    def __call__(self, *args, **kwargs):
        if force_single_call.called:
            print(f"{self} already called, skipping subsiquent call")
            return None

        force_single_call.called = True
        print(f"{self} called")
        return self.func(*args, **kwargs)
