#!/usr/bin/env python
#
# A python based grading set up script by:
#  Tyler Hunt (thunt@cs.utexas.edu)
#

import argparse
import sys
import os
import csv
import re
import time
import pickle
import StringIO
from shutil import rmtree
from sh import git, ErrorReturnCode, mail
from filecmp import dircmp
PUBLIC_FILES = ['{}-RunCollatz.in', '{}-RunCollatz.out', '{}-TestCollatz.c++', '{}-TestCollatz.out']
P_STUDENTS = '.students'
SUBS_DIR_NAME = 'submissions'
# these denote the collumns of the google spreadsheed where
# data is located
TIME_IDX  = 0
EID_IDX   = 3
FNAME_IDX = 1
LNAME_IDX = 2
URL_IDX   = 7
SHA_IDX   = 8
EMAIL_IDX = 6
###########################################################
# RESPONSES
###########################################################
SUBJECT = "({}) CS 371p: Problem With Poject 1 Submission"
OPENING_MESSAGE = "Hello {} {},\nI had a problem processing your submission."
BAD_URL = "It seems that the URL you provided ({}) is either invalid, or the one of the graders does not have access to your repository"
BAD_SHA = "A checkout of the SHA you provided fails. It is possible that you did not push your last commit to github, or perhaps some part of the SHA was mistakenly left off of your Google form submission. SUBMITTED SHA: {}"
MISSING_FILES = "You appear to be missing the files listed below from your private repository. Files should be named precisely and be in the highest level of your repository.\nMissing Files:\n"
MISSING_PUBLIC_FILES = "The public test is missing the following files (or they were misnamed).\nMissing Files:\n"
CLOSING_MESSAGE = "You have 24 Hours from the time this email was sent to fix your submission and resubmit the Google form. Please notify the graders in an email when you have. Unfortunatly this will result in one late day's penalty (20%).\n\nThis message was generated automatically, if you believe anything to be in error please reply to all with your explanation."
###########################################################
# DATA VALIDATION
###########################################################
GOOGLE_TIME_FORMAT = r'%m/%d/%Y %H:%M:%S'
EMAIL_RGX  = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
GITHUB_RGX = re.compile(r'github.com[:/]([^/]+)/([^/]+)/?')

###########################################################
###########################################################
class Student():
   def __init__(self, **data):
      # google form data
      self.eid      = data['eid'].lower()
      self.f_name   = data['first_name']
      self.l_name   = data['last_name']
      self.url      = data['github_url']
      self.sha      = data['git_sha']
      self.email    = data['email']
      self.sub_time = data['time']
      self.ssh_url  = ''

       # descriptors based on data validity  
      self.badEmail = False
      self.badUrl   = False
      self.badSha   = False
      self.missingFiles = None
      self.missingPulicFiles = None

      self.validate()

   def validate_email(self):
      if not EMAIL_RGX.match(self.email):
         badEmail = True

   def validate_url(self):
      match = GITHUB_RGX.search(self.url)
      if match:
         git_id   = match.group(1)
         git_name = match.group(2)
         self.ssh_url = 'git@github.com:{}/{}'.format(git_id, git_name) 
      else:
         self.badUrl = True

   def validate_time( self ):
      self.sub_time = time.strptime(self.sub_time, GOOGLE_TIME_FORMAT)

   def validate(self):
      self.validate_email()
      self.validate_url()
      self.validate_time()

   def isNewerThan(self, other):
      return self.sub_time > other.sub_time

   def isBad( self ):
      return self.badEmail or self.badUrl or self.badSha or self.missingFiles or self.missingPublicFiles

   def notify(self):
      if not self.isBad():
         return
      if self.badEmail:
         print 'no email for {}'.format(self.eid)
      body = open(os.path.join(SUBS_DIR_NAME,self.eid,'reply'), 'w')
      print >>body, OPENING_MESSAGE.format(self.f_name,self.l_name)
      if self.badUrl:
         print >>body, BAD_URL.format(self.url)
      elif self.badSha:
         print >>body,  BAD_SHA.format(self.sha)
      elif self.missingFiles:
         print >>body, MISSING_FILES
         for i in self.missingFiles:
            print >>body, i
         print >>body
      if self.missingPublicFiles:
         print >>body, MISSING_PUBLIC_FILES
         for i in self.missingPublicFiles:
            print >>body, i
      print >>body
      print >>body, CLOSING_MESSAGE 
      body.close()
      with open(os.path.join(SUBS_DIR_NAME,self.eid,'email'), 'w') as f:
         print >>f, self.email
      with open(os.path.join(SUBS_DIR_NAME,self.eid,'subject'), 'w') as f:
         print >>f, SUBJECT.format(self.eid)
      #mail( '-s', SUBJECT.format(self.eid), '-b', 'thunt', '-c', 'downing', self.email,  _in=body.getvalue())

   def __str__(self):
      data = [str(self.eid)]
      if self.badEmail:
         data.append('BadEmail')
      elif self.badUrl:
         data.append('BadUrl')
      elif self.badSha:
         data.append('BadSHA')
      elif self.missingFiles:
         data.extend(self.missingFiles)
         if self.missingPublicFiles:
            data.extend(self.missingPublicFiles)
      return '\n\t'.join(data)

