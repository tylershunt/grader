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
from Google_Form import GoogleForm

PUBLIC_FILES = ['{}-RunCollatz.in', 
                '{}-RunCollatz.out', 
                '{}-TestCollatz.c++', 
                '{}-TestCollatz.out'
               ]
P_STUDENTS = '.students'
SUBS_DIR_NAME = 'submissions'
EMAIL_RGX  = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
GITHUB_RGX = re.compile(r'github.com[:/](?P<uname>[^/]+)/(?P<repo>[^/]+)/?')
GITHUB_SSH = "git@github.com:{}/{}"
col_names = { 0:"time", 3:"eid", 1:"f_name", 2:"l_name", 
   7:"url", 8:"sha", 6:"email" }

pk  = "eid"
url = "url"



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

def standardize_urls( form ):
   for key in form:
      match = GITHUB_RGX.search(form[key][url])
      if match:
         form[key][url] = GITHUB_SSH.format(match.group('uname'), match.group('repo')) 
      

def main( args ):
   form = GoogleForm( cols=col_names )
   form.load( args.google_form )
   sandardize_urls( form )
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
