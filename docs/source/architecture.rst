################
Architecture
################

The architecture underlying EMERGENT's scalability is a network of Node objects which abstractly represent the experiment under study. A typical building block, shown in Figure 1, is the triplet consisting of an Input node representing a state variable such as laser frequency or translation stage position, a Device node interfacing with an apparatus to actuate the input, and a Control node which measures some optimization function and attempts to minimize it by actuating the Inputs through the Device interface. 

An experiment could be as simple as a single triplet, such as our MEMS-based fiber coupling example, or it could consist of many triplets combined in a layered network, as shown in Figure 2. Interdependencies between experimental components are described by their vertical position - for example, the second-stage MOT at 556 nm depends on the first-stage MOT at 399 nm, so it occupies a higher layer. Independence between components is shown by separating them horizontally - for example, the autoAlign modules for slowing and cooling do not depend on one another at all and can thus be simultaneously optimized, so they occupy the same layer side-by-side.

In general, EMERGENT assumes initially that all variables of a single triplet are coupled, i.e. all off-diagonal elements of the covariance matrix of the cost function are nonzero. Therefore, if optimization is run within a layer containing N input nodes, the routine will be carried out in the fulll N-dimensional cost landscape. After the first optimization (or by manually specifying coupling strengths), EMERGENT will decompose the cost landscape into uncorrelated subspaces, for example decomposing an N-dimensional problem into two N/2 dimensional optimizations and thereby reducing the size of the search space.


A typical optimization workflow involves specification of start and stop layers; the routine will traverse the network layer-by-layer, starting by 