:mod:`praxes.physref.elam`
==========================

The :mod:`elam` module provides an interface to the Elam x-ray database.
Elements are accessed using :attr:`atomic_data`, which provides a mapping to
the element data::

   >>> from praxes.physref.elam import atomic_data
   >>> copper = atomic_data['Cu']
   >>> print(copper.atomic_number)
   29

Each element provides a mapping to the x-ray states reported in the Elam
database::

   >>> print(copper.keys())
   ['K', 'L1', 'L2', 'L3', 'M1', 'M2', 'M3', 'M4', 'M5']
   >>> print(copper['K'].fluorescence_yield)
   0.441091

Each x-ray state provides a mapping to the transitions originating from that
state::

   >>> print(copper['K'].keys())
   ['L1', 'L2', 'L3', 'M2', 'M3', 'M4,5']
   >>> print(copper['K']['L3'].iupac_symbol)
   'K-L3'

Note, in multithreading environments, there are issues sharing sqlite data
between threads. As a result, objects arising from a given instance of
:class:`AtomicData`, such as :attr:`atomic_data`, should not be shared between
threads. Instead, you should create a new instance of :class:`AtomicData` in
each thread to access the data.


Module Interface
----------------

.. automodule:: praxes.physref.elam

.. autoclass:: praxes.physref.elam.atomicdata.AtomicData
   :members:
   :inherited-members:

.. autoclass:: praxes.physref.elam.element.Element
   :members:
   :inherited-members:

.. autoclass:: praxes.physref.elam.xraylevel.XrayLevel
   :members:
   :inherited-members:

.. autoclass:: praxes.physref.elam.transition.Transition
   :members:
   :inherited-members:
