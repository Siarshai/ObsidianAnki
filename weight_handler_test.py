import unittest

from weight_handler import WeightHandler


class WeightHandlerTest(unittest.TestCase):
    def test_weights_are_equal_by_default_no_saved_state(self):
        wh = WeightHandler(
            ["path/question1", "path/question2", "path/question3"],
            1001000,
            None)
        self.assertEqual(len(wh.weights), 3)
        self.assertTrue(all(wh.weights[0] == w for w in wh.weights))

    def test_weights_are_equal_by_default_partial_saved_state(self):
        wh = WeightHandler(
            ["path/question1", "path/question2", "path/question3"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 0,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    },
                    "path/question2": {
                        "successes": 0,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    }
                }
            })
        self.assertEqual(len(wh.weights), 3)
        self.assertTrue(all(wh.weights[0] == w for w in wh.weights))

    def test_weights_depend_on_previous_successes(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    },
                    "path/question2": {
                        "successes": 0,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    }
                }
            })
        self.assertEqual(len(wh.weights), 2)
        self.assertLess(wh.weights[0], wh.weights[1])

    def test_weights_depend_on_previous_failures(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 0,
                        "failures": 1,
                        "last_answered_ts": 1000000,
                    },
                    "path/question2": {
                        "successes": 0,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    }
                }
            })
        self.assertEqual(len(wh.weights), 2)
        self.assertGreater(wh.weights[0], wh.weights[1])

    def test_weights_depend_on_time(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    },
                    "path/question2": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 0,
                    }
                }
            })
        self.assertEqual(len(wh.weights), 2)
        self.assertLess(wh.weights[0], wh.weights[1])

    def test_weights_depend_on_previous_hotness(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                        "is_hot": True
                    },
                    "path/question2": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                        "is_hot": False
                    }
                }
            })
        self.assertEqual(len(wh.weights), 2)
        self.assertGreater(wh.weights[0], wh.weights[1])

    def test_reask_increases_weight(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                        "is_hot": True
                    },
                    "path/question2": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                        "is_hot": True
                    }
                }
            })
        self.assertEqual(wh.weights[0], wh.weights[1])
        wh.reask("path/question1")
        self.assertGreater(wh.weights[0], wh.weights[1])
        weight_after_first_reask = wh.weights[0]
        wh.reask("path/question1")
        self.assertGreater(wh.weights[0], weight_after_first_reask)

    def test_weights_updated_after_success(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000000,
            None)
        wh.success_on_question("path/question2", 1000000)
        self.assertGreater(wh.weights[0], wh.weights[1])

    def test_weights_updated_after_failure(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000000,
            None)
        wh.fail_on_question("path/question2")
        self.assertLess(wh.weights[0], wh.weights[1])

    def test_weights_updated_after_ambiguity(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000000,
            None)
        self.assertEqual(wh.weights[0], wh.weights[1])
        wh.ambiguity_on_question("path/question2")
        self.assertLess(wh.weights[0], wh.weights[1])

    def test_weights_record_kept_after_success(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000000,
            None)
        self.assertEqual(len(wh._progress), 0)
        wh.success_on_question("path/question2", 1000000)
        self.assertEqual(len(wh._progress), 1)
        self.assertGreater(len(wh._progress["path/question2"]), 0)

    def test_weights_record_kept_after_failure(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000000,
            None)
        self.assertEqual(len(wh._progress), 0)
        wh.fail_on_question("path/question2")
        self.assertEqual(len(wh._progress), 1)
        self.assertGreater(len(wh._progress["path/question2"]), 0)

    def test_weight_relaxed_gradually_after_wrong_then_correct_answer(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000000,
            None)
        wh.fail_on_question("path/question2")
        wh.success_on_question("path/question2", 1000000)
        self.assertLess(wh.weights[0], wh.weights[1])  # still greater!

    def test_prune(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    },
                    "path/question2": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 0,
                    }
                }
            })
        self.assertEqual(len(wh._progress), 2)
        wh.prune_progress_info(lambda question_uid: "question2" in question_uid)
        self.assertEqual(len(wh._progress), 1)
        self.assertGreater(len(wh._progress["path/question1"]), 0)

    def test_statistics(self):
        wh = WeightHandler(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 3,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "answered": 2,
                    },
                    "path/question2": {
                        "successes": 2,
                        "failures": 4,
                        "answered": 3,
                    }
                }
            })
        statistics = wh.get_statistics()
        self.assertEqual(statistics["successes"], 3)
        self.assertEqual(statistics["failures"], 4)
        self.assertEqual(statistics["answered"], 5)


if __name__ == '__main__':
    unittest.main()
