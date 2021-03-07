"""
Basic preprocessor tools for Fortran files
"""
from __future__ import print_function
import os
import sys
from .core import FortranFile, FortranModule

# default modules to ignore
default_ignored_modules = ['iso_c_binding', 'iso_fortran_env']

HEADER = "#\n# This file is generated automatically. DO NOT EDIT!\n#\n"

class FortranProject:
    """
    Read a set of Fortran source files and produce the dependencies between them. The
    dependencies can be written to a file that can be directly included into a Makefile.

    Attributes
    ----------
    name : str
        Name of the Fortran project, defaults to current working directory
    files : dict
        Collection of FortranFile objects for each source file that will be included
    success : bool
        The exit status of parsing the files
    """
    def __init__(self, name=None, files=None, exclude_files=None,
                 ignore_modules=None,
                 search_dirs=None, extensions=None,
                 macros=None, pp_search_path=None, use_preprocessor=True,
                 verbose=False):
        """
        Args
        ----
        name : str
            Name of the Fortran project, defaults to current working directory
        files : list
            List of source files to include
        exclude_files : list
            List of files to exclude
        ignore_modules : list
            List of module names to ignore, default includes iso_c_binding and iso_fortran_env
        search_dirs : list
            Collection of directories to search for source files. Only used if files=None.
        extensions : list
            List of file extensions to search for. Only used if files=None
        macros : list
            Collection of macro definitions
        pp_search_paths : list
            List of preprocessor search paths to look for included files
        use_preprocessor : bool
            Run the reprocessor on the files
        verbose : bool
            Print more messages
        """
        self.success = True

        if (name is None):
            self.name = os.path.basename(os.getcwd())
        else:
            self.name = name

        if (files is None):
            files = self.get_source(search_dirs, extensions)
        elif (not isinstance(files, list)):
            files = [os.path.relpath(files)]
        else:
            files = [os.path.relpath(f) for f in files]

        if (exclude_files is not None):
            if (not isinstance(exclude_files, list)):
                exclude_files = [os.path.relpath(exclude_files)]
            else:
                exclude_files = [os.path.relpath(f) for f in exclude_files]
        else:
            exclude_files = []

        # remove duplicates and excluded files
        files = list(set(files) - set(exclude_files))

        # build FortranFile objects
        self.files = {fname : FortranFile(filename=fname, readfile=True, macros=macros,
                                          pp_search_path=pp_search_path,
                                          use_preprocessor=use_preprocessor)
                      for fname in files}

        self.modules = self.get_modules() # collect all modules for the project

        # tease out the programs that were found
        self.programs = {k: v for k,v in self.modules.items() if v.unit_type == "program"}

        # remove ignored modules
        self.remove_ignored_modules(ignore_modules)

        # find dependencies
        self.depends_by_module = self.get_depends_by_module(verbose)
        self.depends_by_file = self.get_depends_by_file(verbose)

    def get_source(self, search_dirs, extensions):
        """
        Find source files

        Args
        ----
        search_dirs : list
            List of search directories
        extensions : list
            List of extensions to find

        Returns
        -------
        files : list
            List of files
        """
        if (extensions is None):
            extensions = [".f90", ".F90"]
        if (search_dirs is None):
            search_dirs = ["."]

        if (not isinstance(extensions, list)):
            extensions = [extensions]
        if (not isinstance(search_dirs, list)):
            search_dirs = [search_dirs]

        files = []
        for d in search_dirs: # seach given directories and find files with given extension
            tmp = os.listdir(d)
            for ext in extensions:
                files.extend([os.path.relpath(x) for x in tmp if x.endswith(ext)])

        return files

    def get_modules(self):
        """
        Find all modules in the project

        Returns
        -------
        modules : dict
            A collection of FortranModule objects
        """
        modules = {}
        for source_file in self.files.values(): # loop over FortranFile objects
            modules.update(source_file.modules) # add modules in this file to the project
        return modules

    def remove_ignored_modules(self, ignore_modules=None):
        """
        Remove modules from all dependencies

        Args
        ----
        ignore_modules : list
            Collection of module names to ignore
        """
        if (ignore_modules is None):
            ignore_modules = []
        elif (not isinstance(ignore_modules, list)):
            ignore_modules = [ignore_modules]

        # include the default modules that are ignored
        ignore_modules = list(set(ignore_modules + default_ignored_modules))

        # references to a particular module are in three places:
        #   1) list of all modules in the project
        #   2) other modules may 'use' the ignored module
        #   3) files may 'use' the ignored module
        for ignore_mod in ignore_modules:
            m = self.modules.pop(ignore_mod, None) # 1) remove from project modules

            for module in self.modules.values(): # 2) loop over all remaining modules
                n = len(module.uses)
                if (n > 0 and ignore_mod in module.uses):
                    module.uses.remove(ignore_mod)

            for source_file in self.files.values(): # 3) loop over all File objects
                n = len(source_file.uses)
                if (n > 0 and ignore_mod in source_file.uses):
                    source_file.uses.remove(ignore_mod)

    def get_depends_by_module(self, verbose):
        """
        Determine set of which modules each module directly depends on

        Args
        ----
        verbose : bool
            Print more information

        Returns
        -------
        depends : dict
            Collection of FortranModule objects that each module depends on
        """
        depends = {}
        for module in self.modules.values(): # loop over all modules in project
            graph = []
            for used_mod in module.uses: # loop over all USEd modules
                try:
                    graph.append(self.modules[used_mod])
                except KeyError:
                    #new_module = FortranModule(unit_type='module', name=used_mod)
                    #graph.append(new_module)
                    err = "ERROR: module \"{}\" not defined in any files, skipping"
                    print(err.format(used_mod))
                    self.success = False

            # sort dependencies based on source filename
            depends[module.name] = sorted(graph, key=lambda f: f.source_file.filename)

        if (verbose):
            keys = depends.keys()
            for m in keys: #sorted(depends.keys(), key=lambda f: depends[f].source_file.filename):
                print("Module {} depends on:".format(m))
                for dep in depends[m]:
                    print("\t{}".format(dep))

        return depends

    def get_depends_by_file(self, verbose):
        """
        Determine set of which files each file directly depends on

        Args
        ----
        verbose : bool
            Print more information

        Returns
        -------
        depends : dict
            Collection of FortranFile objects that each module depends on
        """
        depends = {}
        for source_file in self.files.values(): # loop over FortranFile objects
            graph = []
            for mod in source_file.uses: # loop over all USEd modules
                try:
                    mod_file = self.modules[mod].source_file
                    if (mod_file.filename.lower() == source_file.filename.lower()): continue
                    graph.append(mod_file)
                except KeyError:
                    err = "ERROR: module \"{}\" not defined in any files, skipping..."
                    print(err.format(mod))
                    self.success = False

            # sort dependencies based on source filename
            depends[source_file.filename] = sorted(graph, key=lambda f: f.filename)

        if (verbose):
            keys = depends.keys()
            for f in keys: #sorted(depends.keys(), key=lambda f: depends[f].filename):
                print("File {} depends on:".format(f))
                for dep in depends[f]:
                    print("\t{}".format(dep.filename))

        return depends

    def write_dependencies(self, output, overwrite=False, build=None):
        """
        Write dependencies to file

        Args
        ----
        output : str
            Name of output file
        overwrite : bool
            Overwrite existing dependency file
        build : str
            Directory to prepend to filenames
        """
        if (build is None):
            build = ''

        # helper function to format dependency line
        def _format_dependencies(target, target_ext, dep_list):
            # target_ext : the target extension usually ".o"
            # dep_list : list of dependencies for this target
            _, filename = os.path.split(target)
            target_name = os.path.splitext(filename)[0] + target_ext
            listing = "\n{} : ".format(os.path.join(build, target_name))
            for dep in dep_list:
                _, depfilename = os.path.split(dep)
                depobjectname = os.path.splitext(depfilename)[0] + target_ext
                listing += " {}".format(os.path.join(build, depobjectname))
            listing += "\n"
            return listing

        if (os.path.isfile(output) and (not overwrite)): # file exists and overwrite=False
            err = "ERROR: file = {} already exists and overwrite=False, exiting."
            print(err.format(output))
            self.success = False
            return

        with open(output, 'w') as mf:
            mf.write(HEADER)

            for program in self.programs.keys(): # write out dependencies for programs
                program_deps = self.get_all_used_files(program)
                listing = _format_dependencies(program, "", program_deps)
                mf.write(listing)

            keys = self.depends_by_file.keys()
            for f in keys: #sorted(self.depends_by_file.keys(), key=lambda f: f.filename):
                dep_list = [dep.filename for dep in self.depends_by_file[f]]
                listing = _format_dependencies(f, ".o", dep_list)
                mf.write(listing)

    def get_all_used_files(self, module_name):
        """
        Find complete set of files that a module requires, either directly or indirectly

        Args
        ----
        module_name : str
            The module/program name

        Returns
        -------
        files : list
            List of filenames
        """
        used_modules = self._get_all_used_modules(module_name, state=[])

        # grab list of filenames
        used_files = [self.modules[module].source_file.filename for module in used_modules]

        # add the modules own file
        module_filename = self.modules[module_name].source_file.filename

        return sorted(list(set(used_files + [module_filename])))

    def get_all_used_modules(self, module_name):
        """
        Find complete set of modules that a module requires, either directly or indirectly

        Args
        ----
        module_name : str
            The module/program name

        Returns
        -------
        files : list
            List of module names
        """
        return self._get_all_used_modules(module_name, state=[])

    def _get_all_used_modules(self, module_name, state):
        """
        Find complete set of modules/files that a module requires, either directly or indirectly

        Args
        ----
        module_name : str
            The module/program name
        state : list
            A list of modules that have already been processed by this routine

        Returns
        -------
        state : list
            List of module names
        """
        for module in self.modules[module_name].uses:
            try:
                if (module in state): continue # ignore these modules, already processed
                state.append(module)
                if (len(self.modules[module].uses) != 0):
                    state.extend(self._get_all_used_modules(module, state)) # somewhat recursive
            except KeyError:
                print("ERROR: module {} not defined in any files, skipping...".format(module))
                self.success = False

        return sorted(list(set(state)))

