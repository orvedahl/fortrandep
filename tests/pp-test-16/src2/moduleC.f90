module C
#ifdef INTEL_COMPILER
  use data_types
#else
#ifdef GNU_COMPILER
  use A
#else
  use B
#endif
#endif
end module C

