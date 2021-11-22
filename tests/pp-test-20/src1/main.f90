
module B
  use C
end module B

program main
  use B
#ifndef INTEL_COMPILER
  use data_types
#else
  use A
#endif

end program main
