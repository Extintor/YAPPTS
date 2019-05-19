# YAPPTS
Yet Another Python Protobuf Tile Server 

A production grade MVT protobuf Tile Server.

[![codecov](https://codecov.io/gh/Extintor/YAPPTS/branch/master/graph/badge.svg)](https://codecov.io/gh/Extintor/YAPPTS)
[![Build Status](https://travis-ci.org/Extintor/YAPPTS.svg?branch=master)](https://travis-ci.org/Extintor/YAPPTS)

Originally lousy based in [postserve](https://github.com/openmaptiles/postserve).

Single threaded Python MVT Protobuf tile Server that functions using the ST_AsMVT and ST_AsMVT_geom funtions from PostGIS.

It is intentionally designed to be single threaded but can be made multithreaded change from 1 to the number of deisred 
threads. Beware pool conection problems.