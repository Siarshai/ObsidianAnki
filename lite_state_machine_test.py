import unittest
from enum import Enum
import timeout_decorator
from lite_state_machine import LiteStateMachine
from functools import wraps


class TestStates(str, Enum):
    BEGIN = "BEGIN"
    STATE1 = "STATE1"
    STATE2 = "STATE2"


def returner(retval):
    def echo(*args, **kwargs):
        return retval

    return echo


def call_with_trace(f, trace_dest):
    @wraps(f)
    def wrapper(*args, **kwargs):
        retval = f(*args, **kwargs)
        trace_dest.append(retval)
        return retval

    return wrapper


def call_with_trace_in_context(f, trace_tag):
    @wraps(f)
    def wrapper(*args, **kwargs):
        retval = f(*args, **kwargs)
        args[1].setdefault(trace_tag, []).append(retval)
        return retval

    return wrapper


class MyTestCase(unittest.TestCase):
    # Infinite loop inside, should add timeout just in case.
    # Shouldn't consume much time though - loop does not loop indefinitely if code is alright
    @timeout_decorator.timeout(0.1, timeout_exception=StopIteration)
    def test_state_cb_called_in_right_order(self):
        trace = []
        sm = LiteStateMachine(TestStates.BEGIN)
        sm.set_on_state_cb(TestStates.BEGIN,
                           call_with_trace(returner(TestStates.STATE1), trace))
        sm.set_on_state_cb(TestStates.STATE1,
                           call_with_trace(returner(TestStates.STATE2), trace))
        sm.set_on_state_cb(TestStates.STATE2,
                           call_with_trace(returner(None), trace))
        sm.set_head_step_cb(lambda s, c: s != TestStates.STATE2)
        sm.set_on_transition_cb((TestStates.BEGIN, TestStates.STATE1),
                                call_with_trace(returner("TBS1"), trace))
        sm.set_on_transition_cb((TestStates.STATE1, TestStates.STATE2),
                                call_with_trace(returner("TS1S2"), trace))
        sm.start_main_loop()
        self.assertEqual([TestStates.STATE1, "TBS1", TestStates.STATE2, "TS1S2"], trace)

    @timeout_decorator.timeout(0.1, timeout_exception=StopIteration)
    def test_state_cb_called_in_right_order(self):
        sm = LiteStateMachine(TestStates.BEGIN, {"trace": [TestStates.BEGIN]})
        sm.set_on_state_cb(TestStates.BEGIN,
                           call_with_trace_in_context(returner(TestStates.STATE1), "trace"))
        sm.set_on_state_cb(TestStates.STATE1,
                           call_with_trace_in_context(returner(TestStates.STATE2), "trace"))
        sm.set_on_state_cb(TestStates.STATE2,
                           call_with_trace_in_context(returner(None), "trace"))
        sm.set_head_step_cb(lambda s, c: s != TestStates.STATE2)
        sm.set_on_transition_cb((TestStates.BEGIN, TestStates.STATE1),
                                call_with_trace_in_context(returner("TBS1"), "trace"))
        sm.set_on_transition_cb((TestStates.STATE1, TestStates.STATE2),
                                call_with_trace_in_context(returner("TS1S2"), "trace"))
        sm.start_main_loop()
        context = sm.get_context()
        self.assertEqual([TestStates.BEGIN, TestStates.STATE1, "TBS1", TestStates.STATE2, "TS1S2"],
                         context["trace"])

    @timeout_decorator.timeout(0.1, timeout_exception=StopIteration)
    def test_state_loops_and_default_transitions_work(self):
        counter = 0

        def increment_counter(s, c):
            nonlocal counter
            counter += 1

        def head_exit_on_counter(s, c):
            nonlocal counter
            return counter != 10

        sm = LiteStateMachine(TestStates.BEGIN)
        sm.set_on_state_cb(TestStates.BEGIN, lambda s, c: TestStates.BEGIN)
        sm.set_default_on_transition_cb(increment_counter)
        sm.set_head_step_cb(head_exit_on_counter)
        sm.start_main_loop()
        self.assertEqual(10, counter)

    @timeout_decorator.timeout(0.1, timeout_exception=StopIteration)
    def test_state_loops_and_default_on_state_cb_work(self):
        counter = 0

        def increment_counter(s, c):
            nonlocal counter
            counter += 1
            return TestStates.BEGIN

        def head_exit_on_counter(s, c):
            nonlocal counter
            return counter != 10

        sm = LiteStateMachine(TestStates.BEGIN)
        sm.set_on_state_cb(TestStates.BEGIN, lambda s, c: TestStates.STATE1)
        sm.set_default_on_state_cb(increment_counter)
        sm.set_default_on_transition_cb(lambda s, c: None)
        sm.set_head_step_cb(head_exit_on_counter)
        sm.start_main_loop()
        self.assertEqual(10, counter)

    @timeout_decorator.timeout(0.1, timeout_exception=StopIteration)
    def test_stop_iteration_stops_state_machine(self):
        # exception is consumed inside
        sm = LiteStateMachine(TestStates.BEGIN, {"test": "nochange"})
        sm.set_on_state_cb(TestStates.BEGIN, lambda s, c: exec('raise StopIteration("stop")'))
        sm.set_on_state_cb(TestStates.STATE1, lambda s, c: exec('raise RuntimeError("stop")'))
        sm.set_on_state_cb(TestStates.STATE2, lambda s, c: exec('raise RuntimeError("stop")'))
        sm.start_main_loop()
        self.assertEqual({"test": "nochange"}, sm.get_context())
        # no checks needed, should just exit normally


if __name__ == '__main__':
    unittest.main()
