##############
Examples
##############

Simple network
---------------
A full example for a simple network can be found in emergent/examples/basic.py. In this example, a single Control node oversees two Device nodes, one with inputs 'X' and 'Y' and another with input 'Z'. Take a moment to look through the code required to initialize the network.

You can start EMERGENT with this network from the root directory by running

.. code-block :: python

   ipython
   %run main basic

Accessing node attributes
~~~~~~~~~~~~~~~~~~~~~~~~~~
In this example, all of the inputs are initialized to zero. We can check this in three different ways. First, we can check the value of an Input node directly:

.. code-block :: python

   print(deviceA.inputs['X'].value)

.. code-block :: python

   0

Second, we can check the state of a device:

.. code-block :: python

   print(deviceA.state)

.. code-block :: python

   {'X':0, 'Y':0}

Lastly, we can check the overall state of all devices connected to the Control node:

.. code-block :: python

   print(control.state)

.. code-block :: python

   {'deviceA.X':0, 'deviceA.Y':0, 'deviceB.Z':0}

Note the slightly different syntax: state dicts for Device nodes have only the input names as keys, whereas for a Control node we must also pass in the device name; this is to allow multiple devices to share a parameter with the same name, for example ``X``.

Actuation
~~~~~~~~~~~
There are three ways that the state of one or more inputs can be changed. First, we could act directly on the Input node:

.. code-block :: python

   deviceA.inputs['X'].set(3)
   print(deviceA.state)
   print(control.state)

.. code-block :: python

   {'X':3, 'Y':0}
   {'deviceA.X':3, 'deviceA.Y':0, 'deviceB.Z':0}

We can act on one or more inputs of a single device by passing in a target state to the ``Device.actuate()`` method:

.. code-block :: python

   deviceA.actuate({'X':2, 'Y':1})
   print(deviceA.state)
   print(control.state)

.. code-block :: python

   {'X':2, 'Y':1}
   {'deviceA.X':2, 'deviceA.Y':1, 'deviceB.Z':0}

We can also act on any number of inputs across any number of devices through the ``Control.actuate()`` method:

.. code-block :: python

   control.actuate({'deviceA.X':7, 'deviceA.Y':2, 'deviceB.Z':13})
   print(deviceA.state)
   print(deviceB.state)
   print(control.state)

.. code-block :: python

   {'X':7, 'Y':2}
   {'Z':13}
   {'deviceA.X':7, 'deviceA.Y':2, 'deviceB.Z':13}

No matter which method we use, the result is the same: the value of each targeted Input node is changed, and both ``device.state`` and ``control.state`` are updated.

State recall
~~~~~~~~~~~~~
The current state of our Control node can be saved by running ``control.save()``. This stores the state dict in ``basic/settings/control.txt``. The state can be recovered at a later time by running ``control.load()``, which will read the state dict into memory and update included Input nodes to the loaded state.

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

The first step in building the network is to define a custom control node for our alignment task:

.. code-block:: python

   class AutoAlign(Control):
         def __init__(name, labjack, parent=None):
                  super().__init__(name, parent)
                  self.labjack = LabJack()

         def cost(state):
                  self.actuate(state)
                  return self.labjack.AIn(0)

Now we can connect to the LabJack and instantiate the Control node:

.. code-block:: python

   devid = '160049734'
   labjack = LabJack(devid=devid)
   control = AutoAlign(name='control', labjack=labjack)

The final step is to define the Device node based on the custom class in ``emergent/devices/picoAmp.py`` and add Inputs:

.. code-block:: python

   mems = PicoAmp('MEMS', labjack, parent=control)
   mems.add_input('X', 0, -3, 3)
   mems.add_input('Y', 0, -3, 3)

Note that the first argument to the ``add_input`` function should match one of the inputs defined in the Device driver, which in this case are ``X`` and ``Y``. The remaining arguments are the value and min/max values of the inputs, respectively.

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

After moving the mirror, you should have seen the coupling efficiency change. The power can be measured by calling ``control.cost()``, which will read the LabJack's channel AIN0 and multiply by -1 (by convention, all optimization problems are cast as minimization).

