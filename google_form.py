#!/usr/bin/env python
#
# Python abstraction of a google form
#  Tyler Hunt (thunt@cs.utexas.edu)
#
# A google form is essentially a spreadsheet. You can download
# it as a csv ( which is used as input to this script )

import csv

"""
Google form objects are read only; They can
be accesssed loosly like dictionaries
(eg you can specify a primary key and it will return a record)
Fields cna be named anything you want but need to be included
as a dictionary when is created (cols)

"""
class GoogleForm(DictMixin):
    defalut_cols = {0:"time", 3:"eid", 1:"f_name", 2:"l_name", 
                    7:"url", 8:"sha", 6:"email" }
    default_pk   = "eid"
    default_time = "time"

    time_format = r'%m/%d/%Y %H:%M:%S'


    """
    Closeure for Record objects
    prevents changing things like _pk or _time
    in an instance which could be disastrous
    """
    def get_record_builder(_pk, _time, _cols):
        """
        Just a beefy dict, allows me to compare time easily
        and access the id without knowing what the pk is supposed
        to be later
        """
        class Record(UserDict):
            def __init__( self, **kwargs ):
                super(Google_Form, self).__init__(**kwargs)
                self.id = kwargs[_pk].lower()

            def __gt__(self, other):
                return self[_time] > other[_time]
            
            def __lt__(self, other):
                return self[_time] < other[_time]
            
            def __ge__(self, oter):
                return self[_time] >= other[_time]
            
            def __le__(self, other):
                return self[_time] >= other[_time]
            
            def __eq__(self, other):
                return self[_time] == other[_time]
            
            def builder(row):
                d = { _cols[i]:row[i] for i in _cols }
                d[_time] = time.strptime( d[_time], time_format )
                d[_pk] = d[_pk].lower()
                return Record(d)

            return builder


    def __init__(self, pk=default_pk, time_col=default_time,
                 cols=default_cols):
        self.data  = {}
        self.row_to_record = get_record_builder( pk, time_col, cols )


    """
    Try to add record (r), will not add record if a record exists
    which has the same pk and is newer
    @returns True if insert is successful
    """
    def insert( self, r ):      
        if not self.records[ r.id ] or self.records[ r.id ] < r:
            self.records[ r.id ] = r
            return True
        return False


    """
    Try to add updates ( a list of properly formated dictionaries )
    to self.records; uses self.insert
    """
    def insert_batch( self, updates ):
        for record in updates:
        insert( record )


    """
    load a csv file to update self
    """
    def load(self, csv_file):
        with open(csv_sheet) as f:
            reader = csv.reader(f)
            reader.next() # we don't care about col names
            self.update_batch( row_to_record(row) for row in reader)


    def __getitem__(self, key):
        return self.records[key]


    def __setitem__(self, key):
        raise TypeError, "You cannot update a Google_Form this way use" \
                         +"self.row_to_record()"


    def keys(self):
        return self.records.keys()


    def __delitem__(self, key):
        del self.records[key]
