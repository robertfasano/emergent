##############
Examples
##############

Fiber coupling
----------------

As a simple yet highly useful application of EMERGENT, we present here a complete walkthrough for setting up a new EMERGENT project implementing automated beam alignment into an optical fiber.

First steps
~~~~~~~~~~~~~
Before writing any code, you'll need to prepare a project directory for your application in the same directory that houses your EMERGENT package. The emergent/template directory contains a blueprint project that you can copy and rename. Let's name it "autoAlign".

You'll see several files and folders in the newly-created project directory:

* ``main.py``: the script which runs your project. In here, we'll import any modules we want to use, then define our experiment.
* ``nodes``: an empty folder which will contain any project-specific classes inheriting from Node
* ``settings``: an empty folder which will contain settings files for the experiment

If you run into trouble at any point in this tutorial, you can check your code against the emergent/examples/autoAlign directory.

Building the experiment
~~~~~~~~~~~~~~~~~~~~~~~~~
Roughly five degrees of freedom are needed to optimize beam alignment into an optical fiber: tip/tilt controls for a pair of mirrors and z-translation of a lens to allow matching of the optical mode size to the fiber mode. The latter degree appears to be fairly robust and does not need to be frequently reoptimized; here we will implement control of a single MEMS mirror as a basic introduction to the EMERGENT workflow.

Our actuator of choice is the bonded MEMS mirror from Mirrorcle, driven by their PicoAmp board. The board is controlled with SPI from a LabJack, which is fully implemented in the emergent/devices scripts labjackT7.py and picoAmp.py. The wiring scheme to connect the two boards can be found here.

The other key ingredient is a photodiode to measure the fiber coupling efficiency, which will be the optimization signal that EMERGENT will try to optimize via automated tip/tilt control. Set up the photodiode on the other side of the fiber from the mirror and connect its output to the AIN0 channel of the LabJack.

The experimental layout is shown in Figure 1. We have included an additional kinematic mirror before the MEMS to allow the setup to be manually aligned (beam centered on the MEMS and on the fiber tip) before automating the problem. Though EMERGENT will eventually support first-light acquisition methods, this example will assume that the optimization begins with a small amount of optical power transmitted through the fiber.

Building the network
~~~~~~~~~~~~~~~~~~~~~~
The network architecture for the fiber coupling problem is shown in Figure 2. The tip and tilt degrees of freedom comprise two Input nodes, labeled X and Y. The Device node takes these two nodes as inputs and physically actuates the mirror using the driver in ``emergent/devices/picoAmp.py``. The output of the Device node is connected to an Optimizer node, which measures the fiber-coupled power and sends commands to the Device node to optimize the efficiency.

Construction of this network requires only a few lines of code in ``main.py``, which should be added under the Network Construction header. First, we define the Optimizer node:

.. code-block:: python

   optimizer = Node(name='autoAlign', sensor='labjackT7', args=('490016934', 'AIN0'), layer=0)

We have constructed a node named 'autoAlign' in the bottom layer of the network. Passing in a sensor argument tells EMERGENT that this is an Optimizer node (as opposed to a Device or Input node). We also pass in the serial number and the input channel of the LabJack.

Now let's add the Device node:

.. code-block:: python

   MEMS = Node(name='MEMS', device='picoAmp', parent=optimizer, id='0001')

Passing in a device argument specifies that this is a Device node, while passing the Optimizer node as a parent makes the connection between the two. We have also specified a unique id for the Device node, whose importance will be evident below.

Finally, we can add the Input nodes:

.. code-block:: python

   Node(name='X', parent=MEMS)
   Node(name='Y', parent=MEMS)

The names we have chosen here are not arbitrary - 'X' and 'Y' correspond to the degrees of freedom defined in the picoAmp class.

Settings
~~~~~~~~~~~
With the network fully constructed, you can now start up EMERGENT from the command line:

.. code-block :: python

   ipython
   %run main.py

As a last step, we will need to add a json file in emergent/settings.py to define important operational parameters for the MEMS mirror. To do this, run ``MEMS.setup()`` to start the setup wizard for the Device node. When prompted, enter the following parameters:

