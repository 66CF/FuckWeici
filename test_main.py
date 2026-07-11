import unittest
from unittest.mock import patch

import main


class NoChoiceDevice:
    is_king_mode = False

    def get_positional_text(self, key):
        return ""

    def get_choices(self):
        return None, None, None


class SolverCompletionTests(unittest.TestCase):
    def test_choice_solvers_report_no_operation_when_choices_are_missing(self):
        device = NoChoiceDevice()
        with patch("main._report"):
            for solver in (
                main.solve_english_to_chinese,
                main.solve_mixed,
                main.solve_listening,
            ):
                with self.subTest(solver=solver.__name__):
                    self.assertFalse(solver(device, object(), 0))

    def test_solve_question_rejects_solver_without_operation(self):
        with patch.dict(main.SOLVERS, {999: lambda *_: False}):
            with self.assertRaises(main.QuestionNotCompletedError):
                main.solve_question(999, object(), object(), 0)

    def test_solve_question_accepts_completed_operation(self):
        with patch.dict(main.SOLVERS, {999: lambda *_: True}):
            main.solve_question(999, object(), object(), 0)


if __name__ == "__main__":
    unittest.main()
