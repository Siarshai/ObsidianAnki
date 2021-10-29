from io import StringIO
from typing import Dict, Tuple, Callable, Any, Iterable, Optional


class FunctionSelector:
    def __init__(self):
        self._functions: Dict[Tuple[str], Tuple[Callable[[], Any], Optional[str]]] = {}

    def set_on_command_function(self, inputs: Iterable[str], fn: Callable[[], Any], hint: Optional[str] = None):
        inputs = tuple(i.lower() for i in inputs)
        for existing_input_variants in self._functions.keys():
            for v in existing_input_variants:
                if any((new_input == v) for new_input in inputs):
                    raise RuntimeError(f"{inputs} intersects with "
                                       f"already registered input {existing_input_variants}")
        self._functions[inputs] = (fn, hint)

    def __call__(self, input_string: str):
        input_string = input_string.lower()
        for input_variants, (fn, _) in self._functions.items():
            if any(input_string == v for v in input_variants):
                return fn()
        raise StopIteration("Not found")

    def get_hint(self) -> str:
        return "(" + "/".join(input_variants[0] for input_variants in self._functions.keys()) + ")"

    def get_help(self) -> str:
        ss = StringIO()
        ss.write("Known commands:\n")
        for input_variants, (_, hint) in self._functions.items():
            for v in input_variants[:-1]:
                ss.write(v)
                ss.write(", ")
            ss.write(input_variants[-1])
            if hint is not None:
                ss.write(" - ")
                ss.write(hint)
            ss.write("\n")
        return ss.getvalue()
