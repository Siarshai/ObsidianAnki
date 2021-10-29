import pickle
import random
import time
from pathlib import Path
from typing import Optional

from weight_handler import WeightHandler


class QuestionSelector:
    def __init__(self, path_to_questions: Path, with_prune: bool):
        self._path_to_questions = path_to_questions
        self._with_prune = with_prune
        progress = QuestionSelector._load_saved_progress()
        self.current_question_path: Optional[Path] = None
        self._wh: Optional[WeightHandler] = None
        self._reload_index_impl(progress)

    def _load_questions_list(self):
        return [p for p in self._path_to_questions.rglob("*.md")]

    def load_next_question(self):
        self.current_question_path = random.choices(self._wh.question_uids, weights=self._wh.weights)[0]
        return self.current_question_path.stem

    def load_answer_for_current_question(self):
        try:
            with open(self.current_question_path, "r") as fh:
                return fh.readlines()
        except OSError as e:
            raise OSError(f"Could not read answer for question {str(self.current_question_path)}: {str(e)}")

    def reload_index(self):
        self._reload_index_impl(self._wh.get_savable_progress())

    def _reload_index_impl(self, progress):
        question_uids = self._load_questions_list()
        self._wh = WeightHandler(question_uids, time.time(), progress)
        if self._with_prune:
            self._wh.prune_progress_info(lambda uid: uid not in question_uids)
        self.current_question_path: Optional[Path] = None

    def success_on_current_question(self):
        self._wh.success_on_question(self.current_question_path, time.time())

    def fail_on_current_question(self):
        self._wh.fail_on_question(self.current_question_path)

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
                pickle.dump(self._wh.get_savable_progress(), fh)
        except OSError:
            print("WARNING: Could not save progress data")
