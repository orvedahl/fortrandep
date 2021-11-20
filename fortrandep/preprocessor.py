"""
Basic preprocessor tools for Fortran files
"""
from __future__ import print_function
from collections import OrderedDict
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
    def __init__(self, search_paths=["."], macros=None):
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
                for k,v in macros.items():
                    self.define("{}={}".format(k,v))
            elif (isinstance(macros, list)): # assume list
                for m in macros:
                    self.define(m)
            else:
                raise ValueError("macros should be dictionary or list")

        self.search_paths = [] # collection of search paths
        if (search_paths is not None):
            self.add_paths(search_paths)

    def define(self, definition):
        """
        Initialize macro definitions

        definition : str
            A definition should take the form "name=value" or just "name" for boolean values
        """
        if ("=" in definition):
            temp = definition.split("=")
            name = temp[0].strip()
            value = temp[1].strip()
        else:
            name = definition.strip()
            value = 1
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
        p = os.path.expanduser(path) # expand "~" into HOME
        p = os.path.expandvars(p)    # expand environment variables
        self.search_paths.append(os.path.abspath(p))

        # ensure there are no duplicates
        self.search_paths = list(set(self.search_paths))

    def parse(self, text):
        """
        Replace preprocessor directives with their definitions. Supported directives:

            + #include "filename" : included files are simply copied over and not processed,
                 with the exception of any if blocks
            + #ifdef VARIABLE : only if-endif or if-else-endif blocks, no elif statements
            + #ifndef VARIABLE : only if-endif or if-else-endif blocks, no elif statements

        In the case of if blocks, the "correct" code is included, the "invalid" code
        is simply ignored and not retained. For include directives, the included file
        contents are simply copied over, it is not processed for more directives (except if-endif).

        Args
        ----
        text : list
            Text of the Fortran file to parse; each entry in the list is a line in the file

        Returns
        -------
        contents : list
            The preprocessed file contents; each entry in the list is a line
        """
        # parse for directives
        contents = self._parse_include_directives(text)
        contents = self._parse_define_directives(contents)
        contents = self._parse_if_directives(contents)

        # reverse sort of macros by length of their name
        sorted_macros = sorted(self.macros, key=lambda name : len(name))[::-1]

        # change macros that appear in the source code, outside of directives
        for i in range(len(contents)):
            for name in sorted_macros: # replace macros with the longest name first
                if (name in contents[i]):
                    contents[i] = contents[i].replace(name, self.macros[name])

        return contents

    def _parse_define_directives(self, text):
        """
        Parse Fortran file for define directives

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
            if (line.lstrip().startswith("#define")):
                ind = line.find("define") # extract the macro name and value
                entry = Line[ind+len("define"):].strip()
                values = entry.split(maxsplit=1)
                name = values[0]
                if (len(values) == 1):
                    value = 1
                else:
                    value = values[1]

                self.define("{}={}".format(name,value))
            else:
                contents.append(Line)
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
        indices = {"ifs":[], "endif":[]}

        # find the start/end indices of each if block
        for i,Line in enumerate(text):
            line = Line.lower()
            if (line.lstrip().startswith("#")):

                if (("ifdef" in line) or ("ifndef" in line) or ("#if" in line)):
                    indices["ifs"].append(i)

                if ("endif" in line):
                    indices["endif"].append(i)

        if (len(indices["ifs"]) != len(indices["endif"])):
            e = "ERROR: mismatch between if and endif statements, {} ifs and {} endifs"
            raise SyntaxError(e.format(len(indices["ifs"]), len(indices["endif"])))

        # extract if/endif index lists into collection of paired indices
        # for example:
        #     ...
        #     #ifdef 1       line 17 (rather arbitrary line numbers...)
        #        ...
        #        #ifdef 2    line 23
        #           ...
        #        #endif 2    line 27
        #        ...
        #        #ifdef 3    line 35
        #           ...
        #        #endif 3    line 40
        #        ...
        #     #endif 1       line 50
        #     ...
        # produces: indices["ifs"] = [17, 23, 35] & indices["endif"] = [27, 40, 50]
        # iterate over ifdef indices in reverse, i.e., start with line 35. The
        # corresponding endif index will be the first endif index that is larger
        # than 35, i.e., 40. Now remove 40 from the list. The second-to-last ifdef
        # index, 23, will have corresponding endif index that is the first endif index
        # larger than 23 of the remaining endif indices, which is 27. Remove 27 from the
        # list, which only leaves endifs = [50]. The last ifdef index, 17, will be the
        # first index that is larger than 17 of those that remain, i.e., 50. So the
        # proper ifdef/endif pairs would be: [(35,40), (23,27), (17,50)]
        if_index_pairs = []
        for i in indices["ifs"][::-1]:
            start_if = i

            # find all endif indices larger than start, and sort them
            end_ifs = [x for x in indices["endif"] if x > start_if]
            end_ifs.sort()

            # extract the first index that is larger than start and remove it
            end_if = end_ifs[0]
            indices["endif"].remove(end_if)

            if_index_pairs.append([start_if, end_if]) # shape (Nifs, 2)

        parsed_text = text.copy() # avoid changing the input by using a copy, not a reference

        # process the ifdef/ifndef directives
        Nifs = len(if_index_pairs)
        for i in range(Nifs):

            start = if_index_pairs[i][0] # index to #if...
            end = if_index_pairs[i][1]   # index to #endif

            if_text = parsed_text[start:end+1] # include the #endif line

            use_code, Nremoved = self._parse_single_if(if_text)

            # swap out the if statement text for the correct code
            parsed_text = parsed_text[:start] + use_code + parsed_text[end+1:]

            # code length has changed so update the remaining if indices
            for j in range(i+1,Nifs):
                s = if_index_pairs[j][0]
                e = if_index_pairs[j][1]
                if (s > end):
                    if_index_pairs[j][0] = s - Nremoved
                if (e > end):
                    if_index_pairs[j][1] = e - Nremoved

        return parsed_text

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
        and
            #if defined(VARIABLE)
                code_4
            #endif
        In these examples, if VARIABLE is defined, then code_1, code_3, and code_4 will be returned.
        If VARIABLE is not defined, then only code_2 will be returned, other code_? would be ignored.

        Args
        ----
        text : list
            Text of the if block to parse, starting with "#if..." and concluding with "#endif"

        Returns
        -------
        contents : list
            The valid code contents where unused code has been removed
        Nremoved: int
            The number of lines that were ignored from the input list.
        """
        Ninput = len(text)

        if (Ninput < 1): # input is empty, so return empty
            return [], 0

        name = None
        if_type = None

        first_block = []
        second_block = []
        for Line in text:
            line = Line.lower()
            if (line.lstrip().startswith("#if")):
                first = True
                if ("ifndef" in line):
                    if_type = 'ndef'
                    ind = line.find("ifndef") # extract the macro variable name
                    name = Line[ind+len("ifndef"):].strip()
                elif ("ifdef" in line):
                    if_type = 'def'
                    ind = line.find("ifdef") # extract the macro variable name
                    name = Line[ind+len("ifdef"):].strip()

                continue

            if (line.lstrip().startswith("#") and "else" in line):
                first = False
                continue

            if (not line.lstrip().startswith("#")): # skip all other directives...very basic
                if (first):
                    first_block.append(Line)
                else:
                    second_block.append(Line)

        # determine if the macro is defined
        is_defined = name in self.macros.keys()

        # select the proper block of code
        if (((if_type == "def") and is_defined) or ((if_type == "ndef") and (not is_defined))):
            use_first = True
        else:
            use_first = False

        if (use_first):
            return first_block, Ninput - len(first_block)
        else:
            return second_block, Ninput - len(second_block)

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
                if (name.startswith("'") or name.startswith('"')): # remove quotes
                    name = name[1:-1]

                # find the filename in the search paths
                filenames = [os.path.join(d, name) for d in self.search_paths]
                exists = [os.path.isfile(f) for f in filenames]

                if (not any(exists)):
                    e = "ERROR: path does not contain #include file = {}".format(name)
                    raise ValueError(e)

                # find first instance of included file that is in the path
                filename = filenames[exists.index(True)]
                with open(filename) as mf:
                     include_contents = mf.read().splitlines()

                # simple dump of include file into the current file
                contents.extend(include_contents)

            else:
                contents.append(Line) # everything else

        return contents

