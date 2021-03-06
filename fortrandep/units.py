"""
Main classes that define files and modules
"""
from __future__ import print_function
import re
import os

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

    def __init__(self, filename, macros=None, readfile=True, pp_search_path=None, use_preprocessor=True):
        """
        Args
        ----
        filename : str
            The filename
        macros : iterable
            Dictionary of preprocessor macros to be expanded
        readfile : bool
            Read and process the file
        pp_search_path : list or str
            List of directories to add to preprocessor search path
        use_preprocessor : bool
            Preprocess the source file
        """
        if (filename is not None): # only error trap non-None filenames
            if (not os.path.isfile(filename)):
                raise FileNotFoundError("File does not exist or is not a file: {}".format(filename))
        else:
            # filename was specified as None, do not process it
            readfile = False

        self.filename = filename
        self.uses = None     # will be a list of modules USEd by this file
        self.modules = None  # will be a dict of FortranModule objects

        if (readfile):
            with open(self.filename, 'r') as f: # read file contents into list
                contents = []
                need_preprocess = False
                for line in f:
                    if (line.lstrip().startswith("!") or (line.strip() == "")): # skip comments/empty lines
                        continue
                    if (line.lstrip().startswith("#")): # track if any macros are used
                        need_preprocess = True

                    contents.append(f.readline())

            if (need_preprocess and use_preprocessor):

                # build the preprocessor and parse the file
                preprocessor = FortranPreprocessor(macros=macros, search_paths=pp_search_path)

                contents = preprocessor.parse(contents)

            # parse file for modules and use statements
            self.modules = self.get_modules(contents)
            self.uses = self.get_uses()

    def __str__(self):
        return self.filename

    def __repr__(self):
        return "FortranFile('{}')".format(self.filename)

    def get_modules(self, contents, macros=None):
        """
        Find all modules or programs that are defined in this file

        Args
        ----
        contents : list
            Contents of the source file
        macros : dict
            Any defined macros

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
            if ((len(found_units) != len(starts)) or (len(starts) != len(ends))): # mismatch start/end
                err = "Unmatched start/end of modules in {} ({} begins/{} ends)"
                raise ValueError(err.format(self.filename, len(starts), len(ends)))

            # loop over found matches
            for unit, start, end in zip(found_units, starts, ends):
                name = unit.group('modname') # extract the actual module/program name

                # build/store the module/program object
                contains[name] = FortranModule(unit_type=unit.group('unit_type'),
                                               name=name,
                                               source_file=self, # source file is the current object
                                               text=(contents, start, end),
                                               macros=macros)
        return contains

    def get_uses(self):
        """
        Find all instances of USE statements

        Returns
        -------
        uses : list
            A collection of module names
        """
        if (self.modules is None):
            uses = []
        else:
            # get list of uses for each module and make it unique, then sort it
            uses = sorted(set([mod for module in self.modules.values() for mod in module.uses]))

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
    source_file : FortranFile
        The source file that holds the module/program, not needed unless printing information
    uses : list
        Collection of module names that this module/program USEs
    """

    def __init__(self, unit_type, name, source_file=None, text=None, macros=None):
        """
        Args
        ----
        unit_type : str
            Specifies if this is a module or a program
        name : str
            Name of the module/program
        source_file : str
            The source file that holds the module/program
        text : tuple
            Tuple containing (contents of source file, start index, end index). The entire
            module/program would be contained within contents[start:end+1]
        macros : dict
            Any defined macros
        """
        self.unit_type = unit_type.strip().lower()
        self.name = name.strip().lower()

        if (source_file is not None):
            self.source_file = source_file
            self._defined_at = text[1]
            self._end = text[2]

            # find the USEd statements in this module/program
            self.uses = self.get_uses(text[0], macros=macros)

        else:
            self.source_file = FortranFile(filename=None, readfile=False)

            self._defined_at = 0 # definition start/end was not given, default to all
            self._end = None

            # USEd statements will presumably be found later with an explicit call to get_uses
            # so for now, define the attribute with a placeholder value
            self.uses = None

    def __str__(self):
        return self.name

    def __repr__(self):
        return "FortranModule({}, '{}, '{}')".format(self.unit_type, self.name, self.source_file.filename)

    def get_uses(self, contents, macros=None):
        """
        Find all instances of USE statements

        Args
        ----
        contents : list
            Contents of the source file
        macros : dict
            Any defined macros

        Returns
        -------
        uses : list
            A collection of module names
        """
        uses = []

        # loop over module/program definition, but skip "end module/program ..." line
        for line in contents[self._defined_at:self._end]:
            found = re.match(USE_REGEX, line)
            if (found):
                uses.append(found.group('moduse').strip()) # store the module name that is USEd

        # remove duplicates
        uniq_mods = list(set(uses))

        if (macros is not None):
            for i, mod in enumerate(uniq_mods):
                for k, v in macros.items():
                    if (re.match(k, mod, re.IGNORECASE)): # if the definition is found in module name, replace it
                        uniq_mods[i] = mod.replace(k,v)

        return uniq_mods