.. code-block :: python

   X: 0         # defines the initial X input value
   X_min: -3.   # defines the minimum value of X
   X_max: 3     # defines the maximum value of X
   Y: 0         # defines the initial Y input value
   Y_min: -3
   Y_max: 3

The minimum and maximum positions we set will define the bounds of our optimization space. Note that the full range of the PicoAmp driver is +/-80, but +/-3 will suffice for fiber alignment.

After completing the setup wizard, a json file called ``emergent/settings/MEMS#XXXX`` will be created, where ``XXXX=0001`` here, corresponding to the id we passed in to the Device node. During normal operation, EMERGENT will frequently update and log the input values, such that the values stored in the json file will stay up to date.

Manual operation
~~~~~~~~~~~~~~~~~~
With the experiment built and the network constructed, let's now take manual control to familiarize ourselves with the command format. First, let's move the mirror. There are two ways we can do this; first, we could call the actuate() method to move the X and Y to new values, say -1 and 1:

.. code-block :: python

   MEMS.actuate({'X':-1, 'Y':1})
Note that we don't have to specify any values we don't want to change: passing in ``{'X':-1}`` will update ``X`` but leave ``Y`` unchanged.

Alternately, we could have changed the state of the input nodes directly:

.. code-block :: python

   MEMS.input['X'].set(-1)
   MEMS.input['Y'].set(1)

This will call the actuate() method indirectly, so it is functionally nearly identical to the first approach, but will offer greater flexibility when running EMERGENT in a GUI.

After moving the mirror, you should have seen the coupling efficiency change. The power can be measured by calling ``optimizer.cost()``, which will read the LabJack's channel AIN0 and multiply by -1 (by convention, all optimization problems are framed as minimization).

We can also save the new state by calling ``optimizer.save()``, which rewrites the input values stored in the settings json to their current values. If you restart emergent, the mirror should return to ``{'X':-1, 'Y':1}``.


Automated operation
~~~~~~~~~~~~~~~~~~~~~~
We are finally ready to unveil the holy grail of EMERGENT - automatic device optimization. By calling ``optimizer.optimize()``, the inputs will be tuned to maximize the fiber-coupled efficiency. Many different algorithms are implemented in EMERGENT and can be passed in through the ``method`` keyword argument; in general, the ideal algorithm will be chosen for a given application. We will first demonstrate the simplest possible algorithm, a two-dimensional grid-search.

.. code-block :: python

   optimizer.optimize(method='grid_search', args={'steps':20, 'plot':True})

This call to grid_search will create a 20x20 grid in the XY plane, sample each point, and move to the best point. If the parameter 'plot' is True, the cost function evaluated over the grid will be plotted. This allows easy visualization of cost landscapes for lower-dimensional problems, but the aggressive complexity scaling of grid_search in the number of dimensions and steps prohibits its use for higher dimensions.

A more sophisticated algorithm is the Nelder-Mead method:

.. code-block :: python

   optimizer.optimize(method='Nelder-Mead')
Rather than scanning the entire space, the Nelder-Mead method attempts to efficiently move a N+1 dimensional simplex through an N dimensional cost landscape towards a minimum.


Subspace partitioning
----------------------
A powerful feature of EMERGENT is the automatic identification of coupled variables, allowing high-dimensional optimization problems to be decomposed into separate lower-dimensional problems. For example, the idealized fiber coupling problem can be modeled as minimization in a Gaussian cost landscape, which contains no couplings between the X and Y degrees of freedom; therefore, we can run quick 1D line searches in each variable rather than a 2D simultaneous optimization, significantly reducing the size of the search space.

Rather than the physical fiber coupling example above, we will now switch to a virtual cost function to facilitate demonstration of EMERGENT's subspace identification features. The code for this tutorial can be found in emergent/examples/subspace_identification. Navigate to this directory and run main.py within an IPython console.

We analyze a simple network consisting of a control node implementing several virtual cost functions and a trivial device node which maps two virtual inputs, X and Y, to user-defined values. Two cost functions are implemented: ``control.cost_uncoupled`` and ``control.cost_coupled``. The former is simply a multivariate Gaussian with a relative factor of ½ between the widths in the X and Y directions; the latter also rotates the inputs by 30 degrees to create a coupling between X and Y.

