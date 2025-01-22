# ROS2 Observer
Programmatic and human compatible observation of ROS.

The ROS2 observer is a "toolbox" enabling/facilitating tracing and visualizaiton of ros2 
programs/nodes.

## Getting Started

### Prerequisites
This tool requires ROS2 and Python3 installed (tested with Python3.12 and ROS 2 Jazzy)
- Python3 (tested with Python 3.12)
- ROS2 (tested with Jazzy)
- ROS2 https://github.com/ros2/ros2_tracing
- babeltrace2 
- Tested in Ubuntu 24.04
- The following system packages are required:
```
ros-${ROS_DISTRO}-ros2trace
ros-${ROS_DISTRO}-ros2trace-analysis
ros-${ROS_DISTRO}-tracetools
ros-${ROS_DISTRO}-tracetools-acceleration
ros-${ROS_DISTRO}-tracetools-acceleration-dbgsym
ros-${ROS_DISTRO}-tracetools-analysis
ros-${ROS_DISTRO}-tracetools-dbgsym
ros-${ROS_DISTRO}-tracetools-image-pipeline
ros-${ROS_DISTRO}-tracetools-image-pipeline-dbgsym
ros-${ROS_DISTRO}-tracetools-launch
ros-${ROS_DISTRO}-tracetools-read
ros-${ROS_DISTRO}-tracetools-test
ros-${ROS_DISTRO}-tracetools-trace 
babeltrace2
python3-bt2
lttng-modules-dkms
```
- Python3 PIP packages located in `requirements.pip3`

### Building With Docker
- Requires docker and GNU Make installed
On the root of the project run the provided make target/recipe:
```
make build
```

Once built the package can be installed on any debian compatible system with:
```
cd build
sudo dpkg -i *.deb
```

### Building and Installing Nativity
With GNU Make installed run `sudo make install`
The ROS2 observer python package will be installed. 


### Optional: Building Lttng Scope and Trace Compass Docker context
This project provides docker images to run Lttng Scope and Trace Compass.
They can be built with the following:
```
cd lttng_scope && make build
cd ..
cd trace_compass && make build
```

To run Trace Compass use the following make target:
```
cd trace_compass
ROS_HOME="<path to ROS home>" make start
```

To run Lttng Scope use the following make target:
```
cd lttng_scope
ROS_HOME="<path to ROS home>" make start
```

#### ROS_HOME volume
Both Lttng Scope and Trace Compass expect the environmental variable `ROS_HOME`
to be set. All tracing data should be in: ROS_HOME/tracing to be available to 
open in Lttng Scope or Trace Compass.

Unless otherwise specified the default path for both is: 
`./trace_compass/.ros/tracing` and `./lttng_scope/.ros/tracing`.

### Usage
Once installed the ROS2 Observer Python3 package provides the `ros2-tracer` 
command line tool and `ros2-node-inspector` command line tool.

#### `ros2-tracer`
The ROS 2 tracer is a session management tool that invokes the `ros2 trace`
command. It provides basic management of timed and live tracing sessions and
auto-conversion of tracing output to json (via procedural parsing) and CTF
using `babeltrace2`.

##### Basic Usage
1. Start you ROS2 nodes or programs that you want to trace
2. Start a ros trace session using the `ros2-tracer` command line program:
```
ros2-tracer -t 5 -o
```
This will run a tracing session for 5 seconds and terminate. All output will be 
placed in `ROS_HOME/tracing`

For more information on the `ros2-tracer` refer to the help with:
```
ros2-tracer --help
```

Once traces are generated they can be inspected using the provided distributions
of `Trace Compass`, `Lttng Scope` or with `babeltrace2`

#### `ros2-node-inspector`
The ROS2 Node Inspector (ros2-node-inspector) is a procedural
command line aggregator for the ROS 2 cli.

The ROS 2 Node inspector invokes and parses the output from the following 
ROS commands:
- ros2 node list
- ros2 topic info <topic name>
- ros2 node info <node name>
- ros2 interface show <message type>
  
 All ros2 cli command output is parsed into JSON and placed in 
 `ROS_HOME/ros2_node_inspector`.

##### Basic Usage
To inspect a single node invoke the `ros2-node-inspector` with the node name:
```
ros2-node-inspector <node name> 
```

To inspect all running nodes invoke `ros2-node-inspector` with to arguments:
```
ros2-node-inspector
```

For more information use: `ros2-node-inspector --help`
