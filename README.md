Python Link Budget Calculation & Management
===========================================

This software package is meant to replace the manual-intensive
spreadsheet method.  This package is intended to permit the following
major changes in our methodology:

 * Use of configuration files on a per (satellite, ground-station,
   radio) basis.

 * Ability to export consistently-formatted PDF link budgets for
   communcation with external agencies.
 
 * Ability to easily produce graphs, such as pfd/4kHz for regulatory
   compliance.

 * Ability to easily solve for required values within a link budget.

 * Ability to tag components with arbitrary values, such as datasheet
   links, descriptions, and part numbers.


Installation
=============

 * `python setup.py install -f`
 * `pip install -r requirements.txt`
 * `d=${HOME}/.matplotlib; mkdir -p ${d} ; cd ${d} ; fc-list` matplotlib issue #2919


Example Usage
=============

See the `examples` directory for example usages as they are easier to
maintain than a readme.


Extending and Understanding
===========================

Submodules
----------

 * `model.py`: Contains the actual DAG Model class that houses the core
               logic of the calculations.

 * `budget.py`: Contains the logic to combine all of the tributaries
                into a single model.

 * `utils.py`: Utilities

 * `*.py`: Tributaries.  These each provide boilerplate inputs and
                         calculators that are common to link budgets.
                         For example, you're likely to need a
                         transmitter and a receiver.  There will be a
                         channel to carry the signal, etc.

Creating Tributaries
--------------------

If you just want to add one more computation, or modify one, you can
do so by including it in the budget itself -- you don't need to create
your own tributary.  If you do, however, want to create a new one, use
the pre-existing source as a guide (it should be pretty clear).  Note
that you'll need to define the following:

 * `tribute`: This should be a dict of node-names to values.  That
   works both for constants (like `apoapsis_altitude_km` or
   `speed_of_light_mps`), or for functions that calculate values (like
   `slant_range_km` or `link_margin_db`).  The budget will expect this
   value to exist.

 * `enum`: An enum for all of the node-names you use in your
           tributary.  Don't worry about the numbers being mismatched,
           the budget will map them for you.

 * `dependencies`: The budget will incorporate all of the dependencies
                   you register.  Even if you have external
                   dependencies, defined in other tributaries, or even
                   the top-level budget, that's fine.  Just include
                   them in your enum (be sure they're named the same
                   thing), and reference them as you would any other
                   node.

Tagging Architecture
--------------------

Individual components include a facility for tagging with metadata
such as test report links, datasheets, part numbers, etc.  The tagging
is key/value based, and not restricted or controlled.  There are two
primary mechanisms by which tagging occurs:

 * Through pre-defined objects, such as `Antenna` or `Element`, whcih
   permit arbitrary keyword arguments that will be automatically added
   to their metadata.

 * Throug the use of `TaggedAttribute` objects, which permit adding
   arbitrary tags to individual values (such as the
   `rx_antenna_noise_temperature`).

You'll find examples of both of these usages in the `examples`
directory.
