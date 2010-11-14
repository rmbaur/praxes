import collections

import numpy as np

from .attributes import AttributeIndex
from .proxies import McaProxy, ScalarProxy


class SpecScan(object):

    __slots__ = [
        '__attrs', '__bytes_read', '__file_name', '__file_offset', '__id',
        '__index', '__index_finalized', '__mca_data_indices', '__name',
        '__scalar_data_index'
        ]

    @property
    def attrs(self):
        return self.__attrs

    @property
    def file_offsets(self):
        return self.__file_offset, self.__bytes_read

    @property
    def id(self):
        return self.__id

    @property
    def name(self):
        return self.__name

    def __init__(self, name, id, file, offset, **kwargs):
        self.__name = name
        self.__id = id
        self.__file_name = file.name
        self.__file_offset = offset
        self.__bytes_read = offset

        self.__attrs = AttributeIndex(**kwargs)
        self.__attrs._index.update(kwargs)

        self.__scalar_data_index = []
        self.__mca_data_indices = {}
        self.__index = collections.OrderedDict()
        self.__index_finalized = False

        self.update()

    def __contains__(self, item):
        return item in self.__index

    def __getitem__(self, item):
        return self.__index[item]

    def __iter__(self):
        return iter(self.__index)

    def __len__(self):
        return len(self.__index)

    def get(self, key, default=None):
        return self.__index.get(key, default)

    def items(self):
        "Return a new view of the scan's attributes' ``(key, val)`` pairs."
        return self.__index.viewitems()

    def keys(self):
        "Return a new view of the scan's attributes' keys."
        return self.__index.viewkeys()

    def values(self):
        "Return a new view of the scan's attributes' values."
        return self.__index.viewvalues()


    def update(self):
        if self.__index_finalized:
            return

        with open(self.__file_name, 'rb') as f:
            attrs = self.__attrs._index
            f.seek(self.__bytes_read)
            file_offset = f.tell()
            line = f.readline()
            while line:
                if line[0].isdigit() or line[0] == '-':
                    self.__scalar_data_index.append(file_offset)
                elif line[0] == '@':
                    key = line.split(None, 1)[0]
                    try:
                        index = self.__mca_data_indices[key]
                    except KeyError:
                        index = self.__mca_data_indices.setdefault(key, [])
                    index.append(file_offset)
                elif line[:2] == '#S':
                    if 'command' in attrs:
                        self.__index_finalized = True
                        break
                    attrs['command'] = ' '.join(line.split()[2:])
                elif line[:2] == '#D':
                    attrs['date'] = line[3:-1]
                elif line[:2] in ('#T', '#M'):
                    x, val, key = line.split()
                    key = key[1:-1]
                    attrs['duration'] = (key, float(val))
                    if x == '#M':
                        attrs['monitor'] = key
                elif line[:2] == '#G':
                    orientations = attrs.setdefault('orientations', [])
                    orientations.append(
                        [float(i) for i in line.split()[1:]]
                        )
                elif line[:2] == '#Q':
                    attrs['hkl'] = [float(i) for i in line.split()[1:]]
                elif line[:2] == '#P':
                    positions = attrs.setdefault('positions', [])
                    positions.extend(
                        [float(i) for i in line.split()[1:]]
                        )
                elif line[:2] == '#C':
                    comments = attrs.setdefault('comments', [])
                    comments.append(line[3:-1])
                elif line[:2] == '#U':
                    user_comments = attrs.setdefault('user_comments', [])
                    user_comments.append(line[3:-1])
                elif line[:2] == '#L':
                    attrs['labels'] = labels = line.split()[1:]
                    for column, label in enumerate(labels):
                        self.__index[label] = ScalarProxy(
                            self.__file_name,
                            label,
                            column,
                            self.__scalar_data_index
                            )

                file_offset = f.tell()
                line = f.readline()

            self.__bytes_read = f.tell()

        if 'positioners' in attrs:
            positioners = attrs.pop('positioners')
            positions = attrs.pop('positions')
            attrs['positions'] = dict(zip(positioners, positions))

        for key, index in self.__mca_data_indices.items():
            if key not in self.__index:
                self.__index[key] = McaProxy(self.__file_name, key, index)
