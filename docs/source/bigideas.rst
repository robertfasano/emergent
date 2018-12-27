#######################
In-depth guide
#######################

Before reading this, you should have worked through the examples in the Getting
Started page to familiarize yourself with the basic concepts behind EMERGENT. This
guide fleshes those concepts out, explaining how to modify EMERGENT to fit your
needs as well as the underlying design philosophy. For many parts of this page,
I will contrast EMERGENT to earlier scripts accomplishing similar tasks.

Optimization
-------------------
History
~~~~~~~~~
EMERGENT's earliest ancestor was a standalone Python script which offered keyboard
control of piezoelectric mirror mounts on an in-vacuum optical cavity. Flirting
with the idea of automatic alignment, we first implemented a grid search method –
a brute-force search over the 4D parameter space of the two pairs of knobs. After
this proved to be too slow, we implemented a gradient-based fiber alignment routine
on a test setup consisting of an input fiber, steering mirror, and output fiber.
This worked so well that we decided to implement it on a real laser system, where
we ran into trouble: the high-frequency whine of the piezo mounts caused the laser
to unlock from its doubling cavity, so we had to add an additional delay between
actuations to let the laser reacquire lock! This made each iteration take long enough
that we needed a more intelligent algorithm, which we found in the Nelder-Mead (simplex)
method, which, after a bit of tuning, became the new standard for fiber alignment.

The great performance of the simplex method motivated us to apply the fiber-coupling
technique to other parts of our lab. We purchased several high-bandwidth MEMS mirrors
and wrote the basic driver code to set mirror positions through the voltage control board.
Next, we copy-pasted in the simplex code, made a few revisions, and were good to go! Then
we thought: since we could use the simplex routine for alignment on two different mirror
mounts, could we use it with other products? Translation stages? Motorized rotation
mounts? Could our whole lab run on the simplex routine?

The essential first step to developing EMERGENT was ensuring scalability by removing
the need to copy-paste the algorithm into every device driver - instead, we would
write the algorithm in a hardware-agnostic way and include a method in each device
driver script to translate the control command formats specified by manufacturers
into a standardized format used by the algorithm. This meant that any of our algorithms –
grid search, gradient descent, or simplex – could be used to optimize any device, which
at the time was limited to piezoelectric and MEMS mirror mounts. As our stable of
algorithms grew to include more sophisticated methods, like Gaussian process regression,
differential evolution, and neural networks, we extended the capabilities to work on
multiple devices, towards a goal of optimizing many-parameter experiments!

Architecture
~~~~~~~~~~~~~~
Through several rounds of refinement, the system above grew into a three-layer
architecture.

The physical end is represented by a Hub which issues commands to a
Thing to make physical changes in the lab, like steering a mirror. States are represented
through nested dictionaries using the real values of the parameters that are being
set – for example, a 60 V MEMS mirror setpoint could be represented through the dict
``{'MEMS': {'X': 60}}``.

The virtual end is represented by an Algorithm which is entirely unaware of the
physical task it's accomplishing. The algorithm "lives" in a normalized parameter
space spanning 0 to 1 for each degree of freedom, and has the simple task of suggesting
a new point within these bounds based on information gained from previous points.

The Sampler class unifies these two ends. Before running an optimization, a
Sampler is initialized with the experiment and algorithm to run, any relevant
parameters, and user-defined bounds determining the scaling between the physical and
normalized coordinate systems. At each step of the optimization, the Algorithm
suggests a new normalized point and the Sampler converts it to a real experimental
state and passes it to the Hub for actuation.


Monitoring
------------
Not too long before EMERGENT's development started, we underwent an eight-month
measurement campaign between our optical lattice clock and other optical clocks
in Boulder, CO, resulting in improved measurements of the transition frequencies for
all three atomic species. For this measurement to be rigorous, we would need a way
to know exactly when our clock was fully operational ("locked") so that we could
reject bad data. Unlocks compromise the accuracy of the clock, and can come from
a number of sources: unlocks of lasers from optical cavities, loss of fiber-transmitted
power, other other equipment failure. We built a standalone monitoring script to
solve this problem with a very simple method:

1. Once per second, an ADC measures about 16 signals from different parts of the lab.
2. Logical comparisons are made between the measured signals and user-defined thresholds.
3. Data is marked as "locked" or "unlocked" based on the overall comparison.

To fulfill the EMERGENT design philosophy of scalability, we decided to overhaul
this script by breaking it up, from a single centralized monitoring engine to
a number of Watchdog class instances, each of which are associated with a signal
in the lab, such as fiber-transmitted power. Before EMERGENT runs an experiment,
it first commands all Watchdogs to report their state. If any are unlocked, they
will call their ``react()`` method to attempt to reacquire lock in a user-defined way.
This redesign accomplishes a few things:

1. Monitoring can be split across multiple ADCs or even across networked PCs.
2.
