# Software for Testing Adaptive Radar Scanning Strategies (STARSS)
Git repository for studying diffent aspects of the precipitation processing chains.

The type of precipitation, the type of radar, the chosen processing chains, all can have an effect on how well a network of weather radars can see different kinds of precipitation,
The studied meteorological events only occur once, and can only be measured once.
The effects different radar scanning strategies, different processing chains, or different weather radars could have had cannot be quantified using only real data. 
Simulations are required for a robust analysis to help improve the early detection and monitoring of atmospheric threats.

This software does just this.
By using simple models for the preciptiation, the radars, their measurements, and their processing, a modular programme is built with which extensive testing can be done. 
So far, only a model of rain has been implemented, although different precipitation types can easily also be implemented.
The software is made in C to be highly portable. 
One only requires a compiler (gcc), common to most computers, and some experience with the command line to quickly run and test the system performance under new network geometries, processing chains, or precipitation intensities.

Download the repository, and use the instruction manual (instruction\_manual.txt) to generate the figures as a first introduction to the capabilities of this software. 


 This work is part of project SMARTER which is funded by the Dutch Research Council (NWO) under the OTP 19959 grant.
