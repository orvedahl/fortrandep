#
# Main makefile build Information
#

#----------------------------------------------------------------
# various locations
#----------------------------------------------------------------
dep_script_dir := $(MAKEFILE_HOME_DIR)/../bin/
scripts_dir := $(MAKEFILE_HOME_DIR)/scripts
compiler_dir := $(MAKEFILE_HOME_DIR)/compilers
template_dir := $(MAKEFILE_HOME_DIR)/_templates/

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
ifeq ($(f90_compiler), $(filter $(f90_compiler), GNU gfortran GCC gnu))
  include $(compiler_dir)/gfortran.mak
  comp_suf := .gfortran
else
  ifeq ($(f90_compiler), $(filter $(f90_compiler), Intel ifort intel))
    include $(compiler_dir)/intel.mak
    comp_suf := .intel
  else
    $(error "Compiler $(f90_compiler) is not supported")
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
f90sources :=
sf90sources :=
internal_f90sources :=
GPack_fil :=
vpath_loc :=

#----------------------------------------------------------------
# python dependency checker info
#----------------------------------------------------------------
ifndef python_exe
  python_exe := python
endif

dep_script := $(dep_script_dir)/generate_dependencies.py

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
probin_template := $(template_dir)/input_params_template

ifndef namelist_name
  namelist_name := input
endif

# directories to search for the _params files
probin_dirs = . $(src_dirs)

# get list of all valid _params files
params_files := $(shell $(python_exe) $(scripts_dir)/find_paramfiles.py $(probin_dirs))

probin.f90:
	@echo ""
	@echo "${bold}Writing probin.f90 ...${normal}"
	$(python_exe) $(scripts_dir)/write_input_params.py -t "$(probin_template)" \
             -o probin.f90 -n $(namelist_name) -p "$(params_files)"

f90sources += probin.f90
internal_f90sources += probin.f90

clean::
	$(RM) -f probin.f90
endif

#----------------------------------------------------------------
# build info stuff (build_info.f90)
#----------------------------------------------------------------
ifdef build_info
build_info.f90:
	@echo ""
	@echo "${bold}Writing build_info.f90 ...${normal}"
	$(python_exe) $(scripts_dir)/makebuildinfo.py \
           --FCOMP "$(f90_compiler)" \
           --FCOMP_version "$(f90_comp_vers)" \
           --f90_compile_line "$(f90_comp) $(f90_compile) -c" \
           --link_line "$(f90_comp) $(f90_link)" \
           --source_home "$(src_dirs)"
	@echo ""

f90sources += build_info.f90
internal_f90sources += build_info.f90

clean::
	$(RM) -f build_info.f90
endif

#----------------------------------------------------------------
# find/include the GPackage.mak files and add locations to vpath
#----------------------------------------------------------------
ifdef find_GPackage_files
  GPack_fil += $(foreach dir, $(src_dirs), $(dir)/GPackage.mak)
  ifndef GPack_fil
    # did not find any GPackage.mak files
    ifneq ($(MAKECMDGOALS), realclean)
      ifneq ($(MAKECMDGOALS), clean)
        ifneq ($(MAKECMDGOALS), purge)
          GPack_err = "No GPackage.mak found: Set the src_dirs vars"
          $(error $(GPack_err))
        endif
      endif
    endif
  endif

  # include list of all source files
  include $(GPack_fil)
endif

# only need to add source directories
vpath_loc += $(src_dirs)

#----------------------------------------------------------------
# get object/source files
#    sf90sources will not go through the dependency checker
#----------------------------------------------------------------
# strip file extension, add ".o" suffix, sort & remove duplicates, then add "odir/" prefix
ifdef find_GPackage_files
  objects = $(addprefix $(odir)/, $(sort $(addsuffix .o, $(basename $(f90sources)))))
  objects += $(addprefix $(odir)/, $(sort $(addsuffix .o, $(basename $(sf90sources)))))
else
  objects_file := $(tdir)/fortran.objects
endif

# where to look for each type of file extension
vpath %.f90 . $(vpath_loc)
vpath %.F90 . $(vpath_loc)

