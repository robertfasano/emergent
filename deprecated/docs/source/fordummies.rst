####################
EMERGENT for dummies
####################

This article doesn't focus on any specific feature of EMERGENT, but rather on
best practices and useful tricks in software engineering that will hopefully
prove useful to contributors. We will cover version control with Git, automated
documentation with Sphinx, and code visualization with pycallgraph.


pycallgraph
-------------
EMERGENT is a very large and feature-rich library which benefits greatly from
object-oriented design to minimize duplicate code. However, this same design can
make it complicated to understand exactly what EMERGENT is doing - during startup
alone, many functions spread across multiple files are executed. The pycallgraph
library offers a convenient way to visualize the entire process.


Logging and verbosity
----------------------
EMERGENT makes extensive use of the ``logging`` library, which enables printing
to the console with varying levels of priority: ``debug``, ``info``, ``warning``,
``error``, and ``critical``. Messages can be written with the corresponding function,
e.g. ``logging.info('message')`` prints ``'message'`` at the info level. In
``emergent.py``, we define the keyword argument ``-v`` or ``--verbose``, which
can be passed at runtime to set the level to ``debug`` so that all messages will
be shown. 
