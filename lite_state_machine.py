from typing import Callable, Dict, Any, Optional, Tuple
from copy import deepcopy

class LiteStateMachine(object):
    def __init__(self, initial_state: Any, initial_context: Optional[Dict[Any, Any]] = None):
        self._current_state = initial_state
        self._context = deepcopy(initial_context) if initial_context else {}
        self._head_step_cb = None
        self._on_state_cbs = {}
        self._default_on_state_cb = None
        self._on_transition_cbs = {}
        self._default_on_transition_cb = None

    def get_context(self):
        return self._context

    def set_on_state_cb(self, state: Any,
                        cb: Callable[[Any, Dict[Any, Any]], Any]):
        if state in self._on_state_cbs:
            raise RuntimeError(f"{state} is already registered")
        self._on_state_cbs[state] = cb

    def set_on_transition_cb(self, states_key: Tuple[Any, Any],
                             cb: Callable[[Any, Dict[Any, Any]], None]):
        if states_key in self._on_transition_cbs:
            raise RuntimeError(f"{states_key} is already registered")
        self._on_transition_cbs[states_key] = cb

    def set_head_step_cb(self, cb: Callable[[Any, Dict[Any, Any]], bool]):
        if self._head_step_cb:
            raise RuntimeError("Head step is already registered")
        self._head_step_cb = cb

    def set_default_on_state_cb(self, cb: Callable[[Any, Dict[Any, Any]], Any]):
        if self._default_on_state_cb:
            raise RuntimeError("Default on state callback is already registered")
        self._default_on_state_cb = cb

    def set_default_on_transition_cb(self, cb: Callable[[Any, Dict[Any, Any]], None]):
        if self._default_on_transition_cb:
            raise RuntimeError("Default transition callback is already registered")
        self._default_on_transition_cb = cb

    def start_main_loop(self):
        try:
            while True:
                if self._head_step_cb:
                    should_continue = self._head_step_cb(self._current_state, self._context)
                    if not should_continue:
                        break

                if self._current_state not in self._on_state_cbs:
                    if self._default_on_state_cb:
                        new_state = self._default_on_state_cb(self._current_state, self._context)
                    else:
                        raise RuntimeError(f"HALT: No callback for state {self._current_state} "
                                           f"and no default callback")
                else:
                    new_state = self._on_state_cbs[self._current_state](self._current_state, self._context)

                transition_key = (self._current_state, new_state)
                if transition_key not in self._on_transition_cbs:
                    if self._default_on_transition_cb:
                        self._default_on_transition_cb(transition_key, self._context)
                    else:
                        raise RuntimeError(f"HALT: No callback for transition "
                                           f"{self._current_state} -> {new_state} "
                                           f"and no default transition")
                else:
                    self._on_transition_cbs[transition_key](transition_key, self._context)

                self._current_state = new_state
        except StopIteration as si:
            print(f"HALT: State machine is stopped with 'StopIteration': {si}, use head step instead")
