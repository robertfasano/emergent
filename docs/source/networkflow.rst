###############
Network flow
###############

In this page we describe the overall control flow of EMERGENT, including network
construction and initialization, state and sequence actuation, and optimization.
We will follow the example network in ``emergent/examples/basic``.

Network construction
======================

The Control node
-----------------
To define a network, we first define a Control node:

.. code-block:: python

   import sys
   from examples.basic.controls.testControl import TestControl
   control = TestControl('control', path='examples/%s'%sys.argv[1])

The first argument to the node initializer is the ``name`` 'control', which will
label the node within the network tree. It doesn't have to be the same as the
variable name, but it may be helpful. The second argument is the path of our
network directory - to start emergent, we will run ``main.py`` in the root
directory with the argument ``basic`` to specify this network.

When a Control node is initialized, it first calls its parent initializer,
``Node.__init__(name, parent)``, which does five things:

#. Save the passed name as an attribute ``self.name=name``.
#. Append ``self`` to the ``instances`` variable, which will allow nodes of a single type to be collected.
#. Define the empty ``self.children`` dict.
#. Register self with parent (in this case ``parent==None``, so no action is taken)
#. Find the root node (which for a control node is itself)

After initializing the ``Node``, the Control class does a few more things:

#. Initialize empty dicts for ``inputs``, ``state``, ``settings``, and ``sequences``.
#. Set ``self.actuating=0`` to indicate that no motion is currently occurring.
#. Prepare paths to the settings, state, sequence, and data directories based on our network specified in ``sys.argv[1]``.
#. Initialize the Clock, Historian, and Optimizer modules.

Adding devices
------------------
With the Control node defined, we can now add child Device nodes:

.. code-block:: python

   deviceA = TestDevice('deviceA', parent=control)
   deviceB = TestDevice('deviceB', parent=control)

Again we have specified a name, and this time we have specified that each device
is a child of the parent Control node. The Node initialization will proceed
similarly, but this time the ``Node.register(parent)`` function will occur.
This function links the nodes so that the Device node can access the Control node
through the ``Device.parent`` variable, while the Control node can access the
Device node through an entry in the ``Control.children`` dict. The Node initializer
also finds the root again, which is the Control node.

Next, in the Device initializer, the ``Device.state`` variable is initialized to
an empty dict. In the definition of the inheriting class ``TestDevice``, we define
two variables ``X`` and ``Y`` by calling the ``Device.add_input`` function twice.
This function generates an Input node, which once again repeats the Node initializer
and then defines placeholders for variables which will be set later.

After creating the Input node, ``Device.add_input(name)`` does four things:

#. Add the input node by ``name`` to the ``Device.children`` dict.
#. Add the input node by ``full_name`` to the ``Control.inputs`` dict.
#. Call the Control.load(input.full_name) method to attempt to recall a previous state.
#. Set the ``name`` component of ``Device.state`` equal to the state of the input, which is loaded in the previous step.

The ``Control.load()`` method takes a ``full_name`` as an argument and searches for
this component within the last entry of its settings, sequence, and state files.

State actuation
=================
The specific control flow for actuation is designed to make sure that the state
of an Input node never loses sync with its representation in the Device and Control
nodes. Actuation begins with a call to ``Control.actuate()`` with a state dict as
an argument. This indices of this state dict are ``full_name`` variables for each
input such as ``'deviceA.X'`` which label both the device and the state.

#. For each item in the state, call the ``Input.set()`` method of the corresponding Input node.
#. The Input node requests a new state from the parent Device node by passing itself and the target value into a call to ``Device.actuate()``.
#. ``Device.actuate()`` first calls ``Device._actuate()``, which is a private  function implemented for each separate device; this function changes the physical  state (e.g. by setting a voltage to a certain value) but does not change the virtual state.
#. Next, ``Device.actuate()`` calls ``Device.update()``, which simultaneously updates the state of the Input, Device, and Control nodes.

Primary and secondary inputs
-----------------------------
A useful feature is the ability to represent a Device state in terms of multiple
sets of inputs. Perhaps you have an apparatus which converts a voltage setpoint into
a current; in this case, it is convenient to be able to choose either the voltage
or the current and have the other quantity update automatically. We refer to the
voltage as a primary input and the current as a secondary input; secondary
input nodes can be created by passing the keyword argument ``type='virtual'``
into the constructor.

Currently only one set of secondary inputs can be constructed. The secondary inputs
are related to the primary inputs by a pair of methods ``primary_to_secondary`` and
``secondary`` which must be implemented in the Device driver class. Only
one set of inputs can be active at once, and can be chosen by calling
``Device.use_inputs(type)``, where type can be ```primary``` or ```secondary```.
When this method is called, the current representation will be converted into the
other representation and the state dicts of the Device and Control nodes will be
updated accordingly. Note that no actuation is done, since the two states are
physically identical.

When the Device.actuate() method is called, the current input type of the Device
is checked.

An important note must be made here about real (primary) inputs (settable quantities in the
lab) vs. virtual (secondary) inputs, which are functions of real inputs. For example, the
CurrentDriver() class controls a current servo which takes analog voltages and
outputs proportional currents into a pair of coils. Although the analog voltages
are the real inputs, it is experimentally convenient to work with the gradient and
zero position of the magnetic field coils instead, which are virtual inputs;
the real and virtual inputs can be converted to and from each other using known
calibration data and an analytical model for the magnetic field as a function of
current.



EMERGENT allows actuation in terms of either the virtual or real inputs (as long
as the two aren't mixed within one call to actuate()). In the case of the
CurrentDriver class, pointing ``actuate()`` at the virtual inputs will first
convert them to real inputs before setting the physical variables.


Sequencing
============



Optimization
==============
