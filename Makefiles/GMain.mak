#
# Main makefile build Information
#

scripts_dir := $(MAKEFILE_HOME_DIR)/scripts
compiler_directory := $(MAKEFILE_HOME_DIR)/compilers

#----------------------------------------------------------------
# remove command
#----------------------------------------------------------------
RM := -rm

#----------------------------------------------------------------
# pretty output shortcuts
#----------------------------------------------------------------
bold   = `tput bold`
normal = `tput sgr0`
red    = `tput setaf 1`
green  = `tput setaf 2`
yellow = `tput setaf 3`
blue   = `tput setaf 4`
purple = `tput setaf 5`
cyan   = `tput setaf 6`
gray   = `tput setaf 7`

#----------------------------------------------------------------
# machine info
#----------------------------------------------------------------
arch := $(shell uname)
unamen := $(shell uname -n)
hostnamef := $(shell hostname -f)

#----------------------------------------------------------------
# include some basic compiler info
#----------------------------------------------------------------
ifeq ($(findstring gfortran, $(f90_comp)),gfortran)
  include $(compiler_directory)/gfortran.mak
  comp_suf := .gfortran
else
  ifeq ($(f90_comp), intel)
    include $(compiler_directory)/intel.mak
    comp_suf := .intel
  else
    $(error "Compiler $(f90_comp) is not supported")
  endif
endif

#----------------------------------------------------------------
# suffix info/define main executable name
#----------------------------------------------------------------
ifdef debug
  debug_suf := .debug
endif

suf=$(arch)$(comp_suf)$(debug_suf)

ifdef exe_base
  base := $(exe_base)
else
  base := main
endif

ifndef do_not_modify_exe_name
  exe=x$(base).$(suf).exe
else
  exe=$(exe_base)
endif

#----------------------------------------------------------------
# define output directories
#----------------------------------------------------------------
ifndef build_dir
  tname = _build
else
  tname = $(build_dir)
endif
tdir = $(tname)/$(suf)
odir = $(tdir)/o
mdir = $(tdir)/m

#----------------------------------------------------------------
# find/include the GPackage.mak files
#----------------------------------------------------------------
f90sources =
sf90sources =
GPack_fil :=
vpath_loc :=

#----------------------------------------------------------------
# python dependency checker info
#----------------------------------------------------------------
dep_script := $(MAKEFILE_HOME_DIR)/../fortrandep/dependencies.f90

# output file
dep_file := $(tdir)/fortran.depends

#----------------------------------------------------------------
# what will be made - dependencies first, then executable
#----------------------------------------------------------------
all: $(dep_file) $(exe)

#----------------------------------------------------------------
# runtime parameter stuff (probin.f90)
#----------------------------------------------------------------
ifdef build_probin
probin_template := $(MAKEFILE_HOME_DIR)/_templates/input_params_template

ifndef namelist_name
  namelist_name := input
endif

# directories to search for the _params files
probin_dirs = . $(src_dirs)

# get list of all valid _params files
params_files := $(shell $(scripts_dir)/find_paramfiles.py $(probin_dirs))

probin.f90:
ifdef verbose
	@echo ""
	@echo "${bold}Writing probin.f90 ...${normal}"
	$(scripts_dir)/write_input_params.py -t "$(probin_template)" \
             -o probin.f90 -n $(namelist_name) -p "$(params_files)"
	@echo ""
else
	$(scripts_dir)/write_input_params.py -t "$(probin_template)" \
             -o probin.f90 -n $(namelist_name) -p "$(params_files)"
endif

f90sources += probin.f90

clean::
	$(RM) -f probin.f90
endif

#----------------------------------------------------------------
# build info stuff (build_info.f90)
#----------------------------------------------------------------
ifdef build_info
#$(dep_file): build_info.f90

build_info.f90:
ifdef verbose
	@echo ""
	@echo "${bold}Writing build_info.f90 ...${normal}"
	$(scripts_dir)/makebuildinfo.py \
           --FCOMP "$(f90_comp)" \
           --FCOMP_version "$(f90_comp_vers)" \
           --f90_compile_line "$(f90_comp) $(f90_compile) -c" \
           --link_line "$(f90_comp) $(f90_link)" \
           --source_home "$(src_dirs)"
	@echo ""
