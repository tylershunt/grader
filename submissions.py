#!/usr/bin/env python
#
# Python abstraction of a google form
#  Tyler Hunt (thunt@cs.utexas.edu)
#
# A google form is essentially a spreadsheet. You can download
# it as a csv ( which is used as input to this script )

import csv
import time
from UserDict import UserDict, DictMixin
"""
Closeure for Record objects
prevents changing things like pk or time
in an instance which could be disastrous
"""
def get_record_builder(pk, time_col, cols):
    """
    Just a beefy dict, allows me to compare time easily
    and access the id without knowing what the pk is supposed
    to be later
    """
    class Record(UserDict):
        def __init__( self, **kwargs ):
            self.data = dict(kwargs)
            self.id = self.data[pk].lower()

        def __gt__(self, other):
            return self[time_col] >  other[time_col]
        
        def __lt__(self, other):
            return self[time_col] <  other[time_col]
        
        def __ge__(self, oter):
            return self[time_col] >= other[time_col]
        
        def __le__(self, other):
            return self[time_col] >= other[time_col]
        
        def __eq__(self, other):
            return self[time_col] == other[time_col]
        
    def builder(row):
        d = { cols[i]:row[i] for i in cols }
        d[time_col] = time.strptime( d[time_col], GoogleForm.time_format )
        d[pk] = d[pk].lower()
        return Record(**d)

    return builder


"""
Google form objects are read only; They can
be accesssed loosly like dictionaries
(eg you can specify a primary key and it will return a record)
Fields cna be named anything you want but need to be included
as a dictionary when is created (cols)
"""
class GoogleForm(DictMixin):
    default_cols = {0:"time", 3:"eid", 1:"f_name", 2:"l_name", 
                    7:"url", 8:"sha", 6:"email" }
    default_pk   = "eid"
    default_time = "time"

    time_format = r'%m/%d/%Y %H:%M:%S'



    def __init__(self, pk=default_pk, time_col=default_time,
                 cols=default_cols):
        self.records  = {}
        self.row_to_record = get_record_builder( pk, time_col, cols )


    """
    Try to add record (r), will not add record if a record exists
    which has the same pk and is newer
    @returns True if insert is successful
    """
    def insert( self, r ):      
        if not self.records.get(r.id) or self.records[ r.id ] < r:
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


    """
    Access to the underlaying dictionary (required for dictmixin to be
    useful
    """
    def __getitem__(self, key):
        return self.records[key]


    """
    Just provides an informative message when this happens we don't want
    to be able to change Records willy-nilly
    """
    def __setitem__(self, key):
        raise TypeError, "You cannot update a Google_Form this way use" \
                         +"self.row_to_record()"


    """
    More dictmixin compatablility
    """
    def keys(self):
        return self.records.keys()


    """
    More dictmixin compatablility
    """
    def __delitem__(self, key):
        del self.records[key]
