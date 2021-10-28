import pickle
import random
from pathlib import Path
from typing import Optional


class QuestionSelector:
    def __init__(self, path_to_questions: Path):
        self._question_paths = [p for p in path_to_questions.rglob("*.md")]

        self._progress = {}
        self._load_saved_progress()

        self._weights = []
        for path in self._question_paths:
            try:
                matched_name = next(name for name in self._progress.keys() if name in str(path))
                self._weights.append(1/(1 + self._progress[matched_name]))
            except StopIteration:
                self._weights.append(1)
        self._current_question_path: Optional[Path] = None

    def load_next_question(self):
        self._current_question_path = random.choices(self._question_paths, weights=self._weights)[0]
        return self._current_question_path.stem

    def load_answer_for_current_question(self):
        try:
            with open(self._current_question_path, "r") as fh:
                return fh.readlines()
        except OSError as e:
            print(f"WARNING: Could not read answer for question {str(self._current_question_path)}: {str(e)}")

    def success_on_current_question(self):
        question = self._current_question_path.stem
        if question in self._progress:
            self._progress[question] += 1
        else:
            self._progress[question] = 1
        try:
            i, path = next((i, path) for (i, path) in enumerate(self._question_paths) if question in str(path))
            # if it was hot - it's still rather hot
            cold_weight = 1/(1 + self._progress[question])
            self._weights[i] = (self._weights[i] + cold_weight)/2 if self._weights[i] > 1 else cold_weight
        except StopIteration as e:
            print(f"WARNING: Could not find path for question {question} even though just loaded it")

    def fail_on_current_question(self):
        question = self._current_question_path.stem
        if question in self._progress:
            if self._progress[question] > 1:
                self._progress[question] -= 1
            else:
                del self._progress[question]
        try:
            i, path = next((i, path) for (i, path) in enumerate(self._question_paths) if question in str(path))
            # make it hot - ask it soon
            self._weights[i] = 10
        except StopIteration as e:
            print(f"WARNING: Could not find path for question {question} even though just loaded it")

    def _load_saved_progress(self):
        progress_filepath = Path("anki_progress.pkl")
        if progress_filepath.exists():
            with open(progress_filepath, "rb") as fh:
                anki_progress = pickle.load(fh)
                if type(anki_progress) is not dict:
                    print("WARNING: progress data is corrupted, starting from scratch")
                self._progress = anki_progress

    def save_progress(self):
        progress_filepath = Path("anki_progress.pkl")
        with open(progress_filepath, "wb") as fh:
            pickle.dump(self._progress, fh)