We can also save the new state by calling ``control.save()``, which writes the current settings to a json file in ``emergent/examples/MEMS_align/settings``. Calling ``control.load()`` will allow the saved state to be recovered.


Automated operation
~~~~~~~~~~~~~~~~~~~~~~
We are finally ready to unveil the holy grail of EMERGENT - automatic device optimization. By calling ``control.optimizer.optimize()``, the inputs will be tuned to maximize the fiber-coupled efficiency. Many different algorithms are implemented in EMERGENT and can be passed in through the ``method`` keyword argument; in general, the ideal algorithm will be chosen for a given application. We will first demonstrate the simplest possible algorithm, a two-dimensional grid-search.

.. code-block :: python

   control.optimizer.optimize(method='grid_search', args={'steps':20, 'plot':True})

This call to grid_search will create a 20x20 grid in the XY plane, sample each point, and move to the best point. If the parameter 'plot' is True, the cost function evaluated over the grid will be plotted. This allows easy visualization of cost landscapes for lower-dimensional problems, but the aggressive complexity scaling of grid_search in the number of dimensions and steps prohibits its use for higher dimensions.

A more sophisticated algorithm is the Nelder-Mead method:

.. code-block :: python

   control.optimizer.optimize(method='Nelder-Mead')
Rather than scanning the entire space, the Nelder-Mead method attempts to efficiently move a N+1 dimensional simplex through an N dimensional cost landscape towards a minimum.


Subspace partitioning
----------------------
A powerful feature of EMERGENT is the automatic identification of coupled variables, allowing high-dimensional optimization problems to be decomposed into separate lower-dimensional problems. For example, the idealized fiber coupling problem can be modeled as minimization in a Gaussian cost landscape, which contains no couplings between the X and Y degrees of freedom; therefore, we can run quick 1D line searches in each variable rather than a 2D simultaneous optimization, significantly reducing the size of the search space.

Rather than the physical fiber coupling example above, we will now switch to a virtual cost function to facilitate demonstration of EMERGENT's subspace identification features. The code for this tutorial can be found in ``emergent/examples/subspace_identification``. Navigate to this directory and run main.py within an IPython console.

We analyze a simple network consisting of a control node implementing several virtual cost functions and a trivial device node which maps two virtual inputs, X and Y, to user-defined values. Two cost functions are implemented: ``control.cost_uncoupled`` and ``control.cost_coupled``. The former is simply a multivariate Gaussian with a relative factor of ½ between the widths in the X and Y directions; the latter also rotates the inputs by 30 degrees to create a coupling between X and Y.

Uncoupled optimization
~~~~~~~~~~~~~~~~~~~~~~~~
Let's inspect the uncoupled landscape with the grid_search algorithm:

.. code-block : python

   control.optimizer.optimize(method='grid_search', cost=control.cost_uncoupled, args={'plot':True})

To analyze couplings between degrees of freedom, run:

.. code-block :: python

   control.optimizer.covariance(cost = control.cost_uncoupled, method='grid_search')

This will generate and return a covariance matrix through sampling on a uniform grid; couplings can be identified through nonzero off-diagonal elements. In this case, we see that the off-diagonal elements are zero (within an error threshold due to finite sampling), so we can move away from the minimum then optimize the cost through two separate 1D optimizations:

.. code-block :: python

   control.actuate({'MEMS.X':0, 'MEMS.Y':0})
   control.optimizer.optimize(method='grid_search', inputs = [MEMS.input['X']], cost = control.cost_uncoupled)
   control.optimizer.optimize(method='grid_search', inputs = [MEMS.input['Y']], cost = control.cost_uncoupled)

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

   MEMS.inputs['X'].sequence = s
   control.clock.add_input(MEMS.inputs['X'])

Adding the input to the clock lets EMERGENT know that we want to run ``X`` in sequenced, not steady-state, operation. The last step is to start the clock with ``control.clock.start(T=0.5)''. Note that the time values in the sequence definition correspond to fractions of the total cycle, so with this cycle of 0.5 s, the MEMS will move to a position of 3 after 250 ms, then back to 0 after each new cycle starts.
