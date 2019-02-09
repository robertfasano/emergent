##################
Network creation
##################

So you've worked through the examples and have a pretty good idea of what EMERGENT
is capable of, at least in a simulated experiment. This page will guide you
through the process of setting up your own network to run a real experiment.

Creating a new network
------------------------
In order to create a new network for your experiment, simply run

.. code-block :: python

   python new.py name

from the ``emergent/emergent`` directory, where ``name`` can be replaced with
anything you'd like (restricted by your operating system's directory naming
conventions). The script will create a folder in the ``emergent/networks/``
directory and automatically create the required subdirectory structure and some
template Python files.


Network declaration syntax
---------------------------
If you open your new network's ``network.py`` script, you'll see an empty ``initialize``
method which takes a Network object as an argument. When you run EMERGENT, ``main.py``
creates a Network instance and passes it into this function, and any nodes you
define here will be instantiated and assigned to the network. For example, in the
demo network we explored in Getting Started, the ``initialize`` method includes
the following instructions:

.. code-block :: python

	from emergent.networks.demo.hubs import DemoHub
	from emergent.networks.demo.things import DemoThing

	def initialize(network):
	    hub = DemoHub('hub', network = network)
	    thing = DemoThing('thing', params = {'inputs': ['Z']}, parent=hub)

	    ''' Add hubs to network '''
	    for hub in [hub]:
	        network.add_hub(hub)

The important steps include above are:

1. Import the Hubs and Things you need, either from the global emergent/hubs or emergent/things folders or from your network's local folders.
2. Instantiate your hubs within the initialize() method with the network as an argument.
3. Instantiate Things, pass in relevant parameters, and reference them to their respective Hubs with the ``parent`` keyword argument.
4. Add all Hubs to the network.

Importing templates
----------------------
Before we dive into creating a network from scratch, let's try importing
pre-built networks from EMERGENT. For example, let's say we want to add an autoAlign
Hub. Luckily for us, this exists in the ``emergent/networks`` folder, so instead of
defining the whole thing we can add it by importing it, then adding a call to its
initialize method within our own initialize method:

.. code-block :: python

	from emergent.networks.demo.hubs import DemoHub
	from emergent.networks.demo.things import DemoThing
	from emergent.networks.example import network as nw

	def initialize(network):
	    hub = DemoHub('hub', network = network)

	    thing = DemoThing('thing', params = {'inputs': ['Z']}, parent=hub)

	    ''' Add hubs to network '''
	    for hub in [hub]:
	        network.add_hub(hub)

	    ''' Load other network '''
	    nw.initialize(network)


Creating Hubs
---------------


Creating Things
-----------------
