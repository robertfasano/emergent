##############
Examples
##############

Simple network
---------------
A full example for a simple network can be found in emergent/examples/basic.py.
In this example, a single Control node oversees two Device nodes, one with inputs
'X' and 'Y' and another with input 'Z'. Take a moment to look through the code
required to initialize the network: in ``network.py``, we have simply imported
and instantiated the objects defined in the ``devices`` and ``controls`` folder.
EMERGENT hooks up the network under the hood - all you have to do is define the
node parent/child relationships.

EMERGENT uses a single script, ``main.py``, to launch any connected network, which
is defined through its ``network.py`` file which is here in the ``basic`` folder.
You can start EMERGENT with this network from the root directory (``emergent``)
by running

.. code-block :: python

   ipython
   %run main basic

Once EMERGENT launches, a GUI will open. The left pane displays the network tree;
Inputs can be changed by double-clicking on their values, entering a new value,
and pressing the Enter key.

The right pane allows optimization of selected inputs. With one or more inputs
selected in the left pane, you can choose an algorithm from the drop-down menu,
edit the parameters passed into the algorithm, and choose a cost function to
optimize.

Let's try tuning the ``deviceA`` inputs to optimize the ``cost_coupled`` function
using the ``grid_search`` algorithm and 30 steps per axis. Make sure to set
``plot:1`` to display the output.

.. image:: examples_grid_search.png

When you click the Go! button, the parameter space will be sampled uniformly and
the inputs will be set to the best discovered point:

.. image:: examples_grid_search_result.png

The grid search scales poorly with number of inputs, so often we will want to use
a cleverer algorithm. The ``differential_evolution`` algorithm is one example that
we can try:

.. image:: examples_differential_evolution_result.png

In the following examples, we'll go beyond the GUI and get a feel for EMERGENT
from the command line.

State access and actuation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~
In this example, we will assume that the inputs are initialized to 0.
There are three ways that the state of one or more inputs can be changed.
First, we could act directly on the Input node:

.. code-block :: python

   deviceA.children['X'].set(3)
   print(deviceA.state)
   print(control.state)

.. code-block :: python

   {'X':3, 'Y':0}
   {'deviceA.X':3, 'deviceA.Y':0, 'deviceB.X':0, 'deviceB.Y':0}

We can act on one or more inputs of a single device by passing in a target state to the ``Device.actuate()`` method:

.. code-block :: python

   deviceA.actuate({'X':2, 'Y':1})
   print(deviceA.state)
   print(control.state)

.. code-block :: python

   {'X':2, 'Y':1}
   {'deviceA.X':2, 'deviceA.Y':1, 'deviceB.X':0, 'deviceB.Y':0}

We can also act on any number of inputs across any number of devices through the ``Control.actuate()`` method:

.. code-block :: python

   control.actuate({'deviceA.X':7, 'deviceA.Y':2, 'deviceB.X':13})
   print(deviceA.state)
   print(deviceB.state)
   print(control.state)

.. code-block :: python

   {'X':7, 'Y':2}
   {'X':13, 'Y':0}
   {'deviceA.X':7, 'deviceA.Y':2, 'deviceB.X':13, 'deviceB.Y':0}

No matter which method we use, the result is the same: the value of each targeted
Input node is changed, and both ``device.state`` and ``control.state`` are updated.

State recall
~~~~~~~~~~~~~
The current state of our Control node can be saved by running ``control.save()``.
This stores the state dict in ``basic/settings/control.txt``. The state can be
recovered at a later time by running ``control.load()``, which will read the state
dict into memory and update included Input nodes to the loaded state.
