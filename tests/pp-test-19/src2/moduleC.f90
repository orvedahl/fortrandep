module C
#ifdef INTEL_COMPILER
  use data_types
#else
  #define OTHER
#endif
#ifdef OTHER
  use A
#endif
end module C

