#################
Getting started
#################

In this tutorial, we cover installation and startup of EMERGENT, then introduce its
various features by running the ``example`` network.

Installing EMERGENT
---------------------
The latest version of EMERGENT can be found at https://gitlab.com/emergentlab/emergent.
You can download it using Git: just run

.. code-block :: python

   git clone https://gitlab.com/emergentlab/emergent.git

in the directory of your choice. This will create a folder called ``emergent`` which
contains documentation and installation scripts, as well as a nested folder also
called ``emergent`` containing the source code.

Before installing, make sure you have the latest version of Anaconda installed.
To avoid dependency conflicts with other libraries, we'll create a new virtual
environment to install EMERGENT in. Open Anaconda Prompt and run

.. code-block :: python

   conda create --name emergent

Follow the prompt to create the new environment, then activate it with ``conda activate emergent``.
Now navigate to the ``emergent`` folder wherever you downloaded it and install using

.. code-block :: python

   python setup.py install

The installation script will check to make sure that you have all of the necessary
packages, which should be guaranteed by having the latest version of Anaconda. It
will also create a shortcut to launch EMERGENT in the ``emergent/emergent`` directory.


Running EMERGENT
------------------
There are a few ways to start the code, all from the ``emergent/emergent`` directory.
On Windows, the simplest way is to click the shortcut or run the batch script ``run.cmd``
to run the launcher. Alternately, you can start the launcher from the command line:

.. code-block :: python

   python launcher.py

When the launcher opens, it will prompt you to choose one of the networks from the
``emergent/emergent/networks`` folder - choose the ``example`` network for now. You
can also specify an IP address and port; this is only necessary if you want to run a
single EMERGENT session across multiple PCs. To start the session, click Launch.
You should see an IPython console open, and a moment later the EMERGENT window will
appear.

You can also bypass the launcher if you know which network you want to run; just open
an IPython session and call

.. code-block :: python

   %run main <network> --addr <addr> --port <port>

The first argument should be replaced with the network name as it appears in your
``emergent/emergent/networks`` folder. The second and third arguments are optional and
allow you to specify the IP address and port for decentralized applications.


State representation and actuation
------------------------------------
EMERGENT keeps track of the state of your experiment through a State class which is
essentially a nested dictionary. The top-level components are Networks, which represent
clusters of Hubs. A Hub is a self-contained chunk of your experiment that is responsible
for measuring a signal and issuing commands to connected Things in order to optimize the result.
Each Thing possesses one or more Inputs, which represent your experiment's "knobs": quantities
like currents or voltages, laser frequencies, mirror positions, or other controllable
variables that affect the outcome of the experiment.

All of this information is encoded within the Network class, and visible on the Network
panel at the left side of the EMERGENT window. To access a Hub,
query it by name from the ``Network.hubs`` dictionary. Then, you can check its overall
state:

.. code-block :: python

   hub = Network.hubs['autoAlign']
   print(hub.state)

The returned State object gives you the current positions ``X`` and ``Y`` of a virtual
mirror used to steer a beam into an optical fiber. To update the position of one of
these inputs, double click its value in the Network panel, enter a new value, and hit the
Enter key. If you check the state of the ``autoAlign`` hub again, you should see that it
has updated to your value.

You can also issue commands directly from the command line to gain more insight about
how EMERGENT works. Let's command the ``X`` input to move to a
new position specified by a state dict, then check the result:

.. code-block :: python

   hub.actuate({'MEMS': {'X': 1.5}})
   print(hub.state)

The ``hub.actuate()`` method distributes your command to the different Things referenced
by the state dict, which each change the physical state in the lab. Afterwards, each Thing
updates the Hub with its current state and emits signals to update the user interface.


Experiments
------------
An EMERGENT experiment is just a Python method which moves to a state and measures the
result with any sequence of events you want. Let's take a look at a simple experiment
defined in the TestHub class in ``emergent/emergent/networks/example/hubs/testHub.py``,
which simulates measurement of power transmitted through an optical fiber:

