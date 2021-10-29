import argparse
from enum import Enum
from pathlib import Path

from function_selector import FunctionSelector
from lite_state_machine import LiteStateMachine
from quesion_selector import QuestionSelector


class State(str, Enum):
    QUESTION_REQUIRED = "QUESTION_REQUIRED",
    QUESTION_DISPLAYED = "QUESTION_DISPLAYED",
    ANSWER_DISPLAYED = "ANSWER_DISPLAYED",
    EXITING = "EXITING"


def clear_screen():
    print("\033[H\033[J")


def get_on_question_required(selector):
    def print_streak_message(streak):
        if streak == 30:
            print("That's 30 questions answered correctly in a row! Congratulations!\n---\n")
        elif streak == 20:
            print("That's 20 questions answered correctly in a row! Good job!\n---\n")
        elif streak == 10:
            print("That's 10 questions answered correctly in a row! Keep on going!\n---\n")

    def on_question_required(state, context):
        clear_screen()
        print_streak_message(context.get("right_answers_streak", 0))
        question = selector.load_next_question()
        print(question, end="")
        return state.QUESTION_DISPLAYED

    return on_question_required


def get_on_question_displayed(selector):
    def yes(*args, **kwargs):
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
        ("y", "yes"),
        yes,
        "Show answer for displayed question")
    function_selector.set_on_command_function(
        ("s", "skip"),
        lambda *args, **kwargs: State.QUESTION_REQUIRED,
        "Show next question")
    function_selector.set_on_command_function(
        ("x", "exit"),
        lambda *args, **kwargs: State.EXITING,
        "Exit program")
    function_selector.set_on_command_function(
        ("?", "h", "help"),
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

    function_selector = FunctionSelector()
    function_selector.set_on_command_function(
        ("y", "yes"),
        yes,
        "Answer was correct, this question will be shown less frequently")
    function_selector.set_on_command_function(
        ("n", "no"),
        no,
        "Answer was not correct, this question will be shown more frequently")
    function_selector.set_on_command_function(
        ("x", "exit"),
        lambda *args, **kwargs: State.EXITING,
        "Show this hint")
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path_to_questions", help="Path to folder to be recursively searched for .md files")
    args = parser.parse_args()
    try:
        path_to_questions = Path(args.path_to_questions)
    except Exception as e:
        print(f"Could not convert path_to_questions to path: {args.path_to_questions}")
        return -1
    if not path_to_questions.exists():
        print(f"Path does not exist: {args.path_to_questions}")
        return -1
    if not path_to_questions.is_dir():
        print(f"Path is not a directory: {args.path_to_questions}")
        return -1

    qselector = QuestionSelector(path_to_questions)
    state_machine = LiteStateMachine(State.QUESTION_REQUIRED)
    state_machine.set_head_step_cb(lambda s, c: s != State.EXITING)
    state_machine.set_on_state_cb(State.QUESTION_REQUIRED, get_on_question_required(qselector))
    state_machine.set_on_state_cb(State.QUESTION_DISPLAYED, get_on_question_displayed(qselector))
    state_machine.set_on_state_cb(State.ANSWER_DISPLAYED, get_on_answer_displayed(qselector))
    state_machine.set_on_state_cb(State.EXITING, lambda s, c: exit(0))
    state_machine.set_default_on_transition_cb(lambda tup, c: None)

    state_machine.start_main_loop()

    qselector.save_progress()


if __name__ == "__main__":
    main()