def build_student( line ):
   info = {}
   info['time']       = line[TIME_IDX]
   info['eid']        = line[EID_IDX]
   info['first_name'] = line[FNAME_IDX]
   info['last_name']  = line[LNAME_IDX]
   info['github_url'] = line[URL_IDX]
   info['git_sha']    = line[SHA_IDX]
   info['email']      = line[EMAIL_IDX]
            
   return Student(**info)

def insert( students, s ):
   """
   insert a student into a dictionary; resolve
   conflicts based on the date of submission
   """
   if not s.eid in students:
      students[s.eid] = s
      return
   
   if s.isNewerThan(students[s.eid]):
      students[s.eid] = s


def compare_dirs( example, target ):
   comp = dircmp( example, target )
   return comp.left_only

def check_repo_files( example, s ):
   if s.badUrl or s.badSha:
      return
   r = compare_dirs(example, os.path.join(SUBS_DIR_NAME,s.eid))
   s.missingFiles = r if len(r) > 0 else None


def verifyContents( students, example ):
   for eid in students:
      check_repo_files( example, students[eid] )

def git_clone( url, location ):
   git( 'clone', url, location )

def git_checkout( sha, location ):
   git( '-C', location, 'checkout', sha) 

def fetch_git( s ):
   path = os.path.join( SUBS_DIR_NAME, s.eid )
   try:
      git_clone( s.ssh_url, path )
   except ErrorReturnCode:
      print "COULD NOT clone repo of: {}".format(s.eid)
      s.badUrl = True
      return
   try:
      git_checkout( s.sha, path )
   except ErrorReturnCode:
      s.badSha = True

def download_submissions( students ):
   for eid in students:
      fetch_git( students[eid] )
      
def buildStudentsDict( csv_sheet ):
   students = {}
   with open(csv_sheet) as f:
      reader = csv.reader(f)
      reader.next() # we don't care about col names
      for line in reader:
         insert(students, build_student(line))
   return students

def load_students( google_form ):
   if google_form:
      return buildStudentsDict(google_form)
   try:
      with open(P_STUDENTS, 'rb') as f:
         return pickle.load(f)
   except:
      "could not unpickle {}".format(P_STUDENTS)
      sys.exit(1)
def buildFileStructure( students ):
   os.mkdir(SUBS_DIR_NAME)
   for eid in students:
      os.mkdir(os.path.join(SUBS_DIR_NAME,eid))

def lookForSubs( students, force ):
   if force and os.path.isdir(SUBS_DIR_NAME): 
      rmtree(SUBS_DIR_NAME)

   if not os.path.isdir(SUBS_DIR_NAME):
      buildFileStructure( students )
      return False
   return True

def print_if_wrong(s, notify):
   if s.isBad():
      print s
      if notify:
         s.notify()

def listBad( students, notify ):
   for eid in students:
      print_if_wrong( students[eid], notify )

def checkForPublicTests( s, public ):
   files = ( os.path.join(public,f.format(s.eid)) for f in PUBLIC_FILES)
   missingFiles = [f for f in files if not os.path.isfile(f)]
   s.missingPublicFiles = missingFiles if len(missingFiles) > 0 else None

def verifyPublicFiles(students, public):
   for eid in students:
      checkForPublicTests(students[eid], public)

def main( args ):
   students = load_students( args.google_form )
   if not lookForSubs( students, args.force ):
      download_submissions( students ) #could not find submissions
   verifyContents(students, args.example )
   verifyPublicFiles(students, args.public)
   with open(P_STUDENTS, 'w') as f:
      pickle.dump(students, f)
   listBad( students, args.notify )
def parseArgs():
   global F
   global EXAMPLE
   parser = argparse.ArgumentParser(description='Set up grading environment')
   parser.add_argument('-n', '--notify', action='store_true',
         help='when set send an email to students')
   parser.add_argument('-f', '--force', action='store_true',
                   help='overwrite and destroy at will')
   parser.add_argument('example', help='name of an example directory')
   parser.add_argument('public', help='name of public repo directory')
   parser.add_argument('google_form', nargs='?',
         help='CSV file containing student information')
   
   args = parser.parse_args()
   return parser.parse_args()

if __name__ == '__main__':
   main(parseArgs())
