module C
#ifdef INTEL_COMPILER
  use data_types
#else
#ifdef GNU_COMPILER
  use A
#else
  #define OTHER
#endif
#endif
#ifdef OTHER
  use B
#endif
end module C

