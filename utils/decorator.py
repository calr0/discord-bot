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
        ### Note
            derived class must implement
        ### Example implementation
            ```
            return self.func(*args, **kwargs)
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
