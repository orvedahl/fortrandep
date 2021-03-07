"""
Run all the test problems
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

    tests["test-1"] = {}
    tests["test-2"] = {}
    tests["test-3"] = {}
    tests["test-4"] = {}
    tests["test-5"] = {}
    tests["test-6"] = {}
    tests["test-7"] = {"build":"_build/debug/odir"}
    tests["test-8"] = {"build":"build"}
    tests["pp-test-9"] = {"build":"odir"}
    tests["pp-test-10"] = {"build":"odir"}
    tests["pp-test-11"] = {"build":"odir"}
    tests["pp-test-12"] = {"build":"odir"}
    tests["pp-test-13"] = {"build":"odir"}

    passed = 0
    n_tests = len(tests.keys())
    for tdir in tests.keys():
        print("Running: ", end='')
        print_color("{}".format(tdir), "bold")

        files, excludes, ignores, macros = parse_input(tdir)

        files = [os.path.join(tdir, f) for f in files]

        P = FortranProject(name=tdir, files=files, exclude_files=excludes,
                           ignore_modules=ignores, macros=macros,
                           pp_search_path=search_paths, verbose=True)

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

