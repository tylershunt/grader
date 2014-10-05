#!/usr/bin/env python
from submissions import GoogleForm
import unittest
defalut_cols = {0:"time", 3:"eid", 1:"f_name", 2:"l_name", 
                7:"url", 8:"sha", 6:"email" }
class TestGoogleForm(unittest.TestCase):

    def setUp(self):
        pass

    def test_record_add(self):
        pk = "eid123"
        record = ["1/2/1992 4:30:12", "Some", "Student", pk, "", "",
                  "email@someplace.com", "https://github.com/uname/repo",
                  "12345"]
        form = GoogleForm()
        form.insert(form.row_to_record(record))
        self.assertEqual(form[pk]["f_name"], "Some")
        self.assertEqual(form[pk]["l_name"], "Student")
        self.assertEqual(form[pk]["eid"], "eid123")


if __name__ == '__main__':
    unittest.main()
