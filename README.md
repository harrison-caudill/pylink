Note to Anyone Reading This
===========================

I just closed down business operations at BStar and switched over to
consulting.  I have some time on my hands right now, so feel free to file an
issue if you have a feature request.


PyPi Naming
===========

Please note that there is already a `pylink` package on PyPi, so it is
currently registered as `pylink-satcom`.  I'll repeat this warning in
the `Installation` section below.


Python Link Budget Calculation/Management and General Modelling
===============================================================

This software package is meant to replace the manual-intensive
spreadsheet method.  This package is intended to permit the following
major changes in common methodology:

 * Use of configuration files on a per (satellite, ground-station,
   radio) basis.

 * Ability to export consistently-formatted PDF link budgets for
   communcation with external agencies.
 
 * Ability to easily produce graphs, such as pfd/4kHz for regulatory
   compliance.

 * Ability to easily solve for required values within a link budget.

 * Ability to tag components with arbitrary values, such as datasheet
   links, descriptions, and part numbers.

 * Creation of more generalized models for calculating whatever you
   want (see the [Midlife Crisis Example](examples/midlife_crisis.py)
   or the [HyperSpectral Imaging SNR
   Budget](examples/hyperspectral.py))

 * Ease the building of monte-carlo simulations (FIXME: need example).


The nature of this package is best described as three things:

1) A caching DAG (Directed Acyclic Graph) Solver.

2) A set of utilities common to link-budgets.

3) A set of pre-defined computational nodes common to link budgets.

If you're looking for a quick-start and/or just want to go with some
boilerplate examples, take a look at the [Examples](examples/)
directory.


DAG Solver
----------

Spreadsheets are, for the most part, DAGs.  If you define `C46 = C87 -
$B$34` then you are, essentially, saying that 3 nodes exist: `C46`,
`C87`, and `$B$34`.  You are also stating that to solve for node `C46`
you take the value of node `C87` and subtract the value of node
`$B$34`.

This system works the same way, except that instead of saying `C46`,
we might instead say `link_margin_db`.  And instead of coupling our
presentation and data layers, as in a spreadsheet, we might define it
as follows:

```python
def _link_margin_db(model):
    # Note how we're just referencing things like required_ebn0_db as
    # instance vars.  No they aren't instance vars, that's just how
    # you reference nodes in the DAG.
    return model.received_ebn0_db - model.required_ebn0_db

my_example = pylink.DAGModel(received_ebn0_db=8.0,
                             required_ebn0_db=6.0,
                             link_margin_db=_link_margin_db)
print('My Example Link Margin: ', my_example.link_margin_db)
```

The DAGModel class overrides python's `__getattr__` method so that you
can reference nodes directly, without the added syntactic sugar of
extra parens, brakcets, and tick-marks.

If you're curious what this all looks like in a context other than
link budgets, take a look at the [Midlife Crisis
Example](examples/midlife_crisis.py).  There we create a DAGModel that
has nothing at all to do with RF, satellites, etc.  There's really
nothing that restricts us to link budgets, or even RF.  Feel free to
write the nodes and use the framework for whatever you want.

Please note that there are two types of nodes:
 * Static Nodes
 * Calculated Nodes

Simply put, static nodes are just plain old values that you pass in,
whereas calculated nodes are functions/methods/...  You'll see an enum
referenced all over the place.  That's because it uses node numbers
internally, and an enum is convenient way to reference node numbers
without having to use a bunch of single-ticks and brackets.  For example:

```python
def _link_margin_db(model):
    return model.received_ebn0_db - model.required_ebn0_db

my_example = pylink.DAGModel(received_ebn0_db=8.0,
                             required_ebn0_db=6.0,
                             link_margin_db=_link_margin_db)
m = my_example # m as in model
e = m.enum     # e as in enum

print(e.link_margin_db)
print(m.node_name(e.link_margin_db))
print(m.node_num('link_margin_db')) # the alternative to using the enum
```

It also includes a multi-round linear solver for convenience.  See the
[Solver Example](examples/solver.py).


Utilities
---------

