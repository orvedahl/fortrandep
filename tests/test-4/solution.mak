#: test-4/src/data_types.f90
test-4/src/data_types.o : test-4/src/data_types.f90
#: test-4/variables.f90
test-4/variables.o : test-4/src/data_types.o
test-4/variables.o : test-4/variables.f90
#: test-4/main.f90
test-4/main.o : test-4/variables.o
test-4/main.o : test-4/main.f90
#: xmain
xmain : test-4/variables.o
xmain : test-4/src/data_types.o
xmain : test-4/main.o

