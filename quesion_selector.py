import pickle
import random
import time
from pathlib import Path
from typing import Optional

from weight_handler import WeightHandlerMixin


class QuestionSelector(WeightHandlerMixin):
    def __init__(self, path_to_questions: Path):
        progress = QuestionSelector._load_saved_progress()
        question_uids = [p for p in path_to_questions.rglob("*.md")]
        super().__init__(question_uids, time.time(), progress)
        self.current_question_path: Optional[Path] = None
        self.prune_progress_info(lambda uid: uid not in question_uids)

    def load_next_question(self):
        self.current_question_path = random.choices(self.question_uids, weights=self.weights)[0]
        return self.current_question_path.stem

    def load_answer_for_current_question(self):
        try:
            with open(self.current_question_path, "r") as fh:
                return fh.readlines()
        except OSError as e:
            print(f"WARNING: Could not read answer for question {str(self.current_question_path)}: {str(e)}")

    def success_on_current_question(self):
        self.success_on_question(self.current_question_path, time.time())

    def fail_on_current_question(self):
        self.fail_on_question(self.current_question_path)

    @staticmethod
    def _load_saved_progress():
        progress_filepath = Path("anki_progress.pkl")
        if progress_filepath.exists():
            with open(progress_filepath, "rb") as fh:
                anki_progress = pickle.load(fh)
                if type(anki_progress) is not dict:
                    print("WARNING: progress data is corrupted, starting from scratch")
                return anki_progress
        return None

    def save_progress(self):
        progress_filepath = Path("anki_progress.pkl")
        try:
            with open(progress_filepath, "wb") as fh:
                pickle.dump(self.progress, fh)
        except OSError:
            print("WARNING: Could not save progress data")
