################
Architecture
################

The architecture underlying EMERGENT's scalability is a network of Node objects
which abstractly represent the experiment under study. A typical building block,
shown in Figure 1, is the triplet consisting of an Input node representing a state
variable such as laser frequency or translation stage position, a Device node
interfacing with an apparatus to actuate the input, and a Control node which
measures some optimization function and attempts to minimize it by actuating the
Inputs through the Device interface.

.. image:: network_basic.svg
   :align: right

While this simple network model suffices for compact experimental tasks such as
automated fiber alignment, ongoing work will be directed at modeling more complex
experiments, where the outputs of control nodes can be used as the inputs to other
layers.

Full documentation for the Node class and its offshoots can be found in the
links below.

.. toctree::
   :glob:
   :maxdepth: 4

   ./architecture/node
   ./architecture/input
   ./architecture/device
   ./architecture/control
