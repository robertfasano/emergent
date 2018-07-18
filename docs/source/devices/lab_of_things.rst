############
Lab of Things
############

Control code
===============

**The Lab of Things**
The Internet of Things is "a dynamic global network infrastructure with self-configuring capabilities based on standard and interoperable communication protocols where physical and virtual 'Things' have identities, physical attributes, and virtual personalities and use intelligent interfaces, and are seamlessly integrated into the information network" [Kranenburg, 2008].

* The **physical Things** in our network are devices with sensing and/or actuation capabilities.
* Physical Things are united into **virtual Things** which perform higher-level tasks. For example, the magneto-optical trap is controlled by a virtual Thing comprising many physical Things, such as mirror mount actuators, digital synthesizers, and photodetectors.
* The **attributes** of all physical Things, such as their positions or frequencies, are stored in a database alongside the attributes of virtual Things such as calibrated model parameters.
* **Standard and interoperable communication protocols** are implemented between each layer of the code, allowing higher-level governing functions to interface with base devices without explicit hard-coded knowledge of their characteristics.

Control architecture
---------------------------------------
We separate our control code into the following functional blocks:

* **Device**: a physical apparatus with sensing and/or actuation capabilities. The Device also possesses an interface for communication with higher layers.
* **ProcessHandler**: a class providing simple and standardized creation, termination, and analysis of threads and processes.
* **Optimizer**: a class containing common optimization and machine learning algorithms, including grid search, gradient descent, and Bayesian optimization.
* **Hub**: a virtual Thing comprising many base Devices to accomplish a macroscopic goal, such as magneto-optical trapping. Also contains an interface between the Python backend and QML frontend.
* **Database**: The states of all connected Devices are stored in a Database (currently spread across settings files in portable/settings).
* **Application**: the QML-based front-end allows simple access to important Device parameters. More sophisticated tasks can be executed through the IPython console.

The event-driven control flow is as follows:

#. **Event**: a Device parameter is changed either directly in the console or via the GUI
#. **State vector decomposition**: if the event is GUI-initiated, then the Hub overseeing the target lower-level device prepares a new target state vector, separates out the substate of the device, and passes it to the child Device.
#. **Actuation**: The Device.actuate(state) function is called to change the physical state of the device.
#. **Device state updating**: the state vector of the Device is updated. The appropriate params component is updated as well, and the params file is updated.
#. **Hub update**: the Device updates its parent Hub's parameters
#. **State vector preparation**: the Hub computes a new state vector based on the updated parameters
#. **Application update**: the Hub updates the GUI

Each functional block is described in detail as follows.

Device
~~~~~~~~~~~~~~~~~~~~~~~~~
The Device class communicates with two other architectural layers.
Upon instantiation, each Device's settings are loaded into memory from the
Database and stored in the Device.params dict; state variables are also stored
in the Device.state vector. The latter exposes the Device to the Hub layer,
which interacts with the Device via operations on its state vector. The Device
class includes the following methods:

* actuate
* load
* params_to_state
* save
* state_to_params

Hub
~~~~~~~~~~~~~~~~~~~~~~~~~
The Hub class interacts with the Application layer via methods to retrieve
handles of QML elements for Python-initiated GUI updates, as well as Qt slots
for GUI-initiated commands; it also interacts with the Device layer with methods
to push state changes to devices. The following methods are implemented in the Hub:

* actuate
* append_listModel
* populate_listModel
* retrieve_handles
* set_params

ProcessHandler
~~~~~~~~~~~~~~~~~~~~~~~~~

Optimizer
~~~~~~~~~~~~~~~~~~~~~~~~~

Application
~~~~~~~~~~~~~~~~~~~~~~~~~
