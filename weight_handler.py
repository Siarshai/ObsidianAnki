"""
progress dict expects following layout:
{
    "version" : int,
    "progress" : {
        question_uid (str) : {
            "successes" : int,
            "failures" : int,
            "answered" : int,
            "last_success_ts" : int,
            "is_hot" : int
        }
        ...
    }
}
"""
from copy import deepcopy

from typing import Optional, Dict, List


class WeightHandler:
    _SECS_IN_DAY = 86400
    _SECS_IN_WEEK = 7 * _SECS_IN_DAY
    _SECS_IN_MONTH = 4 * _SECS_IN_WEEK
    _SECS_IN_THREE_MONTHS = 3 * _SECS_IN_MONTH
    _TIME_LIMITS = [
        _SECS_IN_DAY,
        _SECS_IN_WEEK,
        _SECS_IN_WEEK,
        _SECS_IN_WEEK
    ]

    CURRENT_PROGRESS_DATA_VERSION = 3
    REASK_WEIGHT_MULTIPLICATION_COEFF = 5

    def __init__(self, question_uids_to_tags: Dict, start_ts: float, progress: Optional[Dict] = None):
        # consciously not updating current ts after start to evade updating every weight on each step
        # this is mostly useless - user won't likely keep program running more than day
        self._start_ts = start_ts
        self._progress = WeightHandler._migrate_progress(progress)
        self.question_uids_to_tags = question_uids_to_tags
        self.question_uids = list(question_uids_to_tags.keys())
        self.weights = [self._compute_weight(self._progress.get(uid, {})) for uid in self.question_uids]
        if not len(self.question_uids):
            raise RuntimeError("No questions loaded")

    @staticmethod
    def _migrate_progress(progress):
        if progress is None:
            return {}
        # can't do much at this point; will need to make sane migration later
        if progress["version"] < 1 or progress["version"] > WeightHandler.CURRENT_PROGRESS_DATA_VERSION:
            print(f"WARNING: Unknown version of saved progress: {progress['version']}")
            return {}
        if progress["version"] <= 2:
            for info in progress["progress"].values():
                info["answered"] = info.get("successes", 0) + info.get("failures", 0)
                info["last_success_ts"] = info.get("last_answered_ts", 0)
                del info["last_answered_ts"]
        return progress["progress"]

    def get_savable_progress(self):
        return {
            "version": WeightHandler.CURRENT_PROGRESS_DATA_VERSION,
            "progress": deepcopy(self._progress)
        }

    def prune_progress_info(self):
        self._progress = {k: v for k, v in self._progress.items() if k in self.question_uids}

    def success_on_question(self, question, ts):
        try:
            i, uid = next((i, uid) for (i, uid) in enumerate(self.question_uids) if question == uid)
            info = self._progress.setdefault(uid, WeightHandler._blank_question_record())
            info["successes"] += 1
            info["answered"] += 1
            info["last_success_ts"] = ts
            info["is_hot"] = False
            cold_weight = self._compute_weight(info)
            # if it was hot - it's still rather hot
            self.weights[i] = ((self.weights[i] + cold_weight) / 2) if self.weights[i] > 1 else cold_weight
        except StopIteration:
            raise RuntimeError(f"WARNING: Could not find path for question {question}")

    def fail_on_question(self, question):
        try:
            i, uid = next((i, uid) for (i, uid) in enumerate(self.question_uids) if question == uid)
            info = self._progress.setdefault(uid, WeightHandler._blank_question_record())
            info["failures"] += 1
            info["answered"] += 1
            info["is_hot"] = True  # make it hot - ask it soon
            self.weights[i] = self._compute_weight(info)
        except StopIteration:
            raise RuntimeError(f"WARNING: Could not find path for question {question}")

    def ambiguity_on_question(self, question):
        try:
            i, uid = next((i, uid) for (i, uid) in enumerate(self.question_uids) if question == uid)
            info = self._progress.setdefault(uid, WeightHandler._blank_question_record())
            info["answered"] += 1
            self.weights[i] *= WeightHandler.REASK_WEIGHT_MULTIPLICATION_COEFF
        except StopIteration:
            raise RuntimeError(f"WARNING: Could not find path for question {question}")

    def get_statistics(self):
        statistics = {
            "successes": 0,
            "failures": 0,
            "answered": 0,
        }
        for info in self._progress.values():
            statistics["successes"] += info.get("successes", 0)
            statistics["failures"] += info.get("failures", 0)
            statistics["answered"] += info.get("answered", 0)
        return statistics

    def reask(self, question):
        try:
            i, _ = next((i, uid) for (i, uid) in enumerate(self.question_uids) if question == uid)
            self.weights[i] *= WeightHandler.REASK_WEIGHT_MULTIPLICATION_COEFF
        except StopIteration:
            raise RuntimeError(f"WARNING: Could not find path for question {question}")

    def _compute_weight(self, info, old_weight=None):
        def _compute_cold_weight():
            delta_answers = float(info.get("successes", 0) - info.get("failures", 0))
            delta_time_secs = self._start_ts - info.get("last_success_ts", self._start_ts)
            recency_multiplier = 1 + sum([int(delta_time_secs > delta) for delta in WeightHandler._TIME_LIMITS])
            return recency_multiplier * (1 + max(0.0, -delta_answers)) / (1.0 + max(0.0, delta_answers))

        def _compute_hot_weight():
            cold_weight = _compute_cold_weight()
            return float(max(len(self.question_uids) / 4, 5 * cold_weight, 5))

        new_weight = _compute_hot_weight() if info.get("is_hot", False) else _compute_cold_weight()
        if old_weight is not None and old_weight > new_weight:
            # when question is asked correctly we diminish its weight gradually
            # program will show it once or twice in the near future to cement the result
            new_weight = (old_weight + new_weight)/2
        return new_weight

    @staticmethod
    def _blank_question_record():
        return {
            "successes": 0,
            "failures": 0,
            "answered": 0,
            "last_success_ts": 0,
            "is_hot": 0
        }
