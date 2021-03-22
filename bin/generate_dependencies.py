"""
Process a Fortran project and write the dependencies to a file.

The output file can readily be included in a Makefile. This was developed with
the included Makefiles in mind (i.e., FortranDep/Makefiles), so certain
assumptions are being made, such as overwrite, skip_programs, etc.
If these options are important to you, use this routine as a guide to
write your own routine, or modify this one accordingly.

Usage:
    generate_dependencies.py [options] <objects>...

    <objects> is the list of source files to process. If --find-source flag
    is used, then this list holds the search directories that hold the
    source files.

    Some options listed below require space-separated lists (for better
    function within Makefiles), this can be achieved by using quotes
    around the entire list. All options also accept comma separated lists,
    as they are much easier to handle, but hard to do in Makefiles.

    Makefiles do not play well with file/directory names that use spaces

Options:
    --preprocess        Run the preprocessor [default: False]
    --exclude=<e>       String of space separated files to exclude
    --ignore-mods=<m>   String of space separated module names to ignore
    --macros=<m>        String of space separated name=value macro definitions
    --search-paths=<p>  String of space separated search paths for preprocessor
    --output=<o>        Specify the filename of the output file [default: depends.mak]
    --build=<d>         Directory where object files will live

    --find-source       Find the source files automatically [default: False]
    --extensions=<e>    String of space separated extensions to find, e.g., ".f90 .F90"
    --add-files=<f>     String of space separated files to include after directory search
"""
from __future__ import print_function
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from fortrandep import FortranProject

def parse_input(entry):
    """parse the input string of space/comma separated strings"""
    if (entry is None or entry.strip() == ""):
        return None

    if ("," in entry):
        fields = entry.split(",")
        fields = [f.strip() for f in fields] # remove leading/trailing space for each entry
        return fields

    # real simple (and probably dumb) : assume valid entries have no space, except separator
    return entry.split()

def main(objects, preprocess, exclude, ignore, macros, search_paths, output, build,
         find_source, extensions, add_files):

    # parse incoming entries: exclude, ignore, macros, search_paths
    search_paths = parse_input(search_paths)
    exclude      = parse_input(exclude)
    ignore       = parse_input(ignore)
    macros       = parse_input(macros)
    extensions   = parse_input(extensions)
    add_files    = parse_input(add_files)

    kwargs = dict(exclude_files=exclude, ignore_modules=ignore,
                  macros=macros, pp_search_path=search_paths,
                  use_preprocessor=preprocess, verbose=False)

    # parse files for dependencies
    if (not find_source):
        project = FortranProject(files=objects, **kwargs)

    else:
        project = FortranProject(search_dirs=objects, extensions=extensions,
                                 add_files=add_files, **kwargs)

    # write project dependencies
    project.write(output, overwrite=True, build=build, skip_programs=True)

if __name__ == "__main__":
    from docopt import docopt
    args = docopt(__doc__)

    objects = args['<objects>']

    preprocess   = args['--preprocess']
    exclude      = args['--exclude']
    ignore       = args['--ignore-mods']
    macros       = args['--macros']
    search_paths = args['--search-paths']
    output       = args['--output']
    build        = args['--build']
    find_source  = args['--find-source']
    extensions   = args['--extensions']
    add_files    = args['--add-files']

    main(objects, preprocess, exclude, ignore, macros, search_paths, output, build,
         find_source, extensions, add_files)
