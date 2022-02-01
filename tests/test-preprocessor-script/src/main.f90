program main

  use A
#ifdef usemoduleB
  use B
#else
  #ifdef usemoduleC
    use C
  #else
    #define using_D 1
    use D
  #endif
#endif

  integer :: cool
#include 'definitions.h'

#ifdef usemoduleB
  write(*,*) 'using module B (ifdef)'
#endif
#ifdef usemoduleC
  write(*,*) 'using module C (nested ifdef)'
#endif
#ifdef using_D
  write(*,*) 'using module D (nested ifdef with define), D=using_D'
#endif

end program main
