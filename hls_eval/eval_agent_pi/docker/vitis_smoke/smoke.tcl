open_project -reset smoke_project
set_top dot4
add_files top.cpp
add_files -tb tb.cpp
open_solution -reset solution1 -flow_target vivado
set_part {xc7z020clg400-1}
create_clock -period 10 -name default
csim_design
csynth_design
exit
