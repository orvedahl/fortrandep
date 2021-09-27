#
# makefile rules surounding gfortran
#

# get version
ifndef compiler_exe
  f90_comp := pgfortran
else
  f90_comp := $(compiler_exe)
endif
f90_comp_vers := $(shell $(f90_comp) --version 2>&1 | grep 'nvfortran')

ifndef f90_flags
  form = -Mfree -Mextend

  # set debugging flags
  ifdef debug
    f90_flags += $(form) -g -O0 -traceback -Mbounds \
            -Mdclchk -Minform=warn -Mchkptr -Mchkstk -r8 -i4
  else
    f90_flags += $(form) -O3 -r8 -i4
  endif

  # set OMP flags
  ifdef OMP
    f90_flags += -mp
  endif
endif

f90_flags += $(xtr_f90_flags)

# make sure modules/object files are found/included
f90_compile = $(f90_flags) -module $(mdir) -I$(mdir)
f90_link = $(f90_flags) -module $(mdir) -I$(mdir)

