#
# makefile rules surrounding Intel compiler
#

# get version
ifndef compiler_exe
  f90_comp := ifort
else
  f90_comp := $(compiler_exe)
endif
f90_comp_vers := $(shell $(f90_comp) -V 2>&1 | grep 'Version')

intel_dbg = -FR -r8 -O0 -traceback -g -check all -noinline -debug all -warn all -shared-intel

ifndef f90_flags
  # set debugging flags
  ifdef debug
    f90_flags := $(intel_dbg)
  else
    f90_flags := -FR -r8 -O3 -shared-intel
  endif

  # set OMP flags
  ifdef OMP
    f90_flags += -qopenmp
  endif
endif

f90_flags += $(xtr_f90_flags)

# make sure modules/object files are found/included
f90_compile = $(f90_flags) -module $(mdir) -I$(mdir)
f90_link = $(f90_flags) -module $(mdir) -I$(mdir)

