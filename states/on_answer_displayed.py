from states.state_enum import State
from utils.function_selector import FunctionSelector


def get_on_answer_displayed(selector):
    def yes(*args, **kwargs):
        ctx = kwargs["context"]
        ctx["right_answers_streak"] = ctx.get("right_answers_streak", 0) + 1
        selector.success_on_current_question()
        return State.QUESTION_REQUIRED

    def no(*args, **kwargs):
        kwargs["context"]["right_answers_streak"] = 0
        selector.fail_on_current_question()
        return State.QUESTION_REQUIRED

    def somewhat(*args, **kwargs):
        selector.ambiguity_on_current_question()
        return State.QUESTION_REQUIRED

    function_selector = FunctionSelector()
    function_selector.set_on_command_function(
        ("y", "yes"),
        yes,
        "Answer was correct, this question will be shown less frequently")
    function_selector.set_on_command_function(
        ("s", "somewhat"),
        somewhat,
        "Answer was somewhat correct. Do not record question as failure, "
        "but show a little more frequently (as in reask command)")
    function_selector.set_on_command_function(
        ("n", "no"),
        no,
        "Answer was not correct, this question will be shown more frequently")
    function_selector.set_on_command_function(
        ("x", "exit"),
        lambda *args, **kwargs: State.EXITING,
        "Exit program, save data")
    function_selector.set_on_command_function(
        ("?", "h", "help"),
        lambda *args, **kwargs: print(function_selector.get_help()),
        "Show this hint")

    def on_answer_displayed(state, context):
        print("\n---")
        command = input(f"Was your answer right? {function_selector.get_hint()}\n")
        try:
            return function_selector(command, context=context)
        except StopIteration:
            print(f"Unknown command: {command}")
            print(function_selector.get_help())
        return None

    return on_answer_displayed