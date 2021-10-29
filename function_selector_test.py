import unittest

from function_selector import FunctionSelector


class FunctionSelectorTest(unittest.TestCase):
    _fs_ut = FunctionSelector()

    @classmethod
    def setUpClass(cls):
        # FunctionSelector is stateless, we can initialize it once
        FunctionSelectorTest._fs_ut.set_on_command_function(
            ("n", "nope"), lambda *args, **kwargs: 0)
        FunctionSelectorTest._fs_ut.set_on_command_function(
            ("y", "YOLO"), lambda *args, **kwargs: 1)
        FunctionSelectorTest._fs_ut.set_on_command_function(
            "a", lambda *args, **kwargs: 2*args[0])
        FunctionSelectorTest._fs_ut.set_on_command_function(
            "k", lambda *args, **kwargs: 2*kwargs["k"])

    def test_valid_inputs(self):
        for command in ("n", "nope", "NoPe"):
            self.assertEqual(FunctionSelectorTest._fs_ut(command), 0)
        for command in ("Y", "yolo", "YOLO"):
            self.assertEqual(FunctionSelectorTest._fs_ut(command), 1)

    def test_invalid_inputs_raises(self):
        for command in ("123", "n   ", "yyyy", "p", ""):
            with self.assertRaises(StopIteration):
                FunctionSelectorTest._fs_ut(command)

    def test_adding_intersecting_input_raises(self):
        with self.assertRaises(RuntimeError):
            FunctionSelectorTest._fs_ut.set_on_command_function(
                ("+", "Yolo"), lambda: 2)

    def test_args_passed_to_registered_function(self):
        self.assertEqual(FunctionSelectorTest._fs_ut("a", 10), 20)

    def test_kwargs_passed_to_registered_function(self):
        self.assertEqual(FunctionSelectorTest._fs_ut("k", k=10), 20)

    def test_hint(self):
        self.assertEqual(FunctionSelectorTest._fs_ut.get_hint(), "(n/y/a/k)")


if __name__ == '__main__':
    unittest.main()
