# EMERGENT
EMERGENT (Experimental Machine-learning EnviRonment for Generalized Networked Things)
is a Python library featuring thing drivers and abstract classes seeking to solve 
two main problems in experimental physics:
* Lack of a standard Internet of Things framework for connected laboratories
* Over-reliance on manual optimization of experimental degrees of freedom

In contrast to previous experimental control software, which focus largely on 
data acquisition and analysis, EMERGENT was built around the idea of completely 
autonomous optimization systems, which can be triggered in response to monitored 
signal changes. Today, EMERGENT is split across four main modules:
* core: an internet-of-things framework for controlling many devices and running experiments
* monitor: a data acquisition and monitoring system which can detect and resolve failures
* optimize: a generic optimization framework allowing simple deployment of one or more algorithms to an experiment
* artiq: an interface for running experiments with timing performed by ARTIQ hardware

EMERGENT was developed in the Optical Frequency Measurement Group at NIST to support 
development of a portable optical lattice clock. Non-commercial usage by other individuals or 
groups is allowed under the [Creative Commons license](https://creativecommons.org/licenses/by-nc/3.0/).
Please contact us regarding commercial use. If you use EMERGENT in your research,
please cite this repository.

For documentation, please reference the tutorials/modules folder.