.. code-block :: python

  @experiment
  def transmitted_power(self, state, params = {'sigma_x': 0.3, 'sigma_y': 0.8, 'x0': 0.3, 'y0': 0.6, 'noise':0}):
      self.actuate(state)
      x=self.state['MEMS']['X']
      y=self.state['MEMS']['Y']
      x0 = params['x0']
      y0 = params['y0']
      sigma_x = params['sigma_x']
      sigma_y = params['sigma_y']
      power =  np.exp(-(x-x0)**2/sigma_x**2)*np.exp(-(y-y0)**2/sigma_y**2) + np.random.normal(0, params['noise'])

      return -power

First note the ``@experiment`` decorator that precedes the method definition. This
decorator labels experiments so that EMERGENT can add them to the GUI. It also does
some features behind the scenes, like optionally repeating an experiment several times
to gather statistics and improve signal-to-noise. Second, let's look at the arguments
to the method. We pass a state dict corresponding to the state whose result we want to
measure, and a parameter dict containing any parameters we might want to change from
experiment to experiment. In this case, ``params`` contains the center position and
scale of a two-dimensional Gaussian, as well as a constant noise term that can be added
to simulate real experiments. The experiment returns this noisy Gaussian with a minus
sign – EMERGENT minimizes the results of experiments, so we include this extra factor of
-1 so that our signal is maximized after optimization.

You can run an experiment from the Run tab of the central panel. When you click any
of the inputs in the Network panel, EMERGENT scans the parent Hub and loads all
experiments into the drop-down menu. Choosing any of them will automatically load
experimental parameters into the table below; by default, EMERGENT uses the parameters
from the function definition, but you can save new default parameters with the
Experiment -> Save parameters menu option. Let's choose a simulated noise level of
0.05 (5%), 2 cycles per sample, and select 128 iterations using the slider.

When you start the experiment by pressing the Go! button, you'll see a new item
appear in the Tasks table. Double clicking it opens a window where you can plot the
experimental result vs. time. Since we chose 2 cycles per sample, we also have error
bars on each point.

You can change any of the inputs freely in Run mode, and the change will be executed
at the start of the next experiment. Try changing the inputs a few times and
checking the results of a single-shot experiment - can you manually tune the inputs
to improve the power? You will find that the result
is maximized when the ``X`` and ``Y`` inputs match the center position of the Gaussian
defined in the ``params`` dict.

Optimization
--------------
The Optimize tab of the central panel lets you hand over control to EMERGENT to
tune the inputs to maximize an experimental result. The left drop-down menu contains
a list of algorithm choices whose parameters you can set in the table below. The right
menu lets you choose experiments just like in the Run panel.

Lets start off with a simple grid-search. This isn't an optimization so much as a
brute-force exploration – a uniform sampling of points spanning the bounds set by the
Min and Max values for each input in the Network panel. Make sure both the ``X`` and
``Y`` inputs are selected in the Network panel, then choose 30 steps and press the
Go! button. You'll see the state update rapidly in the Network panel as EMERGENT
samples the parameter space, and after it finishes its exploration it will return to
the best point found, which should be very close to the center position of the Gaussian
specified in the experimental parameters table. Double clicking the entry in the Tasks
panel will show you similar information to before, but will also let you visualize the
2D space in the Algorithm tab.

You can use grid searches to rapidly sample low dimensional parameter spaces. Want to
measure number of trapped atoms in a MOT vs. laser frequency? A grid search is great for this.
Want to simultaneously optimize laser frequency and intensity as well as magnetic field strength?
Because the number of points in a grid search scales exponentially with the number of dimensions,
you'll be waiting a while. Luckily, EMERGENT has better options for you. Choose the
GaussianProcessRegression algorithm from the dropdown menu and try running it. This is
a more sophisticated algorithm which builds a model of the parameter space and chooses
points to sample to minimize both the modeled experimental result and the corresponding
uncertainty. When you open the plotting window for this task, the Algorithm tab will
display the model based on sampled data instead of the raw data. Gaussian process regression
comes with computational overhead that renders it inefficient for fast, low-dimensional experiments,
but it will often converge in fewer iterations than other algorithms, making it valuable when
either the dimensionality or the experimental duration is high.

