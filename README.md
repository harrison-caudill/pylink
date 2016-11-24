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


Changelog & Migrations
======================

Hints for migrating from previous versions are included here.

`< 0.3 -> 0.3`
--------------

 1. `LinkBudget` is now a Tributary, just like `channel`, or `geometry`

 2. The logic to combine all of the tributaries now resides inside of
    `DAGModel`

 3. The report generation logic was separated out into the `Report` class

 4. Modulations have been implemented for realz this time

 5. Some of the nodes have been added/removed/renamed/...

Points 1 and 2 are pretty easy to deal with.  In older versions, you'd
build a LinkBudget object, which would both combine other tributaries,
add in your custom functions, and add its own nodes as well:

```python
budget = pylink.LinkBudget([pylink.Geometry(),
                            pylink.Antenna(is_rx=True),
                            pylink.Interconnect(is_rx=True),
                            pylink.Receiver(),
                            pylink.Transmitter(),
                            pylink.Interconnect(is_rx=False),
                            pylink.Antenna(is_rx=False),
                            pylink.Channel(),
                            pylink.Modulation(name='QPSK', perf=perf)],
                           name="My Really Cool Budget",
                           rx_antenna_noise_temperature_k=350,
                           **extra_stuff)
```

In the newer rev, it's a bit cleaner, and more true to the DAG nature
of the system:

```python
model = pylink.DAGModel([pylink.Geometry(),
                         pylink.Antenna(is_rx=True),
                         pylink.Interconnect(is_rx=True),
                         pylink.Receiver(),
                         pylink.Transmitter(),
                         pylink.Interconnect(is_rx=False),
                         pylink.Antenna(is_rx=False),
                         pylink.Channel(),
                         pylink.Modulation(name='HomeGrown', perf=perf),
                         pylink.LinkBudget(name="My Really Cool Budget")],
                         **extra_stuff)
```

As you can see, the `LinkBudget` just becomes a regular tributary
which makes it easier to review, instantiate, update, etc etc etc.
There's also a hint, there of point 4, but we'll get to that.

Point 3 is also pretty simple.  Previous versions included the export
logic within `LinkBudget`, so you'd do things like this:

```python
my_awesome_budget.to_latex('awesome.tex',
                           author='The Incredible Hulk',
                           intro='And now, for a budget that needs no intro',
                           watermark_text="Ruh Roh")
```

Now that the logic has been separated out, you would do this instead:

```python
report = pylink.Report(my_awesome_budget)
report.to_latex('awesome.tex',
                'The Incredible Hulk',
                intro='And now, for a budget that needs no intro',
                watermark_text="Ruh Roh")
```

Point 4 is, perhaps, the most complicated.  It introduces a cycle into
the model (as you can see above in [Cycles]), and also necessitates
a bit of rethinking.

Previously, you'd do something like this:
```python
modulation = pylink.Modulation(name='MSK (Magical Shift Keying)',
                               required_ebn0_db=5,
                               spectral_efficiency_bps_per_hz=1)
```

If, however, you have multiple code-options (*cough* DVB-S2X *cough*)
and operate an adaptive bitrate loop, that approach won't work.  You
also don't differentiate between your transmit spectral efficiency,
and your receive spectral efficiency.  If, for example, you have
terrible filtering and need 20% of your allocation for rolloff, then
those two numbers will be different.  The `rx` (rx efficiency) value
affects the noise bandwidth so that you can properly make computations
such as `required_demod_ebn0_db` and `excess_noise_bandwidth_loss_db`.
The `tx` value is useful for things like your channel capacity.

To address these shortcomings, the `Code` object was introduced.  This
allows you to specify a series of these `Code` objects, which will be
automagically-selected based upon your allocation size, and `C/N0`:

```python
perf = [
    #           Name, tx, rx, Es/N0
    pylink.Code("BPSK", .5, .5, 4),
    pylink.Code("QPSK", 1, 1, 8),
    pylink.Code("8PSK", 2, 2, 13),
    ]
modelling_clay = pylink.DAGModel([pylink.Geometry(),
                                  pylink.Antenna(is_rx=True),
                                  pylink.Interconnect(is_rx=True),
                                  pylink.Receiver(),
                                  pylink.Transmitter(),
                                  pylink.Interconnect(is_rx=False),
                                  pylink.Antenna(is_rx=False),
                                  pylink.Channel(),
                                  pylink.Modulation(name='QPSK', perf=perf),
                                  pylink.LinkBudget()])
modulation = pylink.Modulation()
```
The `Modulation` tributary defaults to DVB-S2X.

Point 5 should be pretty obvious as you go.  For example,
`spectral_efficiency_bps_per_hz` doesn't exist anymore since we
consider both the tx and rx sides, so now you have
`tx_spectral_efficiency_bps_per_hz` and
`rx_spectral_efficiency_bps_per_hz`.
