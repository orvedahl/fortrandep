"""
Run all the test problems

To add a new test:

    1) make a new directory and add it to the 'tests' dictionary, using the directory
       name as the key. Be sure to include a "note" that describes the purpose of the
       test. Additional testing parameters specific to this test can be included
       here as well, but their extraction/inclusion in the main loop must be added.

    2) in the new test directory, build your source tree and add any source code

    3) make a file named "source_files.txt" formatted as:

           source : <rel path to source file 1>
           source : <rel path to source file 2>
           source : <rel path to source file 3>
             .
             .
             .
           exclude : <rel path of file 1 to exclude>
           exclude : <rel path of file 2 to exclude>
             .
             .
             .
           ignore : <module 1 name to ignore>
           ignore : <module 2 name to ignore>
             .
             .
             .
           macro : <name> = <value>
           macro : <name> = <value>
           macro : <name> = <value>
             .
             .
             .

       the dots indicate "repeat as necessary", ordering of lines is unimportant.
           source = an actual source file
           exclude = a file to ignore
           ignore = the name of a module to ignore (not the filename)
           macro = define a preprocessor macro for use with #ifdef and #ifndef

    4) run this test suite as "python run_tests.py"

"""
from __future__ import print_function
import os
import sys
from collections import OrderedDict
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fortrandep import FortranProject

colors = {
    "purple"    : '\033[95m',
    "cyan"      : '\033[96m',
    "darkcyan"  : '\033[36m',
    "blue"      : '\033[94m',
    "green"     : '\033[92m',
    "yellow"    : '\033[93m',
    "red"       : '\033[91m',
    "bold"      : '\033[1m',
    "underline" : '\033[4m',
    "end"       : '\033[0m',
}
def print_color(text, color):
    if (color not in colors.keys()):
        raise KeyError("Color = {} not defined".format(color))
    x = '{}{}{}'.format(colors[color], text, colors["end"])
    print(x)

def parse_input(tdir):
    with open(os.path.join(tdir, "source_files.txt"), "r") as f:
        sources = []
        excludes = []
        ignores = []
        macros = []
        for line in f:
            fields = line.split(":")
            entry = fields[1].strip()

            if line.startswith("source"):
                sources.append(entry)

            if line.startswith("exclude"):
                excludes.append(entry)

            if line.startswith("ignore"):
                ignores.append(entry)

            if line.startswith("macro"):
                m = entry.split("=")
                macros.append("{}={}".format(m[0],m[1]))

    return sources, excludes, ignores, macros

def main():

    search_paths = ["include"]

    tests = OrderedDict() # key is directory, value is dictionary of test parameters

    tests["test-1"] = {"note":['single file project']}
    tests["test-2"] = {"note":['single file project, with module']}
    tests["test-3"] = {"note":['multifile project', 'single src/ location']}
    tests["test-4"] = {"note":['multifile project', 'two src/ locations']}
    tests["test-5"] = {"note":['multifile project', 'multiple src/ directories']}
    tests["test-6"] = {"note":['multifile project', 'multiple src/, ignore module']}
    #--
    tests["test-7"] = {"build":"_build/debug/odir",
                       "note":['multifile project', 'multiple src/', 'ignore mod',
                               'build specified']}
    tests["test-8"] = {"build":"build",
                       "note":['multifile project', 'multiple src/', 'ignore mod',
                               'build specified', 'include file']}
    #--
    tests["pp-test-9"] = {"build":"odir",
                          "note":['multifile project', 'multiple src/', 'ignore mod',
                                  'build specified', '#include file']}
    #--
    tests["pp-test-10"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', '#ifdef & defined']}
    tests["pp-test-11"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', '#ifdef & undefined']}
    #--
    tests["pp-test-12"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', '#ifdef-else & defined']}
    tests["pp-test-13"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', '#ifdef-else & undefined']}
    #--
    tests["pp-test-14"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', '#ifndef-else & undefined']}
    tests["pp-test-15"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', '#ifndef-else & defined']}
    #--
    tests["test-16"] = {"build":"build",
                       "note":['multifile project', 'multiple src/', 'ignore mod',
                               'build specified', 'include file', 'exclude file']}

    verbose = True
    print_dependencies = False

    passed = 0
    n_tests = len(tests.keys())
    for tdir in tests.keys():
        print("Running: ", end='')
        print_color("{}".format(tdir), "bold")
        if (verbose):
            if ("note" in tests[tdir].keys()):
                print("\tParameters:")
                for x in tests[tdir]["note"]:
                    print("\t\t{}".format(x))

        files, excludes, ignores, macros = parse_input(tdir)

        files = [os.path.join(tdir, f) for f in files]

        P = FortranProject(name=tdir, files=files, exclude_files=excludes,
                           ignore_modules=ignores, macros=macros,
                           pp_search_path=search_paths, verbose=print_dependencies)

        build = tests[tdir].pop("build", None)
        P.write_dependencies(os.path.join(tdir, "depends.mak"), overwrite=True, build=build)

        if (P.success):
            print("\t",end=''); print_color("Pass", "green")
            passed += 1
        else:
            print("\t",end=''); print_color("Fail", "green")

    print("\nSuccessful tests: {}".format(passed))
    print("Total tests run : {}\n".format(n_tests))

if __name__ == "__main__":
    main()

