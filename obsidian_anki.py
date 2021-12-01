import argparse
from pathlib import Path

from states.on_answer_displayed import get_on_answer_displayed
from states.on_question_displayed import get_on_question_displayed
from states.on_question_required import get_on_question_required
from states.on_statistics_shown import get_on_statistics_shown
from states.state_enum import State
from utils.lite_state_machine import LiteStateMachine
from question_selector import QuestionSelector


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prune",
                        help="Remove old records from progress data when encountered",
                        action="store_true")
    parser.add_argument("--save_data_dir",
                        metavar="PATH",
                        help="Save and locate statistics save file in this directory",
                        default=None)
    parser.add_argument("--questions_dirs",
                        metavar="PATH",
                        help="Directories to be recursively searched for .md files",
                        nargs="+")
    args = parser.parse_args()
    return args


def validate_and_convert_args(args):
    try:
        args.paths_to_questions = [Path(p) for p in args.questions_dirs]
    except Exception as e:
        raise ValueError("Could not convert questions_dirs to path") from e
    for dirpath in args.paths_to_questions:
        if not dirpath.exists():
            raise OSError(f"Path does not exist: {dirpath}")
        if not dirpath.is_dir():
            raise OSError(f"Path is not a directory: {str(dirpath)}")
    try:
        args.save_data_dir = Path(args.save_data_dir) if args.save_data_dir is not None else None
    except Exception as e:
        raise ValueError(f"Could not convert save_data_dir to path: {args.save_data_dir}") from e


def main():
    args = parse_args()
    validate_and_convert_args(args)

    try:
        qselector = QuestionSelector(args.paths_to_questions, args.prune, args.save_data_dir)
    except RuntimeError as e:
        print(f"{str(e)}; specified paths: {', '.join(args.questions_dirs)}")
        return -1
    state_machine = LiteStateMachine(State.QUESTION_REQUIRED)
    state_machine.set_head_step_cb(lambda s, c: s != State.EXITING)
    state_machine.set_on_state_cb(State.QUESTION_REQUIRED, get_on_question_required(qselector))
    state_machine.set_on_state_cb(State.QUESTION_DISPLAYED, get_on_question_displayed(qselector))
    state_machine.set_on_state_cb(State.ANSWER_DISPLAYED, get_on_answer_displayed(qselector))
    state_machine.set_on_state_cb(State.STATISTICS_SHOWN, get_on_statistics_shown(qselector))
    state_machine.set_on_state_cb(State.EXITING, lambda s, c: exit(0))
    state_machine.set_default_on_transition_cb(lambda tup, c: None)

    state_machine.start_main_loop()

    qselector.save_progress()


if __name__ == "__main__":
    main()