Servos
-------
The Servo tab lets you run digital PID to keep the result of an error function close
to zero. Error functions are defined similarly to experiments, but are labeled with a
different decorator. Let's look at one in the ``testHub``:

.. code-block :: python

  @error
  def error(self, state, params = {"cycle delay": 1, "drift rate": 1}):
      self.actuate(state)
      thing = list(state.keys())[0]
      input = list(state[thing].keys())[0]
      if not hasattr(self, 'start_time'):
          self.start_time = time.time()
      setpoint = params['drift rate']*(time.time()-self.start_time)
      e = setpoint - self.state[thing][input]
      time.sleep(params['cycle delay'])

      print('Setpoint:',setpoint)
      return(e)

This particular function simulates a linear drift in a setpoint, where we want to change an input
at a constant rate specified by ``params['drift rate']`` to minimize the absolute value
of the result. The bandwidth will be limited by your processor (and other competing processes)
so it won't be sufficient for demanding tasks like laser frequency stabilization, but is
more than suitable for slower applications such as temperature control. The repetition rate
of this simulated process is determined by ``params['cycle delay']``, and you'll notice that
the servo performance improves with shorter delays.


Watchdogs
---------
By now, I'm assuming that you have:

1. Worked through the above examples
2. Sprinted into the lab to automate your entire job
3. Kicked back at your desk with a stack of backlogged papers
4. Returned to the lab to find that your laser unlocked halfway through the experiment
5. Wished you just stayed in the lab instead of trusting EMERGENT

EMERGENT's optimization routines are powerful, but not enough to get good results
when the experiment isn't running properly! Luckily, you can set up automated
watchdogs to make sure everything is running smoothly. The Watchdog class looks like
this:

.. code-block :: python

  class Watchdog(ProcessHandler):
      def __init__(self, parent, experiment, threshold, input_state = None, name = 'watchdog'):
          super().__init__()
          self.parent = parent
          self.experiment = experiment        # experiment to run to check lock state
          self.threshold = threshold
          self.input_state = input_state
          if self.input_state is None:
              self.input_state = parent.state
          self.name = name
          self.value = 0
          self.threshold_type = 'lower'
          self.value = 0
          self.state = 0
          self.signal = WatchdogSignal()
          self.enabled = True
          self.reacting = False

          ''' Set up sampler object '''
          experiment_params = recommender.load_experiment_parameters(self.parent, experiment.__name__)
          self.sampler = Sampler('Watchdog',
                            self.input_state,
                            self.parent,
                            self.experiment,
                            experiment_params)
          self.sampler.skip_lock_check = True

      def check(self):
          ''' Private method which calls self.measure then updates the state '''
          value = self.measure()
          if self.threshold_type == 'upper':
              self.state = value < self.threshold
          elif self.threshold_type == 'lower':
              self.state = value > self.threshold
          self.signal.emit({'state': self.state, 'threshold': self.threshold, 'value': value})
          if not self.state:
              log.info('Watchdog %s is reacting to an unlock!'%self.name)
              self._run_thread(self.react, stoppable=False)
          return self.state

      def measure(self):
          return -self.sampler._cost(self.parent.state, norm = False)

      def react(self):
          ''' Add custom reaction here '''
          self.confirm_lock()

      def confirm_lock(self):
          return

      def reoptimize(self, state, experiment_name):
          self.enabled = False
          self.reacting = True
          self.parent.optimize(state, experiment_name, threaded = False, skip_lock_check = True)
          self.enabled = True
          self.reacting = False

You can create a new class which inherits
from ``Watchdog`` and reimplement the ``measure()`` method to return the result of
something you want to track, like the power transmitted through an optical fiber
(does this sound familiar?). At the start of each experiment, the private ``_measure()``
method is called to measure the tracked signal and decide whether the experiment
is working or not based on the result. You can reimplement the ``react()`` method to
do something when the experiment fails: for example, if fiber-coupled power dips
below a threshold, you could have ``react()`` launch an optimizer to realign the
fiber. Any experimental results obtained during an unlocked state are flagged and disregarded.
