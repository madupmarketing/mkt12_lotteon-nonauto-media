import unittest

from utils.upload_policy import already_uploaded, is_auto_run, should_upload


class UploadPolicyTests(unittest.TestCase):
    def test_uploads_when_no_errors_exist(self):
        self.assertTrue(should_upload([]))

    def test_skips_upload_when_errors_exist_by_default(self):
        self.assertFalse(should_upload(["RTB House 오류: login failed"]))

    def test_allows_partial_upload_when_explicitly_enabled(self):
        self.assertTrue(should_upload(["Buzzvil 데이터 없음"], allow_partial=True))


class AlreadyUploadedTests(unittest.TestCase):
    def test_true_when_date_row_exists(self):
        values = [["날짜", "매체구분"], ["2026-11-14", "BSA"], ["2026-11-15", "RTB_APP"]]
        self.assertTrue(already_uploaded(values, "2026-11-15"))

    def test_false_when_date_row_missing(self):
        values = [["날짜", "매체구분"], ["2026-11-14", "BSA"]]
        self.assertFalse(already_uploaded(values, "2026-11-15"))

    def test_ignores_empty_rows_and_whitespace(self):
        values = [[], [" 2026-11-15 ", "BSA"]]
        self.assertTrue(already_uploaded(values, "2026-11-15"))
        self.assertFalse(already_uploaded([[]], "2026-11-15"))


class IsAutoRunTests(unittest.TestCase):
    def test_schedule_is_auto(self):
        self.assertTrue(is_auto_run("schedule"))

    def test_dispatch_without_dates_is_auto(self):
        self.assertTrue(is_auto_run("workflow_dispatch", "", "", ""))
        self.assertTrue(is_auto_run("workflow_dispatch", "  ", "", ""))

    def test_dispatch_with_any_date_is_manual(self):
        self.assertFalse(is_auto_run("workflow_dispatch", "2026-11-24", "", ""))
        self.assertFalse(is_auto_run("workflow_dispatch", "", "2026-11-20", "2026-11-24"))

    def test_other_events_are_not_auto(self):
        self.assertFalse(is_auto_run("push"))
        self.assertFalse(is_auto_run(""))


if __name__ == "__main__":
    unittest.main()
