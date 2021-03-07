
module B
end module B

program main
  use B
#ifdef INTEL_COMPILER
  use data_types
#else
  use A
#endif

end program main
