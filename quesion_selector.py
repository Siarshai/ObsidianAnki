import pickle
import random
import time
from pathlib import Path
from typing import Optional, List

from weight_handler import WeightHandler


class QuestionSelector:
    _MAX_HISTORY = 10

    def __init__(self, paths_to_questions: List[Path],
                 with_prune: bool,
                 path_to_save_data_dir: Optional[Path] = None):
        self._paths_to_questions = paths_to_questions
        self._with_prune = with_prune
        self._path_to_save_file = QuestionSelector._resolve_path_to_save_file(path_to_save_data_dir)
        progress = self._load_saved_progress()
        self.current_question_path: Optional[Path] = None
        self.history: List[Path] = []
        self._wh: Optional[WeightHandler] = None
        self._reload_index_impl(progress)
        if not len(self._wh.question_uids):
            raise RuntimeError("No questions loaded")

    def _load_questions_list(self):
        mds_globs = [dirpath.rglob("*.md") for dirpath in self._paths_to_questions]
        return [p for glob in mds_globs for p in glob]

    def load_next_question(self):
        def _get_distinct_from_last_question():
            question = random.choices(self._wh.question_uids, weights=self._wh.weights)[0]
            if self.history:
                while question == self.history[-1]:
                    question = random.choices(self._wh.question_uids, weights=self._wh.weights)[0]
            return question

        if self.current_question_path:
            self.history.append(self.current_question_path)
        if len(self.history) > QuestionSelector._MAX_HISTORY:
            self.history.pop(0)
        self.current_question_path = _get_distinct_from_last_question()
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

    def ambiguity_on_current_question(self):
        self._wh.ambiguity_on_question(self.current_question_path)

    def reask_last_question(self):
        if self.history:
            self._wh.reask(self.history[-1])

    def get_statistics(self):
        return self._wh.get_statistics()

    @staticmethod
    def _resolve_path_to_save_file(path_to_save_data_dir):
        if path_to_save_data_dir is not None:
            if not path_to_save_data_dir.exists():
                path_to_save_data_dir.mkdir(parents=True)
            elif not path_to_save_data_dir.is_dir():
                raise OSError("Specified path to save data is not a dir")
        if path_to_save_data_dir is None:
            path_to_save_data = Path("anki_progress.pkl")
        else:
            path_to_save_data = path_to_save_data_dir.joinpath("anki_progress.pkl")
        return path_to_save_data

    def _load_saved_progress(self):
        if self._path_to_save_file.exists():
            with open(self._path_to_save_file, "rb") as fh:
                anki_progress = pickle.load(fh)
                if type(anki_progress) is not dict:
                    print("WARNING: progress data is corrupted, starting from scratch")
                return anki_progress
        return None

    def save_progress(self):
        progress_data = self._wh.get_savable_progress()
        try:
            with open(self._path_to_save_file, "wb") as fh:
                pickle.dump(progress_data, fh)
        except OSError:
            print("WARNING: Could not save progress data")
