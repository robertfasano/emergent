################
Architecture
################

The architecture underlying EMERGENT's scalability is a network of Node objects
which abstractly represent the experiment under study. Nodes come in three types:
Control, Device, and Input nodes.

Inputs
=======
An :doc:`/architecture/input` node is the lowest-level object in an EMERGENT network. Its sole purpose
is to represent the state of some physical variable in the lab. For example, a
power supply creating a 60 A current might be represented by an Input node called
``current`` with ``current.state=60``. The Input node class only offers basic
functionalities for representing this state; more advanced functionalities like
state actuation and optimization are carried out in higher-level nodes.

Devices
========
A :doc:`/architecture/device` node represents a physical device which is responsible
for controlling one or more Input nodes. For example, a motorized XY translation
stage could be represented by a Device node called ``stage`` with inputs ``X`` and
``Y``. The inputs can be accessed through the ``children`` attribute, e.g.
``stage.children['X']`` returns a handle to the Input node representing the X
degree of freedom. A dictionary is used to represent the state of multiple Input
nodes in a human-readable way: a typical state might be ``stage.state={'X':0, 'Y':1}``.
Changes in state are driven by the ``stage.actuate(state)`` function, which takes
a state dictionary with at least one input, drives the physical change, then updates
the internal state of the network accordingly.

Controls
=========
The :doc:`/architecture/control` node is the brain of the experiment. While Input
and Device nodes are responsible for representing and changing the experimental state,
Control nodes serve as an interface for many devices and are capable of intelligently
optimizing the macroscopic state towards a desired outcome. This macroscopic state,
containing many device substates, is represented through a nested dict which could
look like ``control.state={'stage':{'X':0,'Y':1}, 'power_supply':{'current':60}}``.
Like the Device node, the Control node possesses a method called ``actuate`` which
decomposes a macroscopic state into substates and distributes them to the correct
Device nodes.


Experiments
============
An experiment is represented through a class method of the Control node. Let's
take a look at a very basic experiment from the ``autoAlign`` class:

.. code-block :: python

  @experiment
  def measure_power(self, state):
      ''' Moves to the target alignment and measures the transmitted power. '''
      self.actuate(state)
      return -self.readADC()

This experiment steers a MEMS mirror to the specified state, e.g. ``state={'X':-60,'Y':0}``,
and measures and returns the power transmitted through an optical fiber. The @experiment
decorator carries out two functions: first, it lets EMERGENT know that this method
should appear in drop-down menus for experiment selection; second, it automatically
logs the state and experimental result every time it's called so that previous
states can be recalled. 
