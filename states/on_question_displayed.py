from states.state_enum import State
from utils.function_selector import FunctionSelector


def get_on_question_displayed(selector):
    def show_answer(*args, **kwargs):
        try:
            for line in selector.load_answer_for_current_question():
                print(line, end="")
            return State.ANSWER_DISPLAYED
        except OSError as e:
            print(f"WARNING: {str(e)}")
            print("Have you renamed file while program was running?")
            print("Restoring index...")
            selector.reload_index()
            return State.QUESTION_REQUIRED

    function_selector = FunctionSelector()
    function_selector.set_on_command_function(
        ("c", "continue"),
        show_answer,
        "Show answer for displayed question")
    function_selector.set_on_command_function(
        ("n", "next"),
        lambda *args, **kwargs: State.QUESTION_REQUIRED,
        "Show next question")
    function_selector.set_on_command_function(
        ("s", "stats"),
        lambda *args, **kwargs: State.STATISTICS_SHOWN,
        "Show last answered questions and other statistics")
    function_selector.set_on_command_function(
        ("x", "exit"),
        lambda *args, **kwargs: State.EXITING,
        "Exit program, save data")
    function_selector.set_on_command_function(
        ("?", "help"),
        lambda *args, **kwargs: print(function_selector.get_help()),
        "Show this hint")

    def on_question_displayed(state, context):
        print("\n---")
        command = input(f"Continue? {function_selector.get_hint()}\n")
        try:
            return function_selector(command, context=context)
        except StopIteration:
            print(f"Unknown command: {command}")
            print(function_selector.get_help())
        return None

    return on_question_displayed