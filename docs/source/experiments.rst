##############
Experiments
##############

What is an experiment? This question has many answers, but across many fields
an experiment can be described as:
	• Preparation of an initial sample
	• Performing a sequence of actions on the sample
	• Measuring the result
In atomic physics, theorists love to track the state of an atomic system while
applying a series of unitaries; on the experimental side, it is useful instead
to track the state of the devices performing these actions. We suggest that any
experiment can be formally modeled through a functional M(T)=F[X(t<T)], or in
words: the measurement result at time T is a function of the state vector X at
all times leading up to the measurement. The state vector is a representation
of the individual states of all devices involved in the experiment. We are often
concerned with determining the state vector X(t) which minimizes or maximizes
M(T).

Steady-state optimization
===========================
To make this formalism more intuitive, let's first study an experiment with a
memoryless cost functional F[X(T)]], where the measurement depends on the input
state at time T but not the history. An example which is ubiquitous in AMO
physics is the fiber coupling problem, in which we want to steer a laser beam
into an optical fiber to maximize the light transmitted on the other end. This
is typically done by controlling the tip and tilt of two mirrors, where the more
distant mirror is used to translate the beam relative to the fiber tip while the
closer is used to adjust the angle. If only one mirror is adjusted, the measurement
will look like the Gaussian overlap of the beam and the fiber mode, and simple
hill-climbing algorithms can be employed to find the tip/tilt pair (x,y) which
maximizes the measurement M. This is an example of a convex optimization problem,
where the local minimum is also the global minimum.

.. image:: simplex_parametric.png
    :width: 49 %
.. image:: simplex_time_series.png
    :width: 49 %

:math:`\underline{x}=[  x_{1}, ...,  x_{n}]^{T}`

Time-dependent optimization
==============================
Turning now to a more complicated time-dependent cost functional, we consider
the problem of magneto-optical trapping, in which atoms are trapped at the zero
of a quadrupole magnetic field in a red-detuned laser beam. The problem can be
formulated as a memoryless cost functional depending on parameters such as the
field strength and laser detuning, but the trapping can be improved by adding a
time-dependent ramp such that the Doppler and Zeeman shifts keep the beam resonant
while the atoms cool. In this case we are tasked with determining not the
steady-state parameter values but instead the ramp shape which maximizes the
number of trapped atoms. Algorithmic optimization of atom cooling has been
achieved through parameterized ramps, where each of the d inputs x(t) is stepped
discretely through N steps (t1,...,tN); the N setpoints of each parameter are used
as inputs into a regressor which interpolates the Nd-dimensional cost landscape
to search for a minimum. Unlike the simple fiber coupling example, these problems
possess very complex, high-dimensional cost landscapes which may have many local
minima as well as high shot-to-shot noise, so deterministic convex solvers such
as gradient descent algorithms are unlikely to find the global minimum. A solution
is to use stochastic optimization algorithms, such as differential evolution or
stochastic artificial neural networks. Here the objective is to model rather than
simply explore the cost landscape, and to use information gained in each cycle
to improve the determination of the global maximum.

For an example of a time dependent optimization problem, consider the 1D functional
F[x(t)]=int 1/(1+(1-xt)^2), which qualitatively reproduces the required behavior to
optimize a MOT - the functional is maximized for the ramp x=1/t. If we were naive
to the form of the cost function, we could algorithmically maximize the function.
We discretize the inputs as xi=x(ti) and compute the cost function as
sum_(1...N) 1/(1-xiti),
where tN=1. We'll initialize the state with a guess xi=1 for all i and run a
simplex algorithm to optimize the inputs.

In both the memoryless and time-dependent cases the general process is the same:
	1. The learner suggests a set of inputs
	2. The experiment prepares these inputs
	3. The cost function is assessed and the learner is updated
The only difference is in step 2. In the memoryless case, the inputs are
immediately prepared, whereas in the time-dependent case, the experiment executes
a series of steps according to the inputs.
