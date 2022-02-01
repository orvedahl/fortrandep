
script=../../bin/preprocess_file.py
input=src/main.f90
include=include/

args="--search=${include} --overwrite"

echo "##################################"
echo "EXPECT: fail"
python ${script} ${input}

echo "##################################"
echo "1: use A,D. write using D=1. defines cool, beans"
python ${script} ${input} test1.f90 ${args}

echo "##################################"
echo "2: use A,B. write using B. defines cool, beans"
python ${script} ${input} test2.f90 ${args} --macros=usemoduleB

echo "##################################"
echo "3: use A,C. write using C. defines cool, beans"
python ${script} ${input} test3.f90 ${args} --macros=usemoduleC

echo "##################################"
echo "4: use A,B. write using B,C. defines cool, beans"
python ${script} ${input} test4.f90 ${args} --macros="usemoduleB=1,usemoduleC=1"

echo "##################################"
echo "5: use A,B. write using B,D=2. defines cool, beans"
python ${script} ${input} test5.f90 ${args} --macros="using_D=2,usemoduleB"

echo "##################################"
echo "6: use A,C. write using C,D=2. defines cool, beans"
python ${script} ${input} test6.f90 ${args} --macros="using_D=2,usemoduleC"

echo "##################################"
echo "7: use A,D. write using D=1. defines cool, beans"
echo "   using_D=2 is user-defined, but the code redefines"
echo "   it with the #define using_D 1"
python ${script} ${input} test7.f90 ${args} --macros="using_D=2"

