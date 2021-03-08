"""
Basic preprocessor tools for Fortran files
"""
from __future__ import print_function
import os
import sys
from collections import OrderedDict
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
    def __init__(self, files=None, exclude_files=None,
                 ignore_modules=None,
                 search_dirs=None, extensions=None,
                 exec_names=None,
                 macros=None, pp_search_path=None, use_preprocessor=True,
                 name=None, verbose=False):
        """
        Args
        ----
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
        exec_names : dict
            Give a mapping of program name to corresponding executable name
        macros : list
            Collection of macro definitions
        pp_search_paths : list
            List of preprocessor search paths to look for included files
        use_preprocessor : bool
            Run the reprocessor on the files
        name : str
            Name of the Fortran project, defaults to current working directory
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

        if (exec_names is None):
            self.exec_names = {k:"x"+k for k,v in self.programs.items()}
        else:
            if (len(exec_names.keys()) != len(self.programs.keys())):
                print("\nERROR: number of executable names differs from found programs")
                print("\nPrograms found = {}".format(len(self.programs.keys())))
                for k in self.programs.keys():
                    print("\t{}".format(k))
                print("\nExecutable names found = {}".format(len(exec_names.keys())))
                for k in exec_names.keys():
                    print("\t{}".format(k))
                raise ValueError
            self.exec_names = exec_names

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

        # sort in a sensible way: based on number of USEd modules
        sdepends = OrderedDict()
        for key in sorted(depends, key=lambda name : len(depends[name])):
            sdepends[key] = depends[key]

        if (verbose):
            for m in sdepends.keys():
                print("Module {} depends on:".format(m))
                for dep in sdepends[m]:
                    print("\t{}".format(dep))

        return sdepends

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

        # sort in a sensible way: based on number of USEd modules
        sdepends = OrderedDict()
        for key in sorted(depends, key=lambda fname : len(depends[fname])):
            sdepends[key] = depends[key]

        if (verbose):
            for f in sdepends.keys():
                print("File {} depends on:".format(f))
                for dep in sdepends[f]:
                    print("\t{}".format(dep.filename))

        return sdepends

    def _format_dependencies(self, target, target_ext, dep_list, build=None, program=False):
        """
        Write out the makefile line "target : dependencies"

        As an example, if the following items are passed:
                target = "src/variables.f90"
                target_ext = ".o"
                dep_list = ["src/data_types.f90", "grids.f90"]

            using build = None and program = False will produce:
                src/variables.o : src/data_types.o grids.o src/variables.f90

            using build = "odir" and program = False will produce:
                odir/variables.o : odir/data_types.o odir/grids.o src/variables.f90

            when program=True, target now specifies the executable name, target="xvars":
                using build = None will produce:
                    xvars : src/data_types.o grids.o src/variables.o
                using build = "odir" will produce:
                    xvars : odir/data_types.o odir/grids.o odir/variables.o

        Args
        ----
        target : str
            The main target for this rule
        target_ext : str
            The extension of the target including the ".", usually ".o"
        dep_list : list
            The list of file dependencies
        build : str, optional
            The object files are located in this directory
        program : bool, optional
            This rule is for a "program" not a "module"

        Returns
        -------
        listing : str
            The formatted makefile rule, ready to write to the file
        """
        if (not program):
            name = os.path.splitext(target)[0] + target_ext # full path, change ext
            if (build is not None):
                name = os.path.join(build, os.path.split(name)[1]) # change path
        else:
            name = target # executable name will be unaltered

        # remove duplicate depenencies, e.g., could use two modules defined in same file
        udep_list = []
        for x in dep_list:
            if (x not in udep_list):
                udep_list.append(x)

        if (build is not None):
            # modify the path where dependencies live
            udep_list = [os.path.join(build, os.path.split(x)[1]) for x in udep_list]

        # make each dependency an object file extension
        dep_list = [os.path.splitext(i)[0] + target_ext for i in udep_list]

        # build rule for target using dependency list
        listing = "{} : ".format(name) + " ".join(dep_list)
        if (program):
            listing += "\n"
        else:
            listing += " {}\n".format(target) # original path/ext only included for modules

        return listing

    def write(self, output, overwrite=False, build=None, skip_programs=False):
        """
        Write dependencies to file

        Args
        ----
        output : str
            Name of output file
        overwrite : bool
            Overwrite existing dependency file
        build : str
            Directory where the object files are located
        skip_programs : bool
            Do not process the program rules, only dependencies of modules
        """

        if (os.path.isfile(output) and (not overwrite)): # file exists and overwrite=False
            err = "ERROR: file = {} already exists and overwrite=False, exiting."
            print(err.format(output))
            self.success = False
            return

        with open(output, 'w') as mf:
            mf.write(HEADER)

            # loop over all files and extract the files on which it depends.
            # the dependency list will not include the current file: that is added
            # in the _format_dependencies routine
            for f in self.depends_by_file.keys():
                dep_list = [dep.filename for dep in self.depends_by_file[f]]
                listing = self._format_dependencies(f, ".o", dep_list, build=build)
                mf.write(listing)

            if (not skip_programs):
                # loop over all programs and extract all files on which it depends.
                # here we manually include the current file, because the executable
                # name is provided instead of the filename
                for program in self.programs.keys(): # write out dependencies for programs
                    dep_list = self.get_all_used_files(program)

                    # manually include current file last
                    dep_list.append(self.programs[program].source_file.filename)

                    exec_name = self.exec_names[program] # extract executable name

                    listing = self._format_dependencies(exec_name, ".o", dep_list,
                                                        program=True, build=build)
                    mf.write(listing)

    def get_all_used_files(self, module_name):
        """
        Find complete set of files that a module requires, either directly or indirectly

        Does not include the file that defines this module, so maybe function name is
        wrong. The file that owns this module is included when the dependency list
        is written to the makefile dependency file.

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
        #module_filename = self.modules[module_name].source_file.filename

        #x = list(set(used_files + [module_filename]))
        x = list(set(used_files))

        return x

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
        x = self._get_all_used_modules(module_name, state=[])

        x = list(set(x))

        return x

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