else
	$(scripts_dir)/makebuildinfo.py \
           --FCOMP "$(f90_comp)" \
           --FCOMP_version "$(f90_comp_vers)" \
           --f90_compile_line "$(f90_comp) $(f90_compile) -c" \
           --link_line "$(f90_comp) $(f90_link)" \
           --source_home "$(src_dirs)"
endif

f90sources += build_info.f90

clean::
	$(RM) -f build_info.f90
endif

#----------------------------------------------------------------
# find/include the GPackage.mak files and add locations to vpath
#----------------------------------------------------------------
# main src directory
GPack_fil += $(foreach dir, $(src_dirs), $(dir)/GPackage.mak)
vpath_loc += $(foreach dir, $(src_dirs), $(dir))

# did not find any GPackage.mak files
ifndef GPack_fil
  ifneq ($(MAKECMDGOALS), realclean)
    ifneq ($(MAKECMDGOALS), clean)
      GPack_err = "No GPackage.mak found: Set the src_dirs vars"
      $(error $(GPack_err))
    endif
  endif
endif

# include list of all source files
include $(GPack_fil)

#----------------------------------------------------------------
# get object/source files
#    sf90sources will not go through the dependency checker
#----------------------------------------------------------------
objects = $(addprefix $(odir)/, $(sort $(f90sources:.f90=.o)))
objects += $(addprefix $(odir)/, $(sort $(sf90sources:.f90=.o)))

vpath %.f90 . $(vpath_loc)

#----------------------------------------------------------------
# rule to build the dependency file
#    The magic happens with the '$^' character. This holds all 
#    the dependencies with their full directory path
#----------------------------------------------------------------
$(dep_file): $(sort $(f90sources))
	@if [ ! -d $(tdir) ]; then mkdir -p $(tdir); fi
ifdef verbose
	@echo ""
	@echo "${bold}Writing f90 dependency File ...${normal}"
	$(dep_script) --no-msgs --output=$(dep_file) \
		--skip-mods="$(skip_modules)" --prefix=$(odir)/ $^
	@echo ""
else
	$(dep_script) --no-msgs --output=$(dep_file) \
		--skip-mods="$(skip_modules)" --prefix=$(odir)/ $^
endif

# include the dependencies file (which says what depends on what)
# MAKECMDGOALS is an intrinsic GNUmakefile variable that holds what 
# target was entered on the command line
# Only include the depends file if we are not cleaning up
ifneq ($(MAKECMDGOALS), realclean)
  ifneq ($(MAKECMDGOALS), clean)
    include $(dep_file)
  endif
endif

#----------------------------------------------------------------
# build executable, i.e., Link
#----------------------------------------------------------------
$(exe): $(objects)
ifdef verbose
	@echo "${bold}Linking $@ ...${normal}"
	$(f90_comp) $(f90_link) -o $(exe) $(objects) $(library_flags) $(include_flags)
	@echo
	@echo "${bold}${green}SUCCESS${normal}"
	@echo
else
	$(f90_comp) $(f90_link) -o $(exe) $(objects) $(library_flags) $(include_flags)
	@echo
	@echo "${bold}${green}SUCCESS${normal}"
	@echo
endif

#----------------------------------------------------------------
# how to build each .o file, i.e., Compile
#----------------------------------------------------------------
$(odir)/%.o: %.f90
	@if [ ! -d $(odir) ]; then mkdir -p $(odir); fi
	@if [ ! -d $(mdir) ]; then mkdir -p $(mdir); fi
ifdef verbose
	@echo "${bold}Building $< ...${normal}"
	$(f90_comp) $(f90_compile) -c $< -o $@ $(include_flags)
else
	$(f90_comp) $(f90_compile) -c $< -o $@ $(include_flags)
endif

#----------------------------------------------------------------
# cleanup
#----------------------------------------------------------------
# make will execute even if there exists files named clean, all, etc.
.PHONY: clean realclean all

clean::
	$(RM) -f ./*.o $(odir)/*.o
	$(RM) -f ./*.mod $(mdir)/*.mod
	$(RM) -f $(dep_file)

realclean:: clean
	$(RM) -rf $(tname)
	$(RM) -f $(.exe)

#----------------------------------------------------------------
# debug aide
#----------------------------------------------------------------
# type "make print-f90sources" and it will print the 
#   value of the variable f90sources
print-%: ; @echo $* is $($*)


