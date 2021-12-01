from states.state_enum import State
from utils.function_selector import FunctionSelector


def get_on_statistics_shown(selector):
    def pretty_print_statistics(*args, **kwargs):
        statistics = selector.get_statistics()
        print("Total answered questions: ", statistics["answered"])
        print("Correctly: ", statistics["successes"])
        print("Somewhat correctly: ", statistics["answered"] - statistics["failures"] - statistics["successes"])
        print("Incorrectly: ", statistics["failures"])
        return None

    function_selector = FunctionSelector()
    function_selector.set_on_command_function(
        ("s", "statistics"),
        pretty_print_statistics,
        "Show more robust statistics over all answered questions")
    function_selector.set_on_command_function(
        ("r", "reask"),
        lambda *args, **kwargs: selector.reask_last_question(),
        "Reask last question after a little while (stacks)")
    function_selector.set_on_command_function(
        ("c", "continue"),
        lambda *args, **kwargs: State.QUESTION_REQUIRED,
        "Continue answering questions")
    function_selector.set_on_command_function(
        ("?", "h", "help"),
        lambda *args, **kwargs: print(function_selector.get_help()),
        "Show this hint")

    def on_question_displayed(state, context):
        print("\n---")
        if selector.history:
            print("\nLast answered questions:")
            for question in selector.history[::-1]:
                print(question)
        else:
            print("\nNo questions yet been answered")
        print("\n---")
        command = input(f"What to do next? {function_selector.get_hint()}\n")
        try:
            return function_selector(command, context=context)
        except StopIteration:
            print(f"Unknown command: {command}")
            print(function_selector.get_help())
        return None

    return on_question_displayed