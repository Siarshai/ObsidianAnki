import unittest

from weight_handler import WeightHandlerMixin


class WeightHandlerTest(unittest.TestCase):
    def test_weights_are_equal_by_default(self):
        wh = WeightHandlerMixin(
            ["path/question1", "path/question2", "path/question3"],
            1000000,
            None)
        self.assertEqual(len(wh.weights), 3)
        self.assertTrue(all(wh.weights[0] == w for w in wh.weights))

    def test_weights_depend_on_previous_attempts(self):
        wh = WeightHandlerMixin(
            ["path/question1", "path/question2"],
            1000100,
            {
                "version": 1,
                "progress": {
                    "path/question1": {
                        "successes": 1,
                        "failures": 0,
                        "last_answered_ts": 1000000,
                    }
                }
            })
        self.assertEqual(len(wh.weights), 2)
        self.assertLess(wh.weights[0], wh.weights[1])

    def test_weights_depend_on_time(self):
        wh = WeightHandlerMixin(
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

    def test_weights_updated_after_success(self):
        wh = WeightHandlerMixin(
            ["path/question1", "path/question2"],
            1000000,
            None)
        wh.success_on_question("path/question2", 1000000)
        self.assertGreater(wh.weights[0], wh.weights[1])

    def test_weights_updated_after_failure(self):
        wh = WeightHandlerMixin(
            ["path/question1", "path/question2"],
            1000000,
            None)
        wh.fail_on_question("path/question2")
        self.assertLess(wh.weights[0], wh.weights[1])

    def test_weights_record_kept_after_success(self):
        wh = WeightHandlerMixin(
            ["path/question1", "path/question2"],
            1000000,
            None)
        self.assertEqual(len(wh.progress), 0)
        wh.success_on_question("path/question2", 1000000)
        self.assertEqual(len(wh.progress), 1)
        self.assertGreater(len(wh.progress["path/question2"]), 0)

    def test_weights_record_kept_after_failure(self):
        wh = WeightHandlerMixin(
            ["path/question1", "path/question2"],
            1000000,
            None)
        self.assertEqual(len(wh.progress), 0)
        wh.fail_on_question("path/question2")
        self.assertEqual(len(wh.progress), 1)
        self.assertGreater(len(wh.progress["path/question2"]), 0)

    def test_prune(self):
        wh = WeightHandlerMixin(
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
        self.assertEqual(len(wh.progress), 2)
        wh.prune_progress_info(lambda question_uid: "question2" in question_uid)
        self.assertEqual(len(wh.progress), 1)
        self.assertGreater(len(wh.progress["path/question1"]), 0)


if __name__ == '__main__':
    unittest.main()
