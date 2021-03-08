# BoxLib routine to write the build info module
#
# BoxLib available at: https://ccse.lbl.gov/Downloads/downloadBoxLib.html
#
#        git clone https://ccse.lbl.gov/pub/Downloads/BoxLib.git
#
# a simple script that writes the build_info.f90 file that is used
# to store information for the job_info file that we store in plotfiles.
#
#
# Modifications:
# 	-remove unused (as of version 1.0) variables/input keywords
#		(2013-04-18 R. Orvedahl)

from __future__ import print_function
import sys
import os
import getopt
import datetime
import string
import subprocess

sourceString="""
module build_info_module

  implicit none

  character (len=128), save :: build_date = &
"@@BUILD_DATE@@"

  character (len=128), save :: build_dir = &
"@@BUILD_DIR@@"

  character (len=128), save :: build_machine = &
"@@BUILD_MACHINE@@"

  character (len=128), save :: FCOMP = &
"$FCOMP$@@FCOMP@@"

  character (len=128), save :: FCOMP_version = &
"@@FCOMP_VERSION@@"

  character (len=250), save :: f90_compile_line = &
@@F90_COMP_LINE@@ 

  character (len=250), save :: link_line = &
@@LINK_LINE@@

  character (len=128), save :: source_git_hash = &
"$SOURCE_HASH$@@SOURCE_HASH@@"

end module build_info_module
"""

# usage
def usage():

    print("\nScript to generate the build_info.f90 module. This script is")
    print("based on the BoxLib routine makebuildinfo.py. There are a few")
    print("modifications to the original code.\n")
    print("\tR. Orvedahl (2013-04-18)\n")
    print("Usage:\n")
    print("    makebuildinfo.py <OPTIONS>\n")
    print("    --FCOMP <FCOMP>                  F90 compiler\n")
    print("    --FCOMP_VERSION <version>        Compiler version\n")
    print("    --f90_compile_line <comp line>   Line used for compiling\n")
    print("    --link_line <link line>          Line used for linking\n")
    print("    --source_home <source dir>       Where the source code lives\n")

# using a subprocess, run the command "command" in the shell and pipe the 
# output to standard out to be stored in p 
def runcommand(command):
    p = subprocess.Popen(command.split(), stdout=subprocess.PIPE)
    out = p.stdout.read()
    return out.strip()


try: opts, next = getopt.getopt(sys.argv[1:], "",
                               ["FCOMP=",
                                "FCOMP_version=",
                                "f90_compile_line=",
                                "link_line=",
                                "source_home="])
except getopt.GetoptError:
    print("\n---Invalid Calling Sequence---")
    usage()
    sys.exit(2)

FCOMP = ""
FCOMP_version = ""
f90_compile_line = ""
link_line = ""
source_home = ""

for o, a in opts:

    if o == "--FCOMP":
        FCOMP = a

    if o == "--FCOMP_version":
        FCOMP_version = a

    if o == "--f90_compile_line":
        f90_compile_line = a

    if o == "--link_line":
        link_line = a

    if o == "--source_home":
        source_home = a

MAX_STRING_LENGTH=128
DBL_STRING_LINE_LENGTH=125

# assemble some information

# build stuff
build_date = str(datetime.datetime.now())
build_dir = os.getcwd()
build_machine = runcommand("uname -a")

# git hashes
runningDir = os.getcwd()

# store git hash for source directory
# work-around for now:
if (len(source_home.split()) > 1):
    source_home = source_home.split()[0]
    source_home.replace("\n","")

# remove any spaces that makefile might put in
source_home = source_home.replace(" ","")

os.chdir(source_home)
source_hash = runcommand("git rev-parse HEAD")
os.chdir(runningDir)

# output
fout = open("build_info.f90", "w")

for line in sourceString.splitlines():

    index = line.find("@@")

    if (index >= 0):
        index2 = line.rfind("@@")

        keyword = line[index+len("@@"):index2]

        if (keyword == "BUILD_DATE"):
            newline = string.replace(line, "@@BUILD_DATE@@", build_date[:MAX_STRING_LENGTH])
            fout.write(newline)

        elif (keyword == "BUILD_DIR"):
            newline = string.replace(line, "@@BUILD_DIR@@", build_dir[:MAX_STRING_LENGTH])
            fout.write(newline)

        elif (keyword == "BUILD_MACHINE"):
            newline = string.replace(line, "@@BUILD_MACHINE@@", 
                                     build_machine[:MAX_STRING_LENGTH])
            fout.write(newline)

        elif (keyword == "FCOMP"):
            newline = string.replace(line, "@@FCOMP@@", 
                                     FCOMP)
            fout.write(newline)            

        elif (keyword == "FCOMP_VERSION"):
            newline = string.replace(line, "@@FCOMP_VERSION@@", 
                                     FCOMP_version[:MAX_STRING_LENGTH])
            fout.write(newline)            

        elif (keyword == "F90_COMP_LINE"):
            # this can span 2 lines
            if (len(f90_compile_line) > DBL_STRING_LINE_LENGTH):
                str = f90_compile_line[:DBL_STRING_LINE_LENGTH] + "\"// &\n\"" + \
                      f90_compile_line[DBL_STRING_LINE_LENGTH:2*DBL_STRING_LINE_LENGTH]
            else:
                str = f90_compile_line

            newline = string.replace(line, "@@F90_COMP_LINE@@", 
                                     "\"%s\"" % (str))
            fout.write(newline)

        elif (keyword == "LINK_LINE"):
            # this can span 2 lines
            if (len(link_line) > DBL_STRING_LINE_LENGTH):
                str = link_line[:DBL_STRING_LINE_LENGTH] + "\"// &\n\"" + \
                      link_line[DBL_STRING_LINE_LENGTH:2*DBL_STRING_LINE_LENGTH]
            else:
                str = link_line

            newline = string.replace(line, "@@LINK_LINE@@", 
                                     "\"%s\"" % (str))
            fout.write(newline)

        elif (keyword == "SOURCE_HASH"):
            newline = string.replace(line, "@@SOURCE_HASH@@", source_hash)
            fout.write(newline)

    else:
        fout.write(line)

    fout.write("\n")

fout.close()
