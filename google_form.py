#!/usr/bin/env python
#
# Python abstraction of a google form
#  Tyler Hunt (thunt@cs.utexas.edu)
#
# A google form is essentially a spreadsheet. You can download
# it as a csv ( which is used as input to this script )
#
# I want to support actions that you would need to do to a google
# form and have it behave as a kind of light_weight database


# these denote the collumns of the google spreadsheed where
# data is located
TIME_IDX  = 0
EID_IDX   = 3
FNAME_IDX = 1
LNAME_IDX = 2
URL_IDX   = 7
SHA_IDX   = 8
EMAIL_IDX = 6
EMAIL_RGX  = re.compile(r'^[^@]+@[^@]+\.[^@]+$')
GITHUB_RGX = re.compile(r'github.com[:/]([^/]+)/([^/]+)/?')

class Student():
   def __init__(self, **data):
      # google form data
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
      return self.badEmail or self.badUrl or self.badSha or self.missingFiles

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

   
def lower( string ):
   return string.lower() if string else None

class Google_Form:
   time_format = r'%m/%d/%Y %H:%M:%S'
   class Record:
      def __init__(self, **kwargs):
         self.eid          = kwargs['eid'] #must have eid
         self.f_name       = kwargs.get('f_name')
         self.l_name       = kwargs.get('l_name')
         self.url          = kwargs.get('url')
         self.github_uname = kwargs.get('github_uname')
         self.cs_uname     = kwargs.get('cs_uname')
         self.sha          = kwargs.get('sha')
         self.email        = kwargs.get('email')
         self.time_str     = kwargs.get('time_str')
         self.time         = kwargs.get('time')
         self.partner_eid  = kwargs.get('partner_eid')
         self.standardize()

      def standardize( self ):
         self.eid = lower(self.eid)
         self.url = lower(self.url)
         self.github_uname = lower(self.github_uname)
         self.cs_uname = lower( self.cs_uname )
         self.email = lower(self.email)
         if not self.time:
            self.time = time.strptime(self.time_str, time_format)
                        

   def __init__(self):
      self.students = {}
   def update():
      pass
