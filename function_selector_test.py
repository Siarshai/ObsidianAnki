import unittest

from function_selector import FunctionSelector


class FunctionSelectorTest(unittest.TestCase):
    _fs_ut = FunctionSelector()

    @classmethod
    def setUpClass(cls):
        # FunctionSelector is stateless, we can initialize it once
        FunctionSelectorTest._fs_ut.set_on_command_function(
            ("n", "nope"), lambda: 0)
        FunctionSelectorTest._fs_ut.set_on_command_function(
            ("y", "YOLO"), lambda: 1)

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

    def test_hint(self):
        self.assertTrue(
            FunctionSelectorTest._fs_ut.get_hint() == "n/y" or
            FunctionSelectorTest._fs_ut.get_hint() == "y/n")


if __name__ == '__main__':
    unittest.main()
