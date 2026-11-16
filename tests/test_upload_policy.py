import unittest

from utils.upload_policy import already_uploaded, should_upload


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


if __name__ == "__main__":
    unittest.main()
