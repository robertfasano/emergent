#######################
Examples
#######################

The following examples should get you started with labAPI.

File structure
-------------------
labAPI is a library featuring device drivers and abstract classes allowing
universal control of laboratory experiments. However, actual experimental control
is not done in labAPI, but in a separate library implementing
labAPI's features for a specific use case.

In this tutorial, we will specifically work with the library controlling the NIST ytterbium portable optical lattice
clock experiment, which is called "portable". This library resides in the same
folder as labAPI, which is important for relative pathing.

Version control
-----------------
Git is used to track changes throughout development of labAPI. The repository
location is gitlab.nist.gov/rjf2/labAPI.

Installation
~~~~~~~~~~~~~~
The library can be installed on a new computer by cloning from the repository.
In the console, navigate to the folder which will contain labAPI and run

.. code-block:: python

   git clone gitlab.nist.gov/rjf2/labAPI.git

You may be prompted for login credentials, after which the repository will
be cloned to the local folder.

Pulling from the remote repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To update a local repository with changes on the remote repository, just run
``git pull``. In some cases, multiple remote repositories may coexist across Git platforms;
currently, a "master" copy is stored on the NIST GitLab service, while a separate
copy is stored on GitHub. To specifically pull changes from GitHub, run

.. code-block:: python

   git pull github master

The first argument specifies the remote named "github", while the second specifies
the branch named "master".

Pushing to the remote repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If you want to update the remote repository with changes made on the local
repository, first stage your changes with ``git add filename``, where filename
is specified relative to the current path. You can stage all current changes with
``git add -A``. Next, commit changes to each file with a helpful message, e.g.

.. code-block:: python

   git commit -m "Fixed bug in function bar()" foo.py

Once all changes are committed, you can push to the remote by running ``git push``.

Launching the code
-------------------
To launch the control code, first navigate to the portable directory. Once there,
we will launch the control code within an IPython console by calling

.. code-block:: python

   ipython
   %run main

There will be a short delay as the code initializes all Hubs and connects to
their child Devices. Connection failures will be printed to the console. Afterwards,
the GUI will open, and the user can control the experiment either through the
graphical interface or directly from the command line.




Adding a new Hub
-----------------
This example demonstrates how to add a new Hub to the portable project to control
automated fiber alignment for the magneto-optical trap.

Creating the Hub
~~~~~~~~~~~~~~~~~~~~
We will first create a new file in portable/gui/hubs called autoAlignHub.py.
We define a new class inheriting from the abstract Hub base class in labAPI/archetypes/Hub.py:

.. code-block:: python3

  from labAPI.archetypes.Hub import Hub

  class autoAlignHub(Hub):
      def __init__(self, engine):
          Hub.__init__(self, engine=engine, name='autoAlign')

Linking the Hub
~~~~~~~~~~~~~~~~~
Now we need to add the Hub to the main control code in portable/gui/main.py,
which ensures that both the Python backend and the QML frontend can access it.
We simply import the new hub and define it in main.py; upon initialization,
the hub will be automatically linked with the Application layer:

.. code-block:: python3

    from PyQt5.QtQml import QQmlApplicationEngine
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QCoreApplication
    import sys
    import os
    char = {'nt': '\\', 'posix': '/'}[os.name]
    sys.path.append(char.join(os.getcwd().split(char)[0:-2]))
    from hubs.MOTHub import MOTHub
    from hubs.autoAlignHub import autoAlignHub
    app = QCoreApplication.instance()
    if app is None:
        app = QApplication(sys.argv)         # Create an instance of the application
    engine = QQmlApplicationEngine()    # Create QML engine

    ''' Initialize device links '''
    mot = MOTHub(engine)
    autoAlign = autoAlignHub(engine)

    engine.load("main.qml")                     # Load the qml file into the engine
    window = engine.rootObjects()[0]
    window.show()

    ''' Retrieve hub handles from the engine and initialize default values '''
    for hub in engine.hubs:
        hub.retrieve_handles()
        hub.populate_listModel()


By passing in the engine when initializing the hub, one line of code is all it takes to register the Hub internally with both the Python and QML frameworks - all of the difficult stuff is done under the hood.

We also need to create a new gui Element for the Hub. This only takes one added definition in portable/gui/main.qml:

