"""
Preprocess a single input file and write the results to the specified output

Usage:
    preprocess.py [options] <input_file> <output_file>

Options:
    --overwrite    Overwrite the output file [default: False]
    --macros=<m>   Comma separated list of "name=value" macros do define
    --search=<s>   Comma separated list of search paths to include
    --verbose      Print more information to the screen [default: False]
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from fortrandep.preprocessor import FortranPreprocessor

def main(input_file, output, macros, paths, overwrite, verbose):

    if (os.path.isfile(output) and (not overwrite)):
        print("\nOutput file already exists: {}".format(output))
        print("\n\tTo overwrite this file use the \"--overwrite\" argument\n")
        sys.exit()

    # process input commands or assign defaults
    try:
        macros = macros.split(",")
        if (verbose):
            print("\nUser-defined macros:")
            for m in macros:
                print("\t{}".format(m))
    except:
        macros = None
    try:
        search_paths = paths.split(",")
        if (verbose):
            print("\nIncluded paths:")
            for s in search_paths:
                print("\t{}".format(s))
    except:
        search_paths = ["."]

    # build the preprocessor
    pp = FortranPreprocessor(macros=macros, search_paths=search_paths)
    if (verbose):
        print("\nUsed macros:")
        for k in pp.macros.keys():
            print("\t{} = {}".format(k, pp.macros[k]))
        print("\nUsed search paths:")
        for k in pp.search_paths:
            print("\t{}".format(k))

    # read the input file into a list of source lines
    with open(input_file, "r") as f:
        text = f.readlines()

    print("\nParsing input...")
    processed_text = pp.parse(text)

    # write the processed text to new file
    with open(output, "w") as f:
        for line in processed_text:
            f.write("{}".format(line))

    print("\nOutput written to: {}\n".format(output))

if __name__ == "__main__":
    from docopt import docopt
    args = docopt(__doc__)

    inputfile = args['<input_file>']
    outfile   = args['<output_file>']
    macros    = args['--macros']
    paths     = args['--search']
    overwrite = args['--overwrite']
    verbose   = args['--verbose']

    main(inputfile, outfile, macros, paths, overwrite, verbose)

