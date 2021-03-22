"""
A simple script that returns (to stdout) the object names (".o" files)
by parsing the previously written dependency file.
"""

from __future__ import print_function
import sys
import os

def find_objects(dependency_file, output_file):

    objects = []

    build_dir = None

    with open(dependency_file, "r") as f:

        for Line in f:
            if (Line.lstrip().startswith("#:")):

                # first find the build directory
                if ("build_dir =" in Line and build_dir is None):
                    build_dir = Line.split("build_dir =")[1]
                    build_dir = build_dir.strip()
                    continue

                # parse the filename
                fname = Line.split("#:")[1]
                fname = fname.strip()       # remove any extraneous spaces

                # change extension
                name = os.path.split(fname)[1]
                oname = os.path.splitext(name)[0] + ".o"

                objects.append(os.path.join(build_dir, oname))

    with open(output_file, "w") as f:
        f.write("#\n# This file is generated automatically. DO NOT EDIT!\n#\n")
        f.write("objects :=\n")
        for obj in objects:
            f.write("objects += {}\n".format(obj))

    # generate a space separated list and "return" it by printing
    #list_objects = " ".join(objects)
    #print(list_objects)

if __name__ == "__main__":

    dependency_file = sys.argv[1]

    output_file = sys.argv[2]

    find_objects(dependency_file, output_file)
