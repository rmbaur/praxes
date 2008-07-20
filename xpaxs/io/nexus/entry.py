"""
Wrappers around the pytables interface to the hdf5 file.

"""

#---------------------------------------------------------------------------
# Stdlib imports
#---------------------------------------------------------------------------

import sys
import time

#---------------------------------------------------------------------------
# Extlib imports
#---------------------------------------------------------------------------

from PyQt4 import QtCore
import tables

#---------------------------------------------------------------------------
# xpaxs imports
#---------------------------------------------------------------------------

from xpaxs.io.nexus.node import NXnode
from xpaxs.io.nexus.registry import class_name_dict

#---------------------------------------------------------------------------
# Normal code begins
#---------------------------------------------------------------------------


class NXentry(NXnode):

    """
    """

    def _create_entry(self, where, name, *args, **kwargs):
        self.nx_file.create_h5group(where, name, *args, **kwargs)

class_name_dict['NXentry'] = NXentry
