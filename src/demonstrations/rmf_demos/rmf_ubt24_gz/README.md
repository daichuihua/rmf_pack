# rmf_ubt24_gz

This package provides top level launch files using the Gazebo simulator demonstrating how to build and start systems using RMF.

# command line:
source ~/rmf_ws/install/setup.bash
ros2 launch rmf_ubt24_gz ubt24.launch.xml server_uri:="ws://localhost:8001"

# example:
ros2 run rmf_demos_tasks dispatch_loop -s L8_1 -f L8_4 -n 3 --use_sim_time