.. code-block:: python3

        Elements.Element{
            name: "autoAlign"
            objectName: "autoAlignElement"
            x_pos: 0.2
            y_pos: 0.2
            device: autoAlign
        }

In this definition, the "name" parameter is the display name that will be shown in the GUI,
the "objectName" is an internal reference within the QML engine, "x_pos" and "y_pos"
set where the clickable object will appear onscreen, and "device" corresponds to what
we called the Hub object when we added it to main.py.

Now if you run main.py, the Hub should appear onscreen wherever you chose to
locate it, but there are no devices connected yet. Continue on to the next example
to learn how to add devices.

Adding a new Device
---------------------
For this guide I assume that you already have control code for an experimental
device inheriting from the Device archetype. In our case, we will add a PicoAmp
MEMS driver to control the alignment of the slowing beam. In the Hub file created
in the last example, autoAlignHub.py, we can simply add the device like this:

.. code-block:: python3

    from labAPI.devices.labjackT7 import LabJack
    from labAPI.archetypes.Hub import Hub
    from labAPI.devices.picoAmp import PicoAmp

    class autoAlignHub(Hub):
        def __init__(self, engine):
            Hub.__init__(self, engine=engine, name='autoAlign')

            self.labjackSlowing = LabJack(devid='470016970')
            self.MEMS_slowing = PicoAmp(name='MEMS_slowing', connect = False, parent = self, labjack = self.labjackSlowing)

            self._connect()

Adding Devices is as simple as instantiating them within the hub with the
argument "parent=self", which adds them as children to the Hub. Note that here
the PicoAmp is a Device, whereas the LabJack doesn't inherit from the Device class.
When Devices are initialized, they automatically read in from a settings file
linked to their name (e.g. portable/settings/MEMS_cooling.txt) to determine
their initial state and set other important variables. We create this file below:

.. code-block:: json

    {"default": {"X": {"value": -60, "type": "state", "index":0, "min":-80, "max":80,"gui": 1},
                 "Y": {"value": 0, "type": "state", "index":1, "min":-80, "max":80, "gui": 1}}}

The first key given to the dict is the setpoint, of which the only one is currently
"default" (more setpoints can be saved with the Device._save(setpoint) function).
Here we have only two parameters, "X" and "Y", which are state variables, which
means they are loaded into the Device's state vector and made accessible to the
Optimizer. The "index" defines each state variable's location within the overall
state vector of the Hub: other Devices should use different indices. The "value"
gives the last saved state of the Device, while the "min" and "max" provide
thresholds limiting the actuation range. Lastly, the "gui" element is a bool
determining whether or not the parameter will be shown on the GUI.

That's it! The new Devices should appear on the Hub and any parameters with
"gui":1 will be accessible through the control interface.

Accessing attributes from the console
--------------------------------------
The IPython console can be used simultaneously with the GUI, allowing more
flexibility to the user. Any Hub can be accessed with its name defined in its
``Hub.__init__()`` function; for example, the autoAlign hub created above can
be accessed through the variable ``autoAlign``. Any attributes of the Hub can
then be accessed in a straightforward manner; for example, the MEMS for slowing
fiber alignment can be accessed through the variable ``autoAlign.MEMS_slowing``.

Running functions
-------------------
The built-in methods of a Device or Hub can be called through the console as well.
For example, to create a square wave on the slowing MEMS, we can run

.. code-block:: python3

  autoAlign.MEMS_slowing.wave(A,f)

where ``A`` and ``f`` are the amplitude and frequency respectively. The ProcessHandler
archetype makes it easy to run any function in parallel using either a thread or a process;
for example, you can instead run

.. code-block:: python3

  autoAlign._run_thread(autoAlign.MEMS_slowing.wave, args = (A,f))

to run the square wave in parallel, allowing non-blocked access to the console.
This will automatically pass in a ``stopped()`` function which will return a
bool to allow early termination of the threaded function; the threaded function
should include checks of stopped() in each loop pass if early termination is
desired. In order to quit the threaded function, run

.. code-block: python3

  autoAlign._quit_thread(autoAlign.MEMS_slowing.wave)

Note that, in the current implementation, the _quit_thread() method searches
through the list of currently running threads in the Hub and terminates the first
one matching the specified function (``autoAlign.MEMS_slowing.wave``).
