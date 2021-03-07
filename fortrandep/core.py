"""
Main classes that define files and modules
"""
from __future__ import print_function
import re
import os
from .preprocessor import FortranPreprocessor

# catch the case:
#     "module modname" or "program modname", but not "module procedure ..."
#         unit_type is either "module" or "program"
#         modname is the actual name of module/program
#     but avoid the "module procedure" cases
UNIT_REGEX = re.compile(r"^\s*(?P<unit_type>module(?!\s+procedure)|program)\s*(?P<modname>\w*)",
                        re.IGNORECASE)
# catch the case:
#     "end module modname" or "end program modname"
END_REGEX = re.compile(r"^\s*end\s*(?P<unit_type>module|program)\s*(?P<modname>\w*)?",
                       re.IGNORECASE)
# catch the case:
#     "use module_name" or "use, intrinsic :: module_name"
USE_REGEX = re.compile(r"""^\s*use
(\s*,\s*intrinsic\s*)?(\s*::\s*|\s+)  # Valid separators between "use" and module name
(?P<moduse>\w*)                       # The module name
\s*(, )?\s*(only)?\s*(:)?.*?$         # Stuff that might follow the name
""",
                       re.IGNORECASE | re.VERBOSE)
# catch the cases:
#     include "filename"
#     include 'filename'
#     this will also catch: include "filename', but that won't compile
#     filename can include an extension, e.g., "mpi.h" or "mpi" or "indices.F"
INC_REGEX = re.compile(r"""^\s*include\s+(\'|\")(?P<filename>\w+\.*\w+)?(\'|\")""",
                       re.IGNORECASE)

class FortranFile:
    """
    A generic Fortran file

    Attributes
    ----------
    filename : str
        The filename
    uses : list
        The modules that are USEd by this file
    modules : dict
        Modules defined in this file. The keys are the actual module name,
        the values are a FortranModule object
    """

    def __init__(self, filename=None, readfile=True,
                 macros=None, pp_search_path=None, use_preprocessor=True):
        """
        Args
        ----
        filename : str
            The filename
        readfile : bool
            Read and process the file
        macros : list
            Collection of macro definitions
        pp_search_path : list or str
            List of directories to add to preprocessor search path
        use_preprocessor : bool
            Preprocess the source file
        """
        if (filename is not None): # only error trap filenames that were provided
            if (not os.path.isfile(filename)):
                e = "File does not exist or is not a file: {}".format(filename)
                raise ValueError(e)
        else:
            # filename was specified as None, do not process it
            readfile = False

        self.filename = filename
        self.uses = []     # list of modules USEd by this file
        self.modules = {}  # dict of FortranModule objects

        if (readfile):
            with open(self.filename, 'r') as f: # read file contents into list
                contents = []
                has_directives = False
                for line in f:
                    if (line.lstrip().startswith("!") or (line.strip() == "")):
                        # skip comments/empty lines
                        continue

                    if (line.lstrip().startswith("#")): # track if any macros are used
                        has_directives = True

                    contents.append(line)

            # only preprocess if asked to & there are directives to parse
            if (has_directives and use_preprocessor):

                # build the preprocessor and parse the file
                preprocessor = FortranPreprocessor(macros=macros, search_paths=pp_search_path)

                contents = preprocessor.parse(contents) # run the preprocessor

            # parse file for modules and use statements
            self.modules = self.get_modules(contents)
            self.uses = self.get_uses()

    def __str__(self):
        return self.filename

    def __repr__(self):
        return "FortranFile('{}')".format(self.filename)

    def get_modules(self, contents):
        """
        Find all modules or programs that are defined in this file

        Args
        ----
        contents : list
            Contents of the source file

        Returns
        -------
        contains : dict
            A dictionary of (module/program name, FortranModule object) pairs
        """
        contains = {}
        found_units = [] # keep track of the regex module/program hits
        starts = []      # index of the "module/program ..." line
        ends = []        # index of the "end module/program ..." line

        # loop over all lines
        for num, line in enumerate(contents):
            unit = re.match(UNIT_REGEX, line)
            end = re.match(END_REGEX, line)
            if (unit):
                found_units.append(unit) # store the regex result
                starts.append(num)       # store the starting line index
            if (end):
                ends.append(num)         # store the ending line index

        if (found_units): # there are module/program definitions
            if ((len(found_units) != len(starts)) or (len(starts) != len(ends))):
                err = "Unmatched start/end of modules in {} ({} begins/{} ends)"
                raise ValueError(err.format(self.filename, len(starts), len(ends)))

            # loop over found matches
            for unit, start, end in zip(found_units, starts, ends):
                name = unit.group('modname').lower() # extract the actual module/program name

                # build/store the module/program object
                contains[name] = FortranModule(unit_type=unit.group('unit_type').lower(),
                                        name=name, source=contents[start:end+1],
                                        source_file=self) # source file is current object
        return contains

    def get_uses(self):
        """
        Find all instances of USE statements

        Returns
        -------
        uses : list
            A collection of module names
        """
        uses = []
        for mod in self.modules.keys():
            module = self.modules[mod]
            for m in module.uses:
                uses.append(m)

        list(set(uses)).sort() # sort results in place and make it unique

        return uses

class FortranModule:
    """
    A Fortran module or program

    Attributes
    ----------
    unit_type : str
        Specifies if this is a module or a program
    name : str
        Name of the module/program
    uses : list
        Collection of module names that this module/program USEs
    """

    def __init__(self, unit_type, name, source=None, source_file=None):
        """
        Args
        ----
        unit_type : str
            Specifies if this is a module or a program
        name : str
            Name of the module/program
        source : list, optional
            Source code that defines this module/program
        source_file : str, optional
            A FortranFile object describing the source file
        """
        self.unit_type = unit_type.strip().lower()
        self.name = name.strip().lower()

        self.uses = []
        self.contents = None

        self.source_file = source_file # try to grab the parent filename
        try:
            self.parent_file = self.source_file.filename
        except:
            self.parent_file = None

        if (source is not None):
            self.uses = self.get_uses(source)

    def __str__(self):
        return self.name

    def __repr__(self):
        out = "FortranModule({}, '{}', source_file='{}')"
        return out.format(self.unit_type, self.name, self.parent_file)

    def get_uses(self, contents):
        """
        Find all instances of USE statements

        Args
        ----
        contents : list
            Contents of the source code

        Returns
        -------
        uses : list
            A collection of module names
        """
        uses = []

        for line in contents:
            found = re.match(USE_REGEX, line)
            if (found):
                name = found.group('moduse').strip().lower() # store module name
                uses.append(name)

        # remove duplicates
        uniq_mods = list(set(uses))

        return uniq_mods