#----------------------------------------------------------------
# rule to build the dependency file
#    The magic happens with the '$^' character. This holds all 
#    the dependencies with their full directory path and gets
#    passed to the script as a space separated list of files
#----------------------------------------------------------------
ifdef find_GPackage_files
$(dep_file): $(internal_f90sources) $(f90sources)
	@if [ ! -d $(tdir) ]; then mkdir -p $(tdir); fi
	@echo ""
	@echo "${bold}Writing f90 dependency File ...${normal}"
	$(python_exe) $(dep_script) --output=$(dep_file) --preprocess \
		--exclude="$(sf90sources)" \
		--ignore-mods="$(skip_modules)" \
		--macros="$(pp_macros)" \
		--search-paths="$(pp_search_paths)" \
		--build=$(odir)/ \
		$^
	@echo ""
else
# go find the source files, then build the dependencies
# make sure the probin/build_info are included and explicitly include "." source dir
$(dep_file): $(internal_f90sources) $(src_dirs)
	@if [ ! -d $(tdir) ]; then mkdir -p $(tdir); fi
	@echo ""
	@echo "${bold}Writing f90 dependency File ...${normal}"
	$(python_exe) $(dep_script) --output=$(dep_file) --preprocess \
		--exclude="$(sf90sources)" \
		--ignore-mods="$(skip_modules)" \
		--macros="$(pp_macros)" \
		--search-paths="$(pp_search_paths)" \
		--build=$(odir)/ \
	        --find-source --extensions=".f90 .F90" \
	        --add-files="$(internal_f90sources)" \
		"." $(src_dirs)
	@echo ""
	@echo "${bold}Writing list of object Files ...${normal}"
	$(python_exe) $(scripts_dir)/find_objects.py $(dep_file) $(objects_file)
	@echo ""
clean::
	$(RM) -f $(objects_file)
endif

# include the dependencies file (which says what depends on what)
# MAKECMDGOALS is an intrinsic GNUmakefile variable that holds what 
# target was entered on the command line
# Only include the depends file if we are not cleaning up
# the "-include" operates identically to include, but suppresses errors
ifneq ($(MAKECMDGOALS), realclean)
  ifneq ($(MAKECMDGOALS), clean)
    ifneq ($(MAKECMDGOALS), purge)
      -include $(dep_file)
    endif
  endif
endif
ifndef find_GPackage_files
  ifneq ($(MAKECMDGOALS), realclean)
    ifneq ($(MAKECMDGOALS), clean)
      ifneq ($(MAKECMDGOALS), purge)
        -include $(objects_file)
      endif
    endif
  endif
endif

#----------------------------------------------------------------
# build executable, i.e., Link
#----------------------------------------------------------------
$(exe): $(objects)
	@echo "${bold}Linking $@ ...${normal}"
	$(f90_comp) $(f90_link) -o $(exe) $(objects) $(library_flags) $(include_flags)
	@echo
	@echo "${bold}${green}SUCCESS${normal}"
	@echo

#----------------------------------------------------------------
# how to build each .o file, i.e., Compile
#----------------------------------------------------------------
$(odir)/%.o: %.f90
	@if [ ! -d $(odir) ]; then mkdir -p $(odir); fi
	@if [ ! -d $(mdir) ]; then mkdir -p $(mdir); fi
	@echo "${bold}Building $< ...${normal}"
	$(f90_comp) $(f90_compile) -c $< -o $@ $(include_flags)

# include different extensions
$(odir)/%.o: %.F90
	@if [ ! -d $(odir) ]; then mkdir -p $(odir); fi
	@if [ ! -d $(mdir) ]; then mkdir -p $(mdir); fi
	@echo "${bold}Building $< ...${normal}"
	$(f90_comp) $(f90_compile) -c $< -o $@ $(include_flags)

#----------------------------------------------------------------
# cleanup
#----------------------------------------------------------------
# make will execute even if there exists files named clean, all, etc.
.PHONY: clean realclean purge all

clean::
	$(RM) -f ./*.o $(odir)/*.o
	$(RM) -f ./*.mod $(mdir)/*.mod
	$(RM) -f $(dep_file)

realclean:: clean
	$(RM) -rf $(tname)
	$(RM) -f $(exe)

# somewhat dangerous, depending on what other files there are
purge: realclean
	$(RM) -f ./*.exe

#----------------------------------------------------------------
# debug aide
#----------------------------------------------------------------
# type "make print-f90sources" and it will print the 
#   value of the variable f90sources
print-%: ; @echo $* is $($*)


