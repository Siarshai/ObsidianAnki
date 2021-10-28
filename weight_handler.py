"""
progress dict expects following layout:
{
    "version" : int,
    "progress" : {
        question_uid (str) : {
            "successes" : int,
            "failures" : int,
            "last_answered_ts" : int
        }
        ...
    }
}
"""


class WeightHandlerMixin:
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

    def __init__(self, question_uids, start_ts, progress=None):
        self.question_uids = question_uids
        self.weights = []
        # consciously not updating current ts after start to evade updating every weight on each step
        # this is mostly useless - user won't likely keep program running more than day
        self.start_ts = start_ts
        # can't do much at this point; will need to make sane migration later
        if progress and progress["version"] < 1:
            print(f"WARNING: Unknown version of saved progress: {progress['version']}")
            progress = None
        self.progress = {} if progress is None else progress["progress"]
        for uid in self.question_uids:
            self.weights.append(self._compute_cold_weight(self.progress.get(uid, {})))

    def prune_progress_info(self, predicate_to_delete):
        self.progress = {k: v for k, v in self.progress.items() if not predicate_to_delete(k)}

    def _compute_cold_weight(self, info):
        delta_answers = float(info.get("successes", 0) - info.get("failures", 0))
        delta_time_secs = self.start_ts - info.get("last_answered_ts", self.start_ts)
        recency_multiplier = 1 + sum([int(delta_time_secs > delta) for delta in WeightHandlerMixin._TIME_LIMITS])
        return recency_multiplier * (1 + max(0.0, -delta_answers)) / (1.0 + max(0.0, delta_answers))

    def success_on_question(self, question, ts):
        try:
            i, uid = next((i, uid) for (i, uid) in enumerate(self.question_uids) if question == uid)
            info = self.progress.setdefault(
                uid,
                {
                    "successes": 0,
                    "failures": 0,
                    "last_answered_ts": 0
                })
            info["successes"] += 1
            info["last_answered_ts"] = ts
            cold_weight = self._compute_cold_weight(info)
            # if it was hot - it's still rather hot
            self.weights[i] = (self.weights[i] + cold_weight) / 2 if self.weights[i] > 1 else cold_weight
        except StopIteration:
            raise RuntimeError(f"WARNING: Could not find path for question {question}")

    def fail_on_question(self, question):
        try:
            i, uid = next((i, uid) for (i, uid) in enumerate(self.question_uids) if question == uid)
            info = self.progress.setdefault(
                uid,
                {
                    "successes": 0,
                    "failures": 0,
                    "last_answered_ts": 0
                })
            info["failures"] += 1
            cold_weight = self._compute_cold_weight(info)
            # make it hot - ask it soon
            self.weights[i] = max(len(self.weights) / 4, 5 * cold_weight, 5)
        except StopIteration:
            raise RuntimeError(f"WARNING: Could not find path for question {question}")
