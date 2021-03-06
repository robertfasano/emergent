.. EMERGENT documentation master file, created by
   sphinx-quickstart on Tue Jul 17 17:56:11 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

#######################
EMERGENT
#######################


Overview
-------------------
What is an experiment? Broadly speaking, an experiment is a process which seeks
to map out the relationship between a set of knobs and some measurable signal.
Surprisingly many state-of-the-art experiments in modern science rely on grad students
turning knobs, often following some informal algorithm gleaned from their own experience.
I say this is surprising for two reasons. First, it is usually very simple to gain
computer control of some knob, like a voltage setpoint or laser frequency. Second,
there exist many powerful, often open-source, algorithms which can find a set of
independent variables which extremizes an independent variable, and given computer
control of your experiment, it is not too difficult to hook up the knobs to the
algorithm to optimize your experiment. However, although it is simple to algorithmically
optimize a simple problem like pointing a laser beam into a waveguide, it is not
so simple to control a large experiment for a host of reasons:

* As the number of input variables increases, more and more sophisticated algorithms are needed to explore the parameter space.
* Controlling many devices from a centralized program quickly leads to tangled, unsalvageable code if scalability is not considered.
* Many experiments have coupled degrees of freedom, where the optimum position of one knob depends on another.

We wrote EMERGENT to attempt to solve these problems.

EMERGENT (Explorative Machine-learning EnviRonment for Generalized Experiments of Networked Things) is a library featuring device drivers and abstract classes allowing
universal autonomous control of laboratory experiments. The library was written based on the main belief that science progresses quickest when experimentalists
are free to spend as much time thinking and as little time turning knobs and
writing code as possible.

Introduction
---------------
What is an experiment? Broadly speaking, an experiment is a process which seeks
to map out the relationship between a set of knobs and some measurable signal.
Sometimes this relationship can be very simple, such as a linear dependence between
a knob position and a voltage. However, many experimental outcomes depend on the
simultaneous states of many, possibly coupled and/or nonlinear, degrees of freedom,
and optimization of the outcome can be incredibly difficult. An example is the
magneto-optical trap (MOT), a ubiquitous workhorse in atomic physics. The number
of atoms a MOT can capture depends partly on the magnetic field strength and the
laser frequency, and any attempt to optimize a MOT will quickly show that these
two variables are coupled, i.e. any adjustments to one knob will generally change
the optimal position of the second. In order to optimize the MOT, the experimentalist
must adjust both knobs iteratively until the atom number converges to an optimum value.

This simple example is just the tip of the iceberg: atom number generally depends
on other variables such as the atomic velocity distribution and beam alignment, and
so any two-dimensional optimization is unlikely to find the "true" maximum. But since
our time is limited and the complexity of the optimization grows quickly as we
consider more and more knobs, we typically turn them one or two at a time, content
with locally-maximal yet globally-subpar results.

EMERGENT aims to solve this problem by offering a simple framework for automated
exploration of many-dimensional parameter spaces. Many algorithms specifically
suited for this task are available in open-source libraries, and EMERGENT provides
a simple syntactic structure to leverage these algorithms to optimize your own
experiment. This is accomplished through three class modules: the Input, Thing,
and Hubs. Input nodes are simple structures which only serve to represent
the state of some experimental knob. Things are the glue between EMERGENT
and device APIs that can change physical variables in the lab. Lastly, Hub
nodes measure experimental outcomes and issue commands to connected Things to
optimize the result.
