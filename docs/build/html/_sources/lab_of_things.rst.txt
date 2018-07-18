#######################
Control architecture
#######################

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
