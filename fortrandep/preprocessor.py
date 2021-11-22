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
            + #define VAR VALUE : function definitions are not supported

        In the case of if blocks, the "correct" code is included, the "invalid" code
        is simply ignored and not retained. For include directives, the included file
        contents are simply copied over, it is not processed for more #include directives,
        but if blocks and define directives are parsed.

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

    def _parse_define_directives(self, text, return_count=False):
        """
        Parse Fortran file for define directives outside of any if statements

        Args
        ----
        text : list
            Text of the file to parse; each entry in the list is a line in the file
        return_count : bool, optional
            Return the number of macros that were defined

        Returns
        -------
        contents : list
            The preprocessed file contents; each entry in the list is a line
        count : int, optional
            The number of macros that were found, only returned if return_count=True
        """
        contents = []
        if_count = 0
        count = 0
        for i,Line in enumerate(text):
            line = Line.lower()
            if (line.lstrip().startswith("#if")):
                if_count += 1
            if (line.lstrip().startswith("#endif")):
                if_count -= 1

            # parse #define directives, only if they appear outside of an #if statement
            if (line.lstrip().startswith("#define") and (if_count < 1)):
                ind = line.find("define")
                entry = Line[ind+len("define"):].strip() # entry: name value
                values = entry.split(maxsplit=1)
                name = values[0].strip()
                if (len(values) == 1):
                    value = 1
                else:
                    value = values[1].strip()

                self.define("{}={}".format(name,value))
                count += 1
            else:
                contents.append(Line)

        if (return_count):
            return contents, count
        else:
            return contents

    def _parse_if_directives(self, text):
        """
        Parse Fortran file for #ifdef and #ifndef directives and choose proper code block.

        Only simple if blocks of the form if-else-endif are supported, the #elif directive
        is not supported. If statements may contain #include and #define directives.

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
        ifs = []
        idx_if = -1
        active_if = []
        Nif = 0
        Nendif = 0

        # find the start/end indices of each if block
        for i,Line in enumerate(text):
            line = Line.lower()
            if (line.lstrip().startswith("#")):

                if (("#ifdef" in line) or ("#ifndef" in line) or ("#if" in line)):
                    idx_if += 1              # list index that identifies this if block
                    active_if.append(idx_if) # track "active" if blocks
                    ifs.append([i])          # store line number as new entry
                    Nif += 1

                if ("#else" in line):
                    try:
                        idx = active_if[-1] # index of current if block
                    except:
                        e = "ERROR: parsing #else failed, possible missing #if?"
                        raise ValueError(e)
                    ifs[idx].append(i)  # store line number to existing entry

                if ("#endif" in line):
                    try:
                        idx = active_if[-1] # index of current if block
                    except:
                        e = "ERROR: parsing #endif failed, possible missing #if?"
                        raise ValueError(e)
                    ifs[idx].append(i)  # store line number to existing entry
                    del active_if[-1]   # mark if block as "parsed" by removing from active
                    Nendif += 1

        if (Nif != Nendif):
            e = "ERROR: unmatched #if-#endif statements, found {} ifs and {} endifs"
            raise SyntaxError(e.format(Nif, Nendif))

        parsed_text = text.copy() # avoid changing the input by using a copy, not a reference

        # process the if directives
        for i in range(Nif):

            if_idx = ifs[i] # process if blocks in order, going from top to bottom

            if (len(if_idx) < 2): continue # this block is never reached based on directives

            istart = if_idx[0]  # index to #if...
            iend   = if_idx[-1] # index to #endif

            # full text for this if block, including the #endif line
            if_text = parsed_text[istart:iend+1] # include the #endif line

            # convert the index of the #else directive to reference the extracted if block
            if (len(if_idx) == 3):
                ielse = if_idx[1] - istart
            else:
                ielse = None
            results = self._parse_single_if(if_text, ielse)

            use_code, Nremoved, index_threshold, used_first_block = results

            # swap out the if statement text for the correct code
            parsed_text = parsed_text[:istart] + use_code + parsed_text[iend+1:]

            # now update the remaining if block indices, as necessary, since the
            # number of lines of text has been modified

            # index_threshold = local index that divides if block into
            # "should be kept" and "should be ignored" sections, make it a global index
            index_threshold += istart

            # only adjust entries for if blocks that have not yet been processed
            for j in range(i+1,Nif):
                if (len(ifs[j]) < 1): continue # these have already been processed

                s = ifs[j][0] # start index to other, not yet processed, if blocks

                # this j-th block is either 1) inside the first i-th block, inside
                # the second i-th block, or completely after the i-th block.
                # determine what case the j-th block is and choose the necessary
                # adjustment for its indices

                # this j-th block is inside the first block
                case1 = used_first_block and (s < index_threshold)

                # this j-th block is inside the second block
                case2 = (not used_first_block) and (s > index_threshold) and (s < iend)

                # this j-th block is beyond the entire block
                case3 = s > iend

                Nadjust = 0 # default is to adjust nothing, should never happen though...

                # there were N lines removed, but one of those is the last #endif,
                # which occurs after these indices, so do not adjust for the last #endif
                # line, only the first #if line
                if (case1):
                    Nadjust = 1

                # there were N lines removed, but one of those is the last #endif,
                # which occurs after these indices, so do not adjust for the last #endif line
                if (case2):
                    Nadjust = Nremoved - 1

                # there were N lines removed, all of which occured before this block
                if (case3):
                    Nadjust = Nremoved

                # this block should be kept, but adjusted
                if (case1 or case2 or case3):
                    for k in range(len(ifs[j])): # adjust all indices of the j-th block
                        ifs[j][k] -= Nadjust

                else: # these blocks are no longer relevent, remove them
                    ifs[j].clear()

        return parsed_text

    def _parse_single_if(self, text, ielse):
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
        In these examples, either code_1 and code_3 will be returned, or code_2 will
        be returned; unused code is silently ignored.

        Args
        ----
        text : list
            Text of the if block to parse, starting with "#if" and concluding with "#endif"
        ielse : int or None
            Index into text of the "#else# statement, should be None if no else is present.

        Returns
        -------
        contents : list
            The valid code contents where unused code has been removed
        Nremoved: int
            The number of lines that were ignored from the input list.
        index_threshold : int
            Index into input text that separates it into the True block and the False block.
        used_first_block : bool
            A boolean value describing which block of the if-else-endif block that was used.
        """
        Ninput = len(text)

        if (Ninput < 1): # input is empty
            raise ValueError("ERROR: Cannot parse single-if, line is empty")

        name = None
        if_type = None
        if (ielse is None):
            index_threshold = Ninput-1
        else:
            index_threshold = ielse

        fLine = text[0]
        fline = text[0].lower()

        # check first line for if statement and parse it
        if ("ifndef" in fline):
            if_type = 'ndef'
            ind = fline.find("ifndef") # extract the macro variable name
            name = fLine[ind+len("ifndef"):].strip()
        elif ("ifdef" in fline):
            if_type = 'def'
            ind = fline.find("ifdef") # extract the macro variable name
            name = fLine[ind+len("ifdef"):].strip()
        else:
            e = "ERROR: Cannot parse single-if, it has no #if statement"
            e += "\n\tfirst line = {}".format(fline)
            raise ValueError(e)

        if (not text[-1].lower().lstrip().startswith("#endif")):
            e = "ERROR: Cannot parse single-if, it has no #endif statement"
            e += "\n\tlast line = {}".format(text[-1])
            raise ValueError(e)

        # determine if the macro is defined
        is_defined = name in self.macros.keys()

        # select the proper block of code
        first_def_block  = ((if_type == "def") and is_defined)
        first_ndef_block = ((if_type == "ndef") and (not is_defined))
        if (first_def_block or first_ndef_block):
            block = text[1:index_threshold]
            used_first_block = True
        else:
            block = text[index_threshold+1:-1]
            used_first_block = False

        Nremoved = Ninput - len(block)

        # now find and parse any #define directives that do not appear in any other if blocks
        contents, count = self._parse_define_directives(block, return_count=True)
        Nremoved += count

        return contents, Nremoved, index_threshold, used_first_block

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

