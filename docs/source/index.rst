.. labAPI documentation master file, created by
   sphinx-quickstart on Tue Jul 17 17:56:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

#######################
labAPI
#######################


Overview
-------------------
labAPI is a library featuring device drivers and abstract classes allowing
universal control of laboratory experiments.To allow simple extension to any 
research project, we model a generalized experiment as a network consisting of
*N* inputs, *M* outputs, and *L* intermediate layers, each of which possessing
some number of inputs and outputs.

The library was written based on 
the main belief that science progresses quickest when experimentalists 
are free to spend as much time thinking and as little time turning knobs and 
writing code as possible. This naturally leads to five core tenets underlying 
the development of labAPI, each of which aiming to solve an important problem
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
practices needlessly consume the experimentalist's time during development, as 
well as resulting in code which is tricky to generalize to other experiments.

labAPI solves this problem through a standardized object-oriented design. Every device
in the network is controlled by an abstract Device class which implements a universal
syntax for describing or manipulating the state of a device, as well as providing 
common functionalities such as saving or loading states to/from an archive. Devices
not yet implemented in labAPI can be easily added by inheriting from the Device class,
then rewriting the Device._connect() and Device._actuate() functions to correctly
interface with the device API. As labAPI grows, more and more devices will be 
natively supported, allowing control architecture experiments to be rapidly 
constructed.


Tenet 2: Scalability
~~~~~~~~~~~~~~~~~~~~~~~
With a well-defined standardization method for device integration, it should be
very easy to add large numbers of devices from a central hub, which we refer to
as *minimal marginal device cost*: the 1001st device should be as simple to add 
to the network as the second. In the previous problem, we discussed how labAPI 
streamlines device *creation*, but this is not enough to ensure scalability: a 
control architecture consisting of many devices must also possess a communication
infrastructure to distribute experimental parameter changes to the correct devices.
Additionally, we want a bottom-to-top control flow, where
once a lower-level component is properly implemented, any conflicts need only 
to be addressed at the interface to the next higher layer, avoiding complicated
cross-layer debugging.

We now overview the automated "plumbing" that goes on behind the scenes to hook 
up your devices to the network for actual use. Although any device driver inheriting from the Device class will be able to 
run independently, the true power of labAPI is revealed in our second abstract
class: the Hub. A Hub represents a fully self-contained ecosystem of devices (lasers, current drivers, etc)
united for a common purpose (the magneto-optical trap). Devices can be added as
child objects to a parent Hub upon instantiation, and the Hub acquires a macroscopic
state vector composed of all of the concatenated states from its child Devices.
We can think of a single Hub as an entire experiment, with its input state
(frequency, intensity, etc) producing an output state (atom number, temperature, etc).
Or, a Hub can be a building block of a larger experiment, which can
be thought of as a higher-layered Hub which uses the outputs of the previous Hub layer
as its inputs. 

The Hub archetype also inherits from the Link class, which connects the control code,
which runs in Python, to the Application gui, which can in principle be written in any language
but here is implemented in QML. The Application itself is constructed in a scalable manner,
where new Hubs automatically register themselves within the QML engine and appear
in the interface. Python's powerful introspection features also allow an
automatically-populated function browser within the Application, allowing the user
to run any Device function by navigating through the Hub->Device->function 
hierarchy.

This hierarchical infrastructure enforces standardized, modular data flow from a Device
to its parent Hub to other parts of the experiment, as well as providing an
automatically-generated yet beautiful user interface with which to control the
entire experiment.


Tenet 3: Automation
~~~~~~~~~~~~~~~~~~~~~~
Experimental physics is rife with simple yet tedious tasks which are typically
carried out daily. Our philosophy is that no frequently occurring problem should '
be manually solved more than once - once the important inputs and outputs are 
understood, sensors and actuators can be added to the network and used to automate
the tedious. labAPI offers a suite of optimization algorithms, from simple
grid searches for lower-dimensional problems, to gradient-descent and simplex
methods for middle-dimensional problems, to neural networks for simultaneous optimization
of many degrees of freedom.

An example application is alignment of a laser beam into an 
optical fiber, which must be reoptimized somewhat frequently due to thermally-induced 
beam drift. Complete beam translation and steering requires four degrees of freedom,
such as tip/tilt control on two independent, high-bandwidth MEMS mirrors. A photodetector
which samples some light on the other side of the optical fiber provides a signal
to optimize. Any of the algorithms in the Optimizer module can be used to maximize
fiber coupling efficiency simply by pointing the algorithm at the MEMS axes and 
defining the optimization signal, both of which are trivial due to the standardized,
scalable interface described above.

Another important goal of labAPI is the ability to decouple the macroscopic 
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
be ruined, either by user error or by a fault of the algorithm. labAPI aims to solve
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
labAPI *must* be usable by research groups across the physical sciences rather than
being restricted to the domain of AMO physics. Towards this end, the control architecture
is specified and written in a very abstract sense: any number of user-defined inputs 
(device substates) produce a set of outputs (experimental performance metrics),
and labAPI offers the ability to control the inputs to optimize the outputs. This
tremendous power can be leveraged by researchers in any field simply by adding
Device objects to the network and defining cost functions for the Optimizer.


                    
Table of Contents
-------------------
.. toctree::
   :glob:
   :maxdepth: 2

   self
   examples
   archetypes
   devices
