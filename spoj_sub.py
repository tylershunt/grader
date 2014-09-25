#!/usr/bin/env python

import re
import mechanize
import sys
import urllib2
import time
import argparse

spoj_login = "" #SPOJ USERNAME HERE
spoj_passwd = "" #SPOJ PASSWORD HERE
sub_url = "http://www.spoj.com/submit"
RESULTS_URL = "http://www.spoj.com/status/%s/signedlist"
#problemV1 = "PROBTNPO"
#problemV2 = "PROBTRES"
languages = {"python":"4", "python3":"116"}
ID_PATTERN = re.compile(r'.*?<input type="hidden" name="newSubmissionId" value="(\d+)"/>.*')
RE_PATTERN = re.compile(r'^\|\s+(\d+)\s+\|(?:[^|]+\|){2}\s+([\w?]+)\s+\|')

def get_submission_id(the_page):
    '''Parses the response HTML for the unique Spoj submission ID'''

    for line in the_page:
        match = ID_PATTERN.match(line)

        if match:
            return match.group(1)

    return -1

def get_answer(sub_id):
    '''Parses the results and gets the line with the submission status'''

    url = RESULTS_URL % spoj_login
    
    while True:
        time.sleep(1)
        req = urllib2.Request(url)
        for line in urllib2.urlopen(req):
            match = RE_PATTERN.match(line)
            if match and sub_id == match.group(1): 
                if match.group(2) == "??":
                    break
                else: 
                    return match.group(2) == "AC"

def submit(subFile, problem, lang):
    br = mechanize.Browser()
    br.open(sub_url)

	    
    br.select_form(name="login")
    br["login_user"] = spoj_login
    br["password"] = spoj_passwd
    br.submit()

    br.select_form(nr=0)
    try:
        with open(subFile, 'rb') as content:
            br["file"] = content.read()

        br["lang"] = [languages[lang]]
        br["problemcode"] = problem
    except mechanize._form.ControlNotFoundError:
        sys.stderr.write("Login Failed\n")
        sys.exit(1)
    return get_submission_id(br.submit())

def submitFiles(files, problem, lang):
	ids=[]
	for f in files:
		ids.append( submit(f,problem,lang) )
	return ids

def get_results( file_id_pairs ):
    for f,i in file_id_pairs:
		print f,get_answer(i)


def main(files, problem, language):
	ids = submitFiles(files, problem, language)
	get_results( zip(files, ids) )
  
def parse_args():
	global spoj_login, spoj_passwd
	parser = argparse.ArgumentParser(description='Send a set of files to sphere and return the results')
	parser.add_argument('-p', '--problem', default='PROBTNPO')
	parser.add_argument('-l', '--language', default='python3')
	parser.add_argument('-u', '--username', default=spoj_login)
	parser.add_argument('-x', '--password', default=spoj_passwd)
	parser.add_argument('files', metavar='file', nargs='+', help='Files to be judged')
	
	args = parser.parse_args()

	spoj_login = args.username
	spoj_passwd = args.password

	return args.files,args.problem,args.language

if __name__ == '__main__':
    main(*parse_args())
