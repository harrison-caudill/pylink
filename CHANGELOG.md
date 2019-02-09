`0.6 -> 0.7`
============

Windows support was added.  It actually took shockingly little effort.
Tests pass, LaTeX and image generation works.  I also added expanded
`human_b` support as well as an actual unit-test for `human_b`.


`0.5 -> 0.6`
============

The HyperSpectral Imaging code was integrated here.  I know that it
doesn't really belong, and I should probably separate everything out
into 3 packages (DAG, link budgets, and hyperspectral)...but until
someone cares or there's a reason other than principle I'll wait.


`0.4 -> 0.5`
============

The package was published on PyPi here.  The main change was that it
was published under the title `pylink-satcom` since there was a name
collision in the PyPi index.


`0.3 -> 0.4`
============

There were a number of minor changes, but mostly it was updated to
work properly with Python3 and Anaconda.  I've switched to using
Python 3.7 in Anaconda as my primary dev environment.


`0.2 -> 0.3`
============

 1. `LinkBudget` is now a Tributary, just like `channel`, or `geometry`

 2. The logic to combine all of the tributaries now resides inside of
    `DAGModel`

 3. The report generation logic was separated out into the `Report` class

 4. Modulations have been implemented for realz this time

 5. Some of the nodes have been added/removed/renamed/...


Points 1 & 2
------------

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

Point 3
-------

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
                author='The Incredible Hulk',
                intro='And now, for a budget that needs no intro',
                watermark_text="Ruh Roh")
```

Point 4
-------

Point 4 is, perhaps, the most complicated.  It introduces a cycle into
the model (as you can see above in [Cycles](README.md#cycles)), and
also necessitates a bit of rethinking.

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
The `Modulation` tributary defaults to DVB-S2X, with 80% efficiency of
the transmit spectral efficiency.

Point 5
-------
Point 5 should be pretty obvious as you go.  For example,
`spectral_efficiency_bps_per_hz` doesn't exist anymore since we
consider both the tx and rx sides, so now you have
`tx_spectral_efficiency_bps_per_hz` and
`rx_spectral_efficiency_bps_per_hz`.
