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
           'source' refers to an actual source file
           'exclude' refers to a file that will be ignored
           'ignore' references the name of a module to ignore (not the filename)
           'macro' defines a preprocessor macro

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
    """
    Print the text string to standard output in the given color
    """
    if (color not in colors.keys()):
        raise KeyError("Color = {} not defined".format(color))
    x = '{}{}{}'.format(colors[color], text, colors["end"])
    print(x)

def parse_input(tdir):
    """
    Parse the "source_files.txt" file in the given directory for the
    test parameters.
    """
    sources = []
    excludes = []
    ignores = []
    macros = []
    with open(os.path.join(tdir, "source_files.txt"), "r") as f:
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

def compare_files(file1, file2):
    """
    Determine if the two files contain the same dependency information
    """

    entries1 = {}
    with open(file1, "r") as f:
        for line in f:
            if (line.lstrip().startswith("#")): continue
            if (line.strip() == ""): continue

            entries = line.split(":")
            obj = entries[0].strip()
            dep = entries[1].strip()
            if (obj not in entries1.keys()):
                entries1[obj] = [dep]
            else:
                if (dep not in entries1[obj]):
                    entries1[obj].append(dep)
                else:
                    e = "{} contains two entries for {} : {}"
                    print(e.format(file1, obj, dep))

    for k in entries1.keys():
        entries1[k].sort()

    entries2 = {}
    with open(file2, "r") as f:
        for line in f:
            if (line.lstrip().startswith("#")): continue
            if (line.strip() == ""): continue

            entries = line.split(":")
            obj = entries[0].strip()
            dep = entries[1].strip()
            if (obj not in entries2.keys()):
                entries2[obj] = [dep]
            else:
                if (dep not in entries2[obj]):
                    entries2[obj].append(dep)
                else:
                    e = "{} contains two entries for {} : {}"
                    print(e.format(file2, obj, dep))

    for k in entries2.keys():
        entries2[k].sort()

    return entries1 == entries2

def main():
    """
    Run all the tests and determine which ones pass/fail
    """

    # paths to where #include files can be found
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
    #--
    tests["pp-test-16"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', 'nested #ifdef & one defined']}
    tests["pp-test-17"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', 'nested #ifdef & other one defined']}
    tests["pp-test-18"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', 'nested #ifdef & neither defined']}
    tests["pp-test-19"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', 'nested #ifdef & neither defined',
                                   '#define inside #ifdef']}
    tests["pp-test-20"] = {"build":"odir",
                           "note":['multifile project', 'multiple src/', 'ignore mod',
                                   'build specified', 'nested #ifdef & one defined',
                                   '#define inside #ifdef (never reached)']}

    verbose = True
    print_dependencies = False

    passed = 0
    n_tests = len(tests.keys())
    for tdir in tests.keys(): # loop over each test directory
        print("\nRunning: ", end='')
        print_color("{}".format(tdir), "bold")
        if (verbose):
            if ("note" in tests[tdir].keys()):
                print("\tParameters:")
                for x in tests[tdir]["note"]:
                    print("\t\t{}".format(x))

        # find the parameters for this test
        files, excludes, ignores, macros = parse_input(tdir)

        files = [os.path.join(tdir, f) for f in files] # give appropriate path to all files

        # build the project
        P = FortranProject(name=tdir, files=files, exclude_files=excludes,
                           ignore_modules=ignores, macros=macros,
                           pp_search_path=search_paths, verbose=print_dependencies)

        # write the dependency file to the proper directory
        build = tests[tdir].pop("build", None)
        P.write(os.path.join(tdir, "depends.mak"), overwrite=True, build=build)

        if (P.success): # dependency file was written successfully

            # check for correctness
            success = compare_files(os.path.join(tdir, "depends.mak"),
                                    os.path.join(tdir, "solution.mak"))

            if (success):
                print("\t",end=''); print_color("Pass", "green")
                passed += 1
            else:
                print("\t",end=''); print_color("Fail", "red")

        else: # dependency file was not written
            print("\t",end=''); print_color("Failed to write", "red")

    print("\nSuccessful tests: {}".format(passed))
    print("Total tests run : {}\n".format(n_tests))

if __name__ == "__main__":
    main()

