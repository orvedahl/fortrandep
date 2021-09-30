#
# makefile rules for a custom compiler
#

# get version
ifndef compiler_exe
  $(error "Must point to compiler executable: set compiler_exe variable")
else
  f90_comp := $(compiler_exe)
endif
f90_comp_vers := $(shell $(f90_comp) --version 2>&1 | grep -i 'version')

ifndef f90_flags
  f90_flags :=
endif

f90_flags += $(xtr_f90_flags)

# The "-I$(mdir)" tells the compiler where to find compiled modules.
# Be sure the compiler places the compiled module in the $(mdir) directory.
#     intel uses the "-module <dir>" syntax
#     gfortran uses "-J <dir>" syntax
f90_compile = $(f90_flags) -I$(mdir)
f90_link = $(f90_flags) -I$(mdir)

