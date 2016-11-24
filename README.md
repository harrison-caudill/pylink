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

Cycles
------

In some circumstances, cycles do exist, breaking the DAG nature of
this system.  Under very special circumstances, we can deal with
those.  If one of the items in the loop exists within a finite set,
then you can do an O(N) search across all of those options, to
determine the most appropriate value.  A real-life example can be
found in `modulation.py`:

```
best_modulation_code
 -> additional_rx_losses_db
 -> excess_noise_bandwidth_loss_db
 -> required_rx_bw_dbhz
 -> required_rx_bw_hz
 -> rx_spectral_efficiency_bps_per_hz
 -> best_modulation_code
```

The way we get around this issue, is to recognize that
`best_modulation_code` exists within a finite set (specifically all
available modulation options).  That allows us to, essentially, fake
the return value of our own function, observe a figure of merit, and
return the appropriate value at the end.  To introduce a cycle, you'll
need to do the following:

 1. Loop through all possible options

 2. In your loop, start by overriding the value you are attempting to
    compute to the current option

 3. Compute the value that induces a cycle with `clear_stack=True`

 4. Revert the value you are attempting to calculate

For example:
```python
def _cycle_inducement(model):
    e = model.enum

    for option in model.cycle_inducement_options: # Step 1
        model.override(e.cycle_inducement, option) # Step 2
        cycle = model.cached_calculate(e.cycle, clear_stack=True) # Step 3
        model.revert(e.cycle_inducement) # Step 4
```

You can also find a unit-test of this behavior in `model_test.py`.
