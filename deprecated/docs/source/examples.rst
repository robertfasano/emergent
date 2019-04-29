##############
Examples
##############

Simple network
---------------
A full example for a simple network can be found in emergent/networks/example.py.
In this example, a single Hub oversees two Things, one with inputs
'X' and 'Y' and another with inputs 'X' and 'Y'. Take a moment to look through the code
required to initialize the network: in ``network.py``, we have simply imported
and instantiated the objects defined in the ``things`` and ``hubs`` folder.
EMERGENT hooks up the network under the hood - all you have to do is define the
node parent/child relationships.

EMERGENT uses a single script, ``main.py``, to launch any connected network, which
is defined through its ``network.py`` file which is here in the ``basic`` folder.
You can start EMERGENT with this network from the root directory (``emergent``)
by running

.. code-block :: python

   ipython
   %run master example

Once EMERGENT launches, a GUI will open. The left pane displays the network tree,
with top-level Hubs overseeing one or more Things, each of which
having one or more Input node. The state of a Thing can be changed by double-clicking
on one of its Input nodes, entering a new value, and pressing the Enter key.

The right pane lets you run and/or optimize experiments. The drop-down menu at
the top is automatically populated with all functions tagged with the @experiment
decorator within the currently selected Hub. You can run an experiment
from the Run tab with a chosen number of iterations and delay between each loop.
Experiments return data in an array, and the post-processing menu allows different
quantities to be output; for example, with the same experiment you may wish to view
the mean, standard deviation, or slope of all of the data gathered.

The Optimize tab gives experimental control to EMERGENT with the goal of minimizing
the result of the given experiment. With one or more inputs selected in the network
tree and a target experiment, you can choose an optimization algorithm from the
lower drop-down menu.

Let's try tuning the ``thingA`` inputs to optimize the ``cost_coupled`` function
using the ``grid_search`` algorithm and 30 steps per axis. Make sure to click the
plot checkbox to display the output.

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
There are two ways that the state of one or more inputs can be changed.
First, we could act on a Thing with the ``Thing.actuate()`` method:

.. code-block :: python

   thingA.actuate({'X':2, 'Y':1})
   print(thingA.state)
   print(hub.state)

.. code-block :: python

   {'X':2, 'Y':1}
   {'thingA':{'X':2,'.Y':1}, 'thingB':{'X':0, 'Y':0}}

We can also act on any number of inputs across any number of things through the ``Hub.actuate()`` method:

.. code-block :: python

   hub.actuate({'thingA':{'X':7,'.Y':2}, 'thingB':{'X':13}})
   print(thingA.state)
   print(thingB.state)
   print(hub.state)

.. code-block :: python

   {'X':7, 'Y':2}
   {'X':13, 'Y':0}
   {'thingA':{'X':7,'.Y':2}, 'thingB':{'X':13}}

No matter which method we use, the result is the same: the value of each targeted
Input node is changed, and both ``thing.state`` and ``hub.state`` are updated.
