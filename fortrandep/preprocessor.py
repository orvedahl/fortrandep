"""
Basic preprocessor tools for Fortran files
"""
from __future__ import print_function
import os

class FortranPreprocessor:
    """
    Basic preprocessor for Fortran files

    Attributes
    ----------
    macros : dict
        The keys are the definition name, values are the definition value
    search_paths : list
        List of search paths to look for included files
    """
    def __init__(self, search_paths=None, macros=None):
        """
        Args
        ----
        search_paths : list, optional
            List of search paths to include
        macros : dict or list
            Collection of definitions. Dictionary key is name of the macro. List entries
            should be list of strings of the form "name=value" or "name"
        """
        self.macros = {} # keep track of macro definitions
        if (macros is not None):
            if (isinstance(macros, dict)):
                self.macros.update(macros)
            elif (isinstance(macros, list)): # assume list
                for m in macros:
                    self.define(m)
            else:
                raise ValueError("macros should be dictionary or list")

        self.search_paths = [] # collection of search paths
        if (search_paths not is None):
            self.add_paths(seach_paths)

    def define(self, definition):
        """
        Initialize macro definitions

        definition : str
            A definition should take the form "name=value" or just "name" for boolean values
        """
        if ("=" in definition):
            temp = definition.split("=")
            name = temp[0]
            value = temp[1]
        else:
            name = definition
            value = True
        self.macros[name] = value

    def add_paths(self, paths):
        """
        Add multiple search paths for included files

        path : list
            Collection of search paths to include
        """
        if (not isinstance(paths, list)):
            paths = [paths]
        for p in paths:
            self.add_path(p)

    def add_path(self, path):
        """
        Add a search path for included files

        path : str
            search path to include
        """
        self.search_paths.append(os.path.abspath(path))

    def parse(self, text):
        """
        Replace preprocessor directives with their definitions. Supported directives:

            + #ifdef VARIABLE : only if-endif or if-else-endif blocks, no elif statements
            + #ifndef VARIABLE : only if-endif or if-else-endif blocks, no elif statements
            + #include "filename" : included files are simply copied over and not processed

        In the case of if blocks, the "correct" code is included, the "invalid" code
        is simply ignored and not retained. For include directives, the included file
        contents are simply copied over, it is not processed for more directives.

        Args
        ----
        text : list
            Text of the Fortran file to parse; each entry in the list is a line in the file

        Returns
        -------
        contents : list
            The preprocessed file contents; each entry in the list is a line
        """
        contents = self._parse_if_directives(text)

        contents = self._parse_include_directives(contents)

        return contents

    def _parse_if_directives(self, text):
        """
        Parse Fortran file for if directives and choose proper code block

        Args
        ----
        text : list
            Text of the file to parse; each entry in the list is a line in the file

        Returns
        -------
        contents : list
            The preprocessed file contents; each entry in the list is a line
        """
        contents = []
        indices = {"ifdef_ifndef":[], "endif":[]}

        # find the start/end indices of each if block
        for i,Line in enumerate(text):
            line = Line.lower()
            if (line.lstrip().startswith("#")):

                if (("ifdef" in line) or ("ifndef" in line)):
                    indices["ifdef_ifndef"].append(i)

                if ("endif" in line):
                    indices["endif"].append(i)

        if (len(indices["ifdef_ifndef"]) != len(indices["endif"])):
            e = "ERROR: mismatch between if and endif statements, {} ifs and {} endifs"
            raise SyntaxError(e.format(len(indices["ifdef_ifndef"]), len(indices["endif"])))

        # process the ifdef/ifndef directives
        Nifs = len(indices["ifdef_ifndef"])
        s = 0
        for i in range(Nifs):

            start = indices["ifdef_ifndef"][i] # index to #ifdef & #ifndef
            end = indices["endif"][i]          # index to #endif

            use_code = self._parse_single_if(text[start:end+1]) # include text[end] line

            contents.extend(text[s:start]) # add code outside if blocks, exclude the text[start] line
            contents.extend(use_code)      # add proper code from the if block

            s = end+1 # update new starting point, which will be included

        # add last part of file that is outside the if block
        contents.extend(text[s:])

        return contents

    def _parse_single_if(self, text):
        """
        Parse single ifdef/ifndef block and return the valid code that should be used

        Only simple if blocks are supported, else-if statements are not.
        Examples include:
            #ifdef VARIABLE
                code_1
            #endif
        and
            #ifndef VARIABLE
                code_2
            #else
                code_3
            #endif
        In these examples, if VARIABLE is defined, then code_1 and code_3 will be returned.
        If VARIABLE is not defined, then only code_2 will be returned, code_1 would be ignored.

        Args
        ----
        text : list
            Text of the if block to parse

        Returns
        -------
        contents : list
            The valid code contents where unused code has been removed
        """
        first_block = []
        second_block = []
        for Line in text:
            line = Line.lower()
            if (line.lstrip().startswith("#") and ("ifdef" in line or "ifndef" in line)):
                first = True
                if ("ifndef" in line):
                    if_type = 'ndef'
                    ind = line.find("ifndef") # extract the macro variable name
                    name = Line[ind+len("ifndef"):].strip()
                else:
                    if_type = 'def'
                    ind = line.find("ifdef") # extract the macro variable name
                    name = Line[ind+len("ifdef"):].strip()
                continue
            if (line.lstrip().startswith("#") and "else" in line):
                first = False
                continue

            if (not line.lstrip.startswith("#")): # skip all other directives...very basic
                if (first):
                    first_block.append(Line)
                else:
                    second_block.append(Line)

        # determine if the macro is defined
        is_defined = name in self.macros.keys()

        # select the proper block of code
        if (((if_type == "def") and is_defined) or ((if_type == "ndef") and (not is_defined))):
            return first_block
        else
            return second_block

    def _parse_include_directives(self, text):
        """
        Parse include statements and fill in valid code that should be used

        Args
        ----
        text : list
            Text of the file to parse; each entry in the list is a line in the file

        Returns
        -------
        contents : list
            The preprocessed file contents; each entry in the list is a line
        """
        contents = []

        for i,Line in enumerate(text):
            line = Line.lower()
            if (line.lstrip().startswith("#") and "include" in line): # include directive
                ind = line.find("include")
                name = Line[ind+len("include"):].strip() # get the included filename
                if (name.startswith('"') or name.startswith('"')): # remove quotes
                    name = name[1:-1]

                # find the filename in the search paths
                filenames = [os.path.join(d, name) for d in self.search_paths]
                exists = [os.path.isfile(f) for f in filenames]

                if (not any(exists)):
                    raise ValueError("ERROR: path does not contain #include file = {}".format(name))

                # find first instance of included file that is in the path
                filename = filenames[exists.index(True)]
                with open(filename) as mf:
                     include_contents = mf.read().splitlines()

                # simple dump of include file into the current file
                contents.extend(include_contents)

            else:
                contents.append(Line) # everything else

        return contents

