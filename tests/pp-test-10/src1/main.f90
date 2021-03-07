
module B
end module B

program main
  use A
  use B
#ifdef INTEL_COMPILER
  use data_types
#endif

end program main
