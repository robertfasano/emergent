#################
Getting started
#################

Installing EMERGENT
---------------------
The latest version of EMERGENT can be found at https://gitlab.com/emergentlab/emergent.
You can download it using Git: just run

.. code-block :: python

   git clone https://gitlab.com/emergentlab/emergent.git

in the directory of your choice. Before installing, make sure you have the latest version of Anaconda installed.
To avoid dependency conflicts with other libraries, we'll create a new virtual
environment to install EMERGENT in:

.. code-block :: python

   conda create --name emergent

Follow the prompt to create the new environment, then activate it with ``conda activate emergent``.
Now navigate to the ``emergent`` folder wherever you downloaded it and install using

.. code-block :: python

   python setup.py install


Optimization
--------------
A full example for a simple network can be found in emergent/networks/example.py.
In this example, a single Hub oversees two Things, one with inputs
'X' and 'Y' and another with inputs 'X' and 'Y'. Take a moment to look through the code
required to initialize the network: in ``network.py``, we have simply imported
and instantiated the objects defined in the ``things`` and ``hubs`` folder.
EMERGENT hooks up the network under the hood - all you have to do is define the
node parent/child relationships.

EMERGENT uses a single script, ``main.py``, to launch any connected network, which
is defined through its ``network.py`` file which is here in the ``example`` folder.
You can start EMERGENT with this network from the root directory (``emergent``)
by running

.. code-block :: python

   ipython
   %run main example

Once EMERGENT launches, a GUI will open. The left pane displays the network tree,
with top-level Hubs overseeing one or more Things, each of which
having one or more Input node. The state of a Thing can be changed by double-clicking
on one of its Input nodes, entering a new value, and pressing the Enter key.

The middle panel offers three different modes: Optimize, Run, and Servo. Let's look
at the Optimize tab first. If you select an input node, the right drop-down box
will load all functions tagged with the @experiment decorator within the hub node.
User-defined parameter options will be loaded in the table below. On the left side
of the Optimize tab, you can choose an optimization algorithm from the drop-down
menu, then customize the hyperparameters for your given application. The Save button
lets you save parameter sets that work well, whether you found these through trial
and error or through the upcoming hyperparameter tuning feature.

Let's try it out!. Make sure that both inputs, ``X`` and ``Y`` are selected, then
choose the GridSearch algorithm and set the number of steps to 30. The parameters for
the ``cost_uncoupled`` function let you define the position, extent, and noise level
of a two-dimensional Gaussian function. When you click the Go button, the optimization
will start, and the task will appear in the Tasks panel at right. Double-clicking
the task entry will open a visualizer window that offers several different displays:

* The Summary tab displays the experimental and optimizer settings chosen, as well as a plot of the experiment value vs. time which can be used to check for convergence.
* The 1D tab plots the cost vs. input relationships for any included input, letting you visualize the parameter space of the experiment. It also shows the input vs. time, so you can see how the optimizer was selecting points to sample.
* For optimizations of 2 or more inputs, the 2D tab displays cross-sectional plots of the parameter space.

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