There are some utilities that are handy for working with RF.  For
example, there's a function that fakes an antenna gain pattern for
you: `pylink.pattern_generator`, and another one that calculates the
attenuation of PFD from spreading over a distance:
`pylink.spreading_loss_db`.


Pre-Defined Nodes
-----------------

As shown above, new nodes can be registered with the DAG Model directly:

```python
my_example = pylink.DAGModel(received_ebn0_db=8.0,
                             required_ebn0_db=6.0,
                             link_margin_db=_link_margin_db)
```

Here we've added 3 nodes:
 * received_ebn0_db
 * required_ebn0_db
 * link_margin_db

It frequently makes sense to group nodes before registration.  That's
where Tributaries come into play.  If you look in the [Basic
Example](examples/basic.py), you see that it uses a whole list of
tributaries.  [Geometry](pylink/tributaries/geometry.py) is probably
the simplest and most straight-forward tributary if you're looking for
a production example, otherwise please see the [Examples](examples/).

Aside from logical grouping, it also makes sense to reuse code.
[Antennas](pylink/tributaries/antenna.py), for example, have patterns
that can be plotted to PNG files irrespective of whether they're a
transmit or receive antenna.  Instead of duplicating that code, we
simply have a single Antenna class that remembers whether it is meant
for tx or rx.  When it contributes nodes to the DAG, those nodes
(instance methods) will be able to refer to their object and know
whether to use the tx or rx path.


Installation
=============

Please note that there is a name collision with another `pylink`
package in PyPi.  As such, we have registered this package there under
a different name: `pylink-satcom`.

We recommend using Anaconda with Python 3.7.  This package can be
installed by executing: `pip install pylink-satcom`

If you want to install it from source: `pip install .` works as well.


Legacy Support
==============

Migration instructions from previous versions can be found in the
[Changelog](CHANGELOG.md).


Extending and Understanding
===========================

Submodules
----------

 * `model.py`: Contains the actual DAG Model class that houses the core
               logic of the calculations.

 * `utils.py`: Standalone utility functions (such as `to_db`)

 * `report.py`: Satellite link budget latex report generator.

 * `tagged_attribute.py`: The TaggedAttribute class for adding
                          metadata tags to individual components.

 * `element.py`: RF Element container.

 * `tributaries/*.py`: These each provide boilerplate inputs and
                       calculators that are common to link budgets.
                       For example, you're likely to need a
                       transmitter and a receiver.  There will be a
                       channel to carry the signal, etc.

Creating Tributaries
--------------------

If you just want to add one more computation, or modify one, you can
do so by including it in the model itself -- you don't need to create
your own tributary.  If, however, you do want to create a new one, use
the pre-existing source as a guide (it should be pretty clear).  Note
that you'll need to define the `tribute` instance variable.  This
should be a dict of node-names to values.  That works both for
constants (like `apoapsis_altitude_km` or `speed_of_light_m_per_s`),
and for functions that calculate values (like `slant_range_km` or
`link_margin_db`).  The DAG Model will expect this value to exist and
raise an exception otherwise.

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

 5. Select the appropriate option by comparing the figure of merit.

 6. Return the result from your calculator.

For example:
```python
def _cycle_inducement(model):
    e = model.enum

    best_cycle = -1
    best_option = None

    for option in model.cycle_inducement_options: # Step 1
        model.override(e.cycle_inducement, option) # Step 2
        cycle = model.cached_calculate(e.cycle, clear_stack=True) # Step 3
        model.revert(e.cycle_inducement) # Step 4

        # Step 5
        if cycle > best_cycle:
            best_cycle = cycle
            best_option = option

    return best_option # Step 6
```

You can also find a unit-test of this behavior in `model_test.py`.


HyperSpectral Imaging
=====================

BStar pivoted to HyperSpectral in an attempt to address the disparity
between customer/partner/regulator interest in our success and
investor interest.  HyperSpectral Imaging was the selected target (due
to the close association with comms and the simplicity of the business
model).  For expediency, the HSI SNR budget was computed using pylink,
and I'm adding it to the repo to avoid having yet-another-repo.  If it
gathers enough steam, I'll break it out into a separate repo.
