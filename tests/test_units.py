"""
Test the FortranModule and FortranFile classes
"""
import pytest
import os
import utils # must appear before the fortrandep import
from fortrandep import FortranModule

def test_FortranModule_no_sourcefile(tmpdir):
    fname = tmpdir.mkdir("sub").join("module_def.f90")
    contents = ["module Testing", "\n",
                "  implicit none", "\n",
                "  use modA",
                "  use modB", "\n",
                "  real, parameter :: pi = 3.14",
                "  integer :: k", "\n",
                "  contains", "\n",
                "  subroutine print()",
                "    write(*,*)",
                "    write(*,*)",
                "  end subroutine print", "\n",
                "end module Testing"]

    FH = FortranModule("module", "Testing", source_file=None)
    assert FH.unit_type == "module"
    assert FH.name == "testing"

    # when no source_file is given, an explicit call to get_uses is required
    FH.uses = FH.get_uses(contents, macros=None)
    assert len(FH.uses) == 2