Uncoupled optimization
~~~~~~~~~~~~~~~~~~~~~~~~
Let's inspect the uncoupled landscape with the grid_search algorithm:

.. code-block : python
   control.optimize(method='grid_search', cost=control.cost_uncoupled, args={'plot':True})

To analyze couplings between degrees of freedom, run:

.. code-block :: python
   control.covariance(cost = control.cost_uncoupled, method='grid_search')

This will generate and return a covariance matrix through sampling on a uniform grid; couplings can be identified through nonzero off-diagonal elements. In this case, we see that the off-diagonal elements are zero (within an error threshold due to finite sampling), so we can move away from the minimum then optimize the cost through two separate 1D optimizations:

.. code-block :: python
   control.actuate({'X':0, 'Y':0})
   control.optimize(method='grid_search', inputs = [MEMS.input['X']], cost = control.cost_uncoupled)
   control.optimize(method='grid_search', inputs = [MEMS.input['Y']], cost = control.cost_uncoupled)

Since the system is perfectly uncoupled, we converge to the local minimum after only 2N iterations for N steps, whereas a coupled system will require N^2 steps to tile the XY plane.

Note that calling ``control.optimize()`` without specifying arguments will eventually automatically partition the system into subspaces as evaluated by the last call to ``control.covariance()`` (feature coming soon).

Coupled optimization
~~~~~~~~~~~~~~~~~~~~~~~
Now let's inspect the landscape of the coupled cost function:
algorithm:

.. code-block : python
   control.optimize(method='grid_search', cost=control.cost_coupled, args={'plot':True})

We once again compute the covariance matrix:

.. code-block :: python
   cov = control.covariance(cost = control.cost_coupled, method='grid_search')

Since we now observe nonzero off-diagonal elements, we know that separate 1D optimizations will not converge to the minimum. Instead, we must optimize in 2D:

.. code-block :: python
   control.actuate({'X':0, 'Y':0})
   control.optimize(method='grid_search', inputs = [MEMS.input['X'], MEMS.input['Y']], cost = control.cost_coupled)

Subspace decoupling
~~~~~~~~~~~~~~~~~~~~
In the previous two sections, we have seen that uncoupled cost functions can be optimized much more efficiently than coupled functions; in d dimensions and N steps, grid_search will require N^d steps for fully-coupled functions and only Nd for uncoupled functions. EMERGENT contains built-in tools to decouple the cost function through principal component analysis (PCA), a process analogous to diagonalizing the covariance matrix. To use this feature, just run

.. code-block :: python
   control.diagonalize(cov = cov)

The ``diagonalize()`` method produces new virtual Input nodes which are eigenvectors of the covariance matrix. Now the optimization can be run in the decoupled cost landscape with the ``input_type`` flag:

.. code-block :: python
   control.optimize(method='grid_search', input_type='virtual', cost=control.cost_coupled)

Note that when using virtual inputs, the ``optimize()`` method automatically targets individual degrees of freedom sequentially.


Sequencing
------------
The examples above have shown how to use EMERGENT with steady-state optimization schemes. However, experimental outputs often depend on time-dependent inputs; for example, cold atom experiments are frequently enhanced with a ramp of the laser frequency, magnetic field strength, or some other parameter. Such sequences can be parameterized as a list of tuples containing times `t` and setpoints `s`, such as

.. code-block :: python
   s = [(0,0), (0.5,3)]

Now we add the sequence to the ``X`` variable and register it with the master clock, which synchronizes sequences across all devices:

.. code-block :: python
   MEMS.X.sequence = s
   control.clock.add_input(MEMS.X)

Adding the input to the clock lets EMERGENT know that we want to run ``X`` in sequenced, not steady-state, operation. The last step is to start the clock with ``control.clock.start(T=0.5)''. Note that the time values in the sequence definition correspond to fractions of the total cycle, so with this cycle of 0.5 s, the MEMS will move to a position of 3 after 250 ms, then back to 0 after each new cycle starts.
