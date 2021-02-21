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
    def __init__(self, search_paths=None):
        """
        Args
        ----
        search_paths : list, optional
            List of search paths to include
        """
        self.macros = {} # keep track of macro definitions

        if (search_paths is not None): # collection of search paths
            self.search_paths = []
        else:
            if (not isinstance(search_paths, list)):
                search_paths = [search_paths]
            self.search_paths = search_paths

    def define(self, definition):
        """
        Initialize macro definitions

        definition : str
            A definition should take the form "name value" or just "name" for boolean values
        """
        temp = definition.split()
        name = temp[0]
        if (len(temp) > 1):
            value = temp[1]
        else:
            value = True
        self.macros[name] = value

    def add_path(self, path):
        """
        Add a search path for included files

        path : str
            search path to include
        """
        self.search_paths.append(os.path.abspath(path))

    def parse(self, text):
        """
        Parse Fortran file and replace the preprocessor directives with their definition

        Args
        ----
        text : list
            Text of the file to parse; each entry in the list is a line in the file

        Returns
        -------
        contents : list
            The preprocessed file contents; each entry in the list is a line
        """
        return contents

