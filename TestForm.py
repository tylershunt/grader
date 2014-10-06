#!/usr/bin/env python
from submissions import GoogleForm
import unittest
import StringIO
defalut_cols = {0:"time", 3:"eid", 1:"f_name", 2:"l_name", 
                7:"url", 8:"sha", 6:"email" }
class TestGoogleForm(unittest.TestCase):

    def setUp(self):
        self.test_file = "1/2/1992 4:30:12,Some,Student,eid1,,,email@a.com," +\
                "https://github.com/uname/repo,12345,\n" +\
            "1/2/1992 4:31:12,Other,Student,eid2,,,email@someplace.com," +\
                "https://github.com/uname/repo,12345,\n" +\
            "1/2/1992 4:30:14,Some,Student,eid1,,,email@someplace.com," +\
                "https://github.com/uname/repo,12346,\n"


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

    def test_form_add_function(self):
        pk = "eid123"
        record = ["1/2/1992 4:30:12", "Some", "Student", pk, "", "",
                  "email@someplace.com", "https://github.com/uname/repo",
                  "12345"]
        form = GoogleForm()
        form.add(record)
        self.assertEqual(form[pk]["f_name"], "Some")
        self.assertEqual(form[pk]["l_name"], "Student")
        self.assertEqual(form[pk]["eid"], "eid123")



    def test_record_time(self):
        pk = 'eid1'
        old_record = ["1/2/1992 4:30:12", "Some", "Student", pk, "", "",
                      "email@someplace.com", "https://github.com/uname/repo",
                      "12345"]
        new_record = ["1/3/1992 4:30:12", "Some", "Student", pk, "", "",
                      "email@someplace.com", "https://github.com/uname/repo",
                      "54321"]
        form = GoogleForm()
        form.insert(form.row_to_record(old_record))
        form.insert(form.row_to_record(new_record))
        form.insert(form.row_to_record(old_record))
        self.assertEqual(form[pk]["sha"], "54321")

    def test_load(self):
        test_file = StringIO.StringIO(self.test_file)
        form = GoogleForm()
        form.load(test_file)
        self.assertEqual(len(form), 2)

if __name__ == '__main__':
    unittest.main()
