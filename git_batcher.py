#!/usr/bin/env python
#
# Utility for batching git operations
#
import sys
from subprocess      import check_call, CalledProcessError
from multiprocessing import Pool

error_strm = sys.stderr

def git_error_log( message, error ):
    print >>error_strm, "{}: {}".format(message, error)

"""
Run Spawn a subprocess and catch any errors
"""
def run( cmnd ):
    try:
        check_call( cmnd )
        return True
    except CalledProcessError as e:
        git_error_log( " ".join(cmnd), e.returncode )
    return False


"""
Call git (like exec) to clone url into dest_dir
"""
def git_clone( url, dest_dir ):
    return (dest_dir, run( ['git', 'clone', url, dest_dir] ) )

"""
Call git (like exec) to checkout commit sha in dest_dir
"""
def git_checkout( sha, dest_dir ):
    return (dest_dir, run( ['git', '-C', dest_dir, 'checkout', sha] ) )

def pool_run( f, arg_list ):
    pool = Pool()
    return pool.map( f, arg_list )

"""
Clone the repositories in repo_list concurrently repositories
will be cloned from urls specified into the destinations specified
@param repo_list - a list of tuples of the form: (url, dest_dir)
@returns result_list - a list of tuples including the destination
and weather or not the clone was successful
"""
def git_clone_batch( repo_list ):
    return pool_run( git_clone, repo_list )


"""
Checkout specified commits, works much in the same fassion as
git_clone_batch
"""
def git_checkout_batch( commit_list ):
    return pool_run( git_checkout, commit_list )
