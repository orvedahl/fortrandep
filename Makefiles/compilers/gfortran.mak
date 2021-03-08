#
# makefile rules surounding gfortran
#

# get version
f90_comp_vers := $(shell $(f90_comp) -v 2>&1 | grep 'version')

ifndef f90_flags
  form = -ffree-form -ffixed-line-length-132

  # set debugging flags
  ifdef debug
    f90_flags += $(form) -g -fno-range-check -O0 -fbounds-check -fbacktrace \
            -Wuninitialized -Wunused -ffpe-trap=invalid,zero,overflow \
            -finit-real=nan -finit-integer=nan
  else
    f90_flags += $(form) -O3 -fno-range-check
  endif

  # set OMP flags
  ifdef OMP
    f90_flags += -fopenmp
  endif
else
  f90_flags :=
endif

f90_flags += $(xtr_f90_flags)

# make sure modules/object files are found/included
f90_compile = $(f90_flags) -J$(mdir) -I$(mdir)
f90_link = $(f90_flags) -J$(mdir) -I$(mdir)

