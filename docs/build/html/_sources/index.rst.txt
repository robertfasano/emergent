.. EMERGENT documentation master file, created by
   sphinx-quickstart on Tue Jul 17 17:56:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

#######################
EMERGENT
#######################


Overview
-------------------
EMERGENT (Explorative Machine-learning EnviRonment for Generalized Experiments of Networked Things) is a library featuring device drivers and abstract classes allowing
universal autonomous control of laboratory experiments. The library was written based on the main belief that science progresses quickest when experimentalists 
are free to spend as much time thinking and as little time turning knobs and 
writing code as possible.

To allow simple extension to any 
research project, we model a generalized experiment as a network consisting of three types of objects: the Input, a physical degree of freedom like laser frequency or mechanical displacement; the Device, which allows Inputs to be set to desired configurations; and the Control, which oversees many devices to coordinate the experiment. The basic building block of EMERGENT is the Node class, which allows a graph-theoretic framework for experimental control and state traversal, and whose properties are inherited in the three child objects.

The goals of EMERGENT are outlined in five core tenets, each of which aims to solve an important problem
in research. We provide an introduction to these problems viewed through the lens
of a magneto-optical trapping experiment, but the tenets can
be extended to any field.




Tenet 1: Standardization
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
A magneto-optical trap requires simultaneous control of many device states: 
laser intensities and frequencies, current drivers for magnetic quadrupole coils,
beam alignment (both into optical fibers and into the MOT), etc. Generally these
devices can be interfaced with through application programming interfaces (API)
written by the manufacturer, allowing the user to send commands via USB, ethernet,
or some other protocol to manipulate the device state. In other cases (such as for
homebuilt devices), we write our own device drivers, typically involving input
and/or output of analog or digital signals. Due to the diversity of devices with
generally different communications protocols in a typical experiment, uncareful 
control architecture design can easily lead to a proliferation of code which is 
all performing the same task (device communication) in many different ways. Such
practices slow down the typically rapid early stage of experimentation, as 
well as resulting in code which is tricky to generalize to other experiments.

EMERGENT solves this problem through a standardized object-oriented design. Every device
in the network is controlled by an abstract Device class which implements a universal
syntax for describing or manipulating the state of a device, as well as providing 
common functionalities such as saving or loading states to/from an archive. Devices
not yet implemented in EMERGENT can be easily added by inheriting from the Device class,
then reimplementing the Device._connect() and Device._actuate() functions to correctly
interface with the device API, typically only requiring several lines of code. As EMERGENT grows, more and more devices will be 
natively supported, allowing control architecture for experiments to be rapidly 
constructed.


Tenet 2: Scalability
~~~~~~~~~~~~~~~~~~~~~~~
With a well-defined standardization method for device integration, it should be
very easy to add large numbers of devices from a central hub, which we refer to
as the principle of *minimal marginal device cost*: the 1001st device should be as simple to add 
to the network as the second. In the previous problem, we discussed how EMERGENT 
streamlines device *creation*, but this is not enough to ensure scalability: a 
control architecture consisting of many devices must also possess a communication
infrastructure to distribute experimental parameter changes to the correct devices.
Additionally, we want a bottom-to-top control flow, where
once a lower-level component is properly implemented, any conflicts need only 
to be addressed at the interface to the next higher layer, avoiding complicated
cross-layer debugging.

Scalability is ensured through the modular framework of experimental control through the Input->Device->Control triplet. This framework leads to self-contained ecosystems of devices (lasers, current drivers, mechanical actuators, etc) united for a common purpose (the magneto-optical trap) whose quality is measured through some output (atom number, temperature, etc). Individual triplets can be combined into a larger experiment with a simple graphical representation: horizontally separated modules have no interdependences and can be run and/or optimized in parallel, while vertically separated modules naturally enforce typical experimental sequences (e.g. first-stage cooling, second-stage cooling, etc).


Tenet 3: Automation
~~~~~~~~~~~~~~~~~~~~~~
Experimental physics is rife with simple yet tedious tasks which are typically
carried out daily. Our philosophy is that no frequently occurring problem should '
be manually solved more than once - once the important inputs and outputs are 
understood, sensors and actuators can be added to the network and used to automate
the tedious. EMERGENT offers a suite of optimization algorithms, from simple
grid searches for lower-dimensional problems, to gradient-descent and simplex
methods for middle-dimensional problems, to neural networks and genetic algorithms for simultaneous optimization of many degrees of freedom.

An example application is alignment of a laser beam into an 
optical fiber, which must be reoptimized somewhat frequently due to thermally-induced 
beam drift. Complete beam translation and steering requires four degrees of freedom,
such as tip/tilt control on two independent, high-bandwidth MEMS mirrors. A photodetector
which samples some light on the other side of the optical fiber provides a signal
to optimize. Any of the algorithms in the Optimizer module can be used to maximize
fiber coupling efficiency simply by pointing the algorithm at the MEMS axes and 
defining the optimization signal, both of which are trivial due to the standardized,
scalable interface described above.

Another important goal of EMERGENT is the ability to decouple the macroscopic 
experimental state into separate subspaces. For example, a two-wavelength
magneto-optical trap has many knobs to turn, and two of the most important are
the frequencies of the two lasers. These are often optimized separately, one
after the other, but couplings between the two knobs certainly exist, i.e. 
the detuning of the first-stage MOT affects the optimal detuning of the second-stage
through its affect on atomic temperature. Future algorithms will be designed to
identify couplings where they exist, and the Optimizer module will improve
experimental performance through simultaneous optimization of coupled degrees of freedom.

Tenet 4: Reproducibility
~~~~~~~~~~~~~~~~~~~~~~~~~
Progress on a new experiment often proceeds very quickly, and it is often time-consuming
to manually record complete experimental conditions for every single run. Additionally, 
a consequence of handing control over to a computer is that an optimal configuration may
be ruined, either by user error or by a fault of the algorithm. EMERGENT aims to solve
both problems by implementing a Database of experimental conditions, storing the last
*N* states of all devices and optimization signals such as fiber coupling efficiency or
atom number. An operator never has to worry about either careful logging or losing
an important result, since the entire experiment can be rolled back to a previous
state stored in the Database (to the extent that important degrees of freedom are
measured and controlled).

Tenet 5: Generalizability
~~~~~~~~~~~~~~~~~~~~~~~~~~~
Fragmentation of standards, whether for device communications protocols (USB, Ethernet, serial,...), 
code languages (Python, C++, LabView,...) not only makes total experimental control more difficult,
but also reduces shareability of code among different research groups. The ambitious goals
set forth by these tenets are revolutionary for any lab, and so the final tenet is that
EMERGENT *must* be usable by research groups across the physical sciences rather than
being restricted to the domain of AMO physics. Towards this end, the control architecture
is specified and written in a very abstract sense: any number of user-defined inputs 
(device substates) produce a set of outputs (experimental performance metrics),
and EMERGENT offers the ability to control the inputs to optimize the outputs. This
tremendous power can be leveraged by researchers in any field simply by adding
Device objects to the network and defining cost functions for the Optimizer.


                    
Table of Contents
-------------------
.. toctree::
   :glob:
   :maxdepth: 2

   self
   architecture
   examples
   archetypes
   devices
