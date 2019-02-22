#######################
EMERGENT
#######################

Introduction
---------------
Development of EMERGENT began at NIST in 2018. Its earliest ancestors were
standalone Python scripts to automate various tasks in the lab, such as

* Steering laser beams into optical fibers to maximize transmitted power
* Automatic locking of lasers to optical cavities
* Monitoring of critical experimental variables

Around this time, several research groups published exciting applications of
machine learning to optimization of cold-atom experiments. Boasting
performance exceeding human capabilities, these results hint at a disruptive
trend towards automation in experimental physics. We brainstormed a list of tasks
that an automated experiment must be able to do and quickly began development of
a framework including:

* Machine-learning-based modeling and optimization of complex, many-parameter experiments
* A reactive monitoring system which can detect and resolve experimental problems, such as
  cavity unlocks or laser power drifts
* Persistent storage of every bit of data collected by the experiment
* Support for decentralized experiments controlled by multiple networked PCs

We called this framework EMERGENT: Experimental Machine-learning EnviRonment for
GEneralized Networked Things. Dissecting the name, we arrive at two concepts
driving recent tech hype:

* The Internet of Things is a term for a network of different devices, such as
  lasers, motorized mirror mounts, and voltage and current sources, which can
  exchange data and be controlled by a central PC.
* Machine learning is the application of powerful statistical algorithms allowing
  computers to solve tasks without explicit programming.

Combining these two concepts, EMERGENT provides a simple framework for controlling
your Lab of Things, and then lets you hand over the keys to an intelligent system
which can run even the most complicated of experiments.

Because of the potential for scientific advancement, we're committed to keeping
EMERGENT open-source and growing it to fit the needs of the scientific community.
If you're interested in deploying it in your lab, please read the Getting Started
section. Feel free to contact us for troubleshooting, help setting up your
automated experiment, or feature requests.

Table of Contents
-------------------
.. toctree::
   :glob:
   :maxdepth: 2

   self
   gettingstarted
   architecture
   optimization
   reference
