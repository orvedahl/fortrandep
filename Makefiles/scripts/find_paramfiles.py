# a simple script that returns (to stdout) the paths to _params
# files given a list of directories to search (as arguments on the
# commandline).  This is used in various makefiles to get the input
# for write_input_params.py
#
# this code is based on BoxLib routines

from __future__ import print_function
import sys
import os

def findparams(paramFileDirs):

    params = []

    # loop over every directory
    for d in paramFileDirs:

        # is the _params file in this directory
        f = os.path.normpath(os.path.join(d, "_params"))
        if (os.path.isfile(f)):
            params.append(f)

    # this is the old python2 way:
    #for f in params:
    #    # equivalent of fortran write(*,101,advance='no')
    #    # so this will print:
    #    #      file1 file2 file3 file4
    #    print f,
    list_files = " ".join(params)
    print(list_files)

if __name__ == "__main__":

    paramFileDirs = sys.argv[1:]

    findparams(paramFileDirs)
