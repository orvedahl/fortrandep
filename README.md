# Fortran Dependencies Made Easy

`FortranDep` is a Python tool to help with building Fortran projects. Writing
the source code can be challenging enough, the build process should be as streamlined as
possible. The utilities in `FortranDep` try to centralize some of the operations that are
common to all Fortran projects. The user can write a small and very simple makefile
contained in their project, using the included templates, thus leaving more time for
actual development of the Fortran software.

There are two main tools:

* Core Makefile
* Preprocessor

with many supporting scripts to help with the build process that are used in the background.

The original idea is based on the [fort_depend](https://github.com/ZedThree/fort_depend.py)
project, although here we use a custom preprocessor that relies on pure Python.

## Makefiles
The core makefile magic includes a script to automatically determine the depenencies
of the various files. These dependencies are written to a file that is included into
the core makefile. This is often the most annoying part of writing a makefile from
scratch, especially when your software development changes the the dependencies quite often.

An important limitation of this project is that all files are assumed to hold either
a module or a program. Files that contain only a subroutine definition are not currently
handled correctly. This usually is not too much of a restriction, as it is best practice to
define subroutines within modules anyway.

The core makefile lives in this project and is common to most Fortran projects. The makefile
that a user would actually use in their project will include the core makefile and therefore
the user's makefile can be quite short. The simplest possible makefile a user might use could
be as simple as:
```
# space-separated list of directories that hold the source files
src_dirs := . src

# choose the Fortran compiler: intel, gcc, pgi
f90_compiler := gcc

# define the top Makefile directory of the FortranDep project (used throughout the core makefile)
MAKEFILE_HOME_DIR := /path/to/FortranDep/Makefiles

# include the core makefile
include $(MAKEFILE_HOME_DIR)/GMain.mak
```
A stencil for such a minimal makefile is provided in the `Makefiles` directory named
`GNUmakefile.stencil.minimal`. All possible variables that the user can change and their
description are provided in the more extensive `GNUmakefile.stencil`. Some of the more
important options are described below.

Also included is a stencil for a standalone makefile that does not rely on the `FortranDep`
machinery, named `GNUmakefile.stencil.standalone`. This can be used for smaller projects
or systems that do not support python scripts. It is meant to be a fully self-contained
makefile that shares some nice features of the full setup. Nothing is done automatically,
i.e., no autogenerating the list of source files, no automatic dependency checker. The
`GNUmakefile.stencil.standalone` serves more as a template for a typical makefile, with
some sophisticated features.

#### Specifying Source Files
There are two ways to choose what source files will be included in the build. The default method
will automatically find and process the source files based on the specified source directories.
All files with the `*.f90` and `*.F90` suffix will be included. This can lead to processing
far more files than are actually used. Once way to avoid this is to ignore certain files
using the `ignore_files` variable. This is a space-separate list of relative filenames to
ignore and not process.

The second method to choose the source files is to include a file called `GPackage.mak` in
every source directory. This file defines the source files that will be added to the project
and ultimately processed, allowing for a much finer control over what files are included.
The format of the `GPackage.mak` file should follow:
```
f90sources += filename1.f90
f90sources += filename2.F90
...

sf90sources += filesname3.F90
...
```
where there is a single entry per line and the path to the file is not required. Entries that
use the `sf90sources` variable will not go through the dependency checker, but will be
included. Only files found in the `f90sources` and `sf90sources` variables will be included
in the project.

#### Skipping Modules
Sometimes a system module is "used", such as OpenMP or MPI. The dependency checker will try
to find a file that contains a definition of such modules unless you tell it not to look.
This is where the `skip_modules` variable comes in handy. It is a space-separated list of
modules that should be ignored by the dependency checker.

#### Compiler Flags
There are six important variables that control the compiler flags:

* `f90_compiler` - choose a particular compiler: `intel`, `gcc`, or `pgi`
* `debug` - turn on debugging flags
* `f90_flags` - explicitly set the flags to use for compiling and linking
* `xtr_f90_flags` - flags that will always be added and never modified
* `include_flags` - flags related to including directories, e.g., `-I<some dir>`
* `library_flags` - flags related to libraries, e.g., `-L<some dir> -llib`

If the various flag variables are not set, suitable defaults are chosen based on the
chosen compiler.

##### Preprocessor
There are two variables related to the python preprocessor used by the dependency checker.
Adding search paths
for where to find included files is done through the `pp_search_paths` variable. Macros
can be defined with the `pp_macros` variable. These variables control the python preprocessor
used for determining the dependencies, not the C preprocessor invoked by the compiler. As
a result, defining macros must appear in two places:
```
# set macros for python dependency checker
pp_macros := INTEL_COMPILER=1 OUTPUT_DIR=/home/user

# set same macros for actual C preprocessor in the form of compiler flags
xtr_f90_flags += -DINTEL_COMPILER=1 -DOUTPUT_DIR=/home/user
```
The best practice is to use an auxilary variable to define the macros and be sure
the auxilary variable is applied to both the dependency checker as well as the compiler:
```
# user-defined macros
defined_macros := INTEL_COMPILER=1 OUTPUT_DIR=/home/user

# tell python the macro definitions
pp_macros := $(defined_macros)

# tell C preprocessor the macro definitions using "-Dvariable=value" compiler flags
xtr_f90_flags += $(addprefix -D, $(defined_macros))
```

#### Automatic Input Parameters
When choosing `build_probin := t`, a module that handles namelist values is generated.
The module handles reading the namelist as well as parsing the command line in order
to override any values specified in the namelist. The module name is set to be
`input_params` and the name of the namelist can be set using the `namelist_name`
variable in the makefile. The template for the final module can be found in
`/path/to/FortranDep/Makefiles/_templates/input_params_template`.

The main advantage to using this module is how new namelist variables are declared.
In the build directory of your project, include a file named `_params` with the
following format:
```
# variable name     type        default value
tstop               real        1.0d0

max_iter            integer     500

update              logical     .true.

output              character   "output.txt"
```
Comments can be included by starting the line with `#`. The first column provides the
variable name, the second column provides the variable type, and the last column
provides the default value. To add a new namelist variable, simply add a new
entry to the `_params` file and recompile. The newly added variable will be
available in the namelist as well as from the command line. A stencil for the
`_params` file can be found in `/path/to/FortranDep/Makefiles/_params.stencil`.

When compiling the project using this module, the command line interface becomes:
```
./executable.exe <namelist_file> --tstop 5.0d0 --max_iter 100 --update F --output output_1.txt

or

./executable.exe --tstop 5.0d0 --max_iter 100 --update F --output output_1.txt <namelist_file>
```
The namelist file must be either the first or the last argument. All other parameters are
set using the typical two dashes syntax with no equals sign.

#### Build Information
When choosing `build_info := t`, a module is generated that contains various information
concerning the build, including date, directory, machine name, compiler, compiler version,
compiler flags, linking flags, and the git hash of the build directory. This information
can then be used from within Fortran and included in various output formats.

#### Scipt to Generate Dependencies
Within the `/path/to/FortranDep/bin/` directory, the main script for generating the
dependency file is named `generate_dependencies.py`. This script is automatically called
within the larger makefile machinery. It is quite flexible with many options; use the
`--help` flag to see the details, or search the `/path/to/FortranDep/Makefiles/GMain.mak`
file for the string `dep_script` to see how it is used within a makefile.

## Preprocessor

The preprocessor is written in pure Python and does not require any third-party modules. As
a result, it does not support all possible preprocessor directives and their complexities.
Supported directives include:

#### Include Statements
Including code from other files is supported in the form
```
#include 'filename'
```
Nested `#include`s are not supported, i.e., an included file cannot have another `#include`
statement. All supported if-else-endif statements can appear in the included file. Also
supported are any `#define` statements, but there are some restrictions.

#### Define Statments
Defining macros using the `#define <name> <value>` form is supported. Only simple
"substitution" type macros are supported. Macros such as function definitions are not yet
supported. Conditional definitions are fully supported, for example:
```
#ifndef VARIABLE
  #define VARIABLE
#endif

#ifdef VARIABLE
  ...
#endif
```

#### If Statements
Standard `#ifdef - #else - #endif` statements as well as the `#ifndef` variation are
supported. More complex `#elif` statements are not supported. The if statements can be
nested, for example:
```
#ifdef INTEL_COMPILER
  use intel_version
#else
  #ifdef GNU_COMPILER
    use gnu_version
  #else
    use generic_version
  #endif
#endif
```

#### Important Notes
The directives are processed in a particular order which has important implications for
understanding and fixing bugs. The order-of-operations is:

* process all `#include` statements by simply copying the contents of the included file.
* process all `#define` statements that do not occur inside an if block.
* process all `#ifdef` and `#ifndef` statements, including nested if statements. After
   evaluation of a single if block, any `#define` directives contained in the surviving
   code will be parsed, allowing for conditional definitions.

As a result of this ordering, included files can only use `#ifdef`, `#ifndef`, and `#define`
directives. The only supported directives that may appear inside an if statement are:
other if blocks, `#include` directives, and `#define` directives.

#### Example Usage
To use the preprocessor, make sure the path to the `fortrandep` directory is included in
your `PYTHONPATH`. Then simply import the preprocessor as:
```
from preprocessor import FortranPreprocessor
```
To build the preprocessor:
```
fpp = FortranPreprocessor()
```
You can also include the optional `search_paths` option:
```
paths = ["..", "~/Include", "$PROJECTS/include"]   # list of relative or absolute paths

fpp = FortranPreprocessor(search_paths=my_paths)
```
This tells the preprocessor where to search for files that are included with the `#include`
directive. The current directory, `./` is automatically included. Paths can also be
included after the preprocessor has already been constructed using the `add_paths`
method:
```
fpp.add_paths("/some/new/path")   # add a single path

include_paths = ["..", "include", "~/bin"]   # list of multiple paths to add
fpp.add_paths(include_paths)
```

Predefined macros can also be included when building the preprocessor by passing in a
dictionary:
```
macros = {"VAR1" : value_1, "VAR2" : value_2}  # dictionary of macros

fpp = FortranPreprocessor(macros=macros)
```
An alternative method is to specify macros using a list of particularly formatted strings:
```
macros = ["VAR1=value_1", "VAR2=value_2", "VAR3"]  # list of "name=value" entries, no spaces

fpp = FortranPreprocessor(macros=macros)
```
In the case of using a list, variables with no "=" sign will be defined with a value of 1.
Macros can be added after the preprocessor has been built using the `define` method:
```
fpp.define("name=value")
```

To preprocess the contents of a file, first read the contents into a list, then call
the `parse` method:
```
with open(filename, "r") as f:
    lines = f.readlines()

parsed_lines = fpp.parse(lines)
```
The returned `parsed_lines` will be a list where each entry is a line of source code.

#### Script to Preprocess Single Files
Within the `/path/to/FortranDep/bin` directory, there is a python script named
`preprocess_file.py`. This script can be used to preprocess a source file and write the
parsed lines to another file. There are options for specifying macros as well as the
search paths, use the `--help` flag to see the details.

## Available Test Suites
During the ongoing development of this project, multiple test cases were used to test
the accuracy. The `test/` directory contains a bunch of source tree variations and the
dependencies will be written to a file named `<test dir>/depends.mak`. This file
can be compared to the `<test dir>/solution.mak` to ensure proper accuracy. To run all
of the test cases and perform the accuracy check:
```
cd /path/to/FortranDep/tests

python run_tests.py
```
This will generate the `depends.mak` file for each test case and compare it against the
corresponding `solution.mak` file. Successful cases will print `Pass` on the screen and
unsuccessful cases will show `Fail`.

#### Add a New Case (only for developers)
To include a new test case:

* build a new directory under the `tests` directory and include any source files and
   included files
* write the `source_files.txt` file
* generate the `solution.mak` file
* add the new test to the `run_tests.py` Python script

The contents of the `source_files.txt` should be formatted as:
```
source : <rel path to source file 1>
source : <rel path to source file 2>
source : <rel path to source file 3>
...
exclude : <rel path of file 1 to exclude>
exclude : <rel path of file 2 to exclude>
...
ignore : <module 1 name to ignore>
ignore : <module 2 name to ignore>
...
macro : <name>=<value>
macro : <name>=<value>
...
```
where the `...` indicate repeat as needed. This file will be parsed by the Python script
to determine what files to include, which ones to ignore, what modules to skip, and any
macros to use. Changing the contents of this file will lead to a different expected
`solution.mak` result.

The easiest way to generate the `solution.mak` file is to wait until after the new test
has been added to the `run_tests.py` Python script. To add a new test to the script
add an entry to the `tests` dictionary. The key should be the name of the new test
directory. The values of the dictionary are another dictionary, with only two keys,
both optional. The first key is `build`, which describes the location where all of the
object files are expected to be found. The default value is to search for the object
files in the same directory as the appropriate source file. The second key is `note`,
which is a list of strings that help define the test case; what kind of source directories,
was `build` provided, are any modules ignored, what kind of preprocessor capabilities 
are being used, etc.

Running the `run_tests.py` script will parse the source tree of each test directory and
write the `depends.mak` file. To generate the `solution.mak` file, simply copy it from
the `depends.mak` file:
```
cd /path/to/new/test

cp depends.mak solution.mak
```
It is **very important** that you inspect the `solution.mak` file for accuracy, as this
will be used to test the accuracy of future versions of the `FortranDep` project.

An alternative method, is to write the `solution.mak` file from scratch using the existing
files as a template. Any line that starts with `#` will not be processed and all blank
lines are skipped as well. The syntax is that of a standard makefile:
```
/path/to/target : /path/to/dependency
```
with a single target-dependency pair per line; multiple dependencies cannot occur on the
same line.
Usually the `target` will be an object file contained in a directory common to all objects.
The `dependency` will include the Fortran source file as well as any objects on which
it depends. This alternative method should be considered the "best practices" method.
