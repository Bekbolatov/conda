"""
Solver-agnostic logic to expose the prefix state to the solver.
"""

from collections import defaultdict, Mapping, MutableMapping
from types import MappingProxyType
import logging
import functools


class TrackedMap(MutableMapping):
    def __init__(self, name, data=None):
        self._data = data
        self._name = name
        self._logger = logging.getLogger(f"{__name__}::{self.__class__.__name__}")

    def _set(self, key, value, *, reason=None, _level=3):
        msg = f'{self._name}[{key}] set to `{value}`'
        if reason:
            msg += f' ({reason})'
        self._logger.debug(msg, stacklevel=_level)
        self._data[key] = value

    @property
    def name(self):
        return self._name

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value):
        self._set(key, value)

    def __delitem__(self, key):
        self._logger.debug(f'{self._name}[{key}] was deleted', stacklevel=2)
        del self._data[key]

    def pop(self, key):
        self._logger.debug(f'{self._name}[{key}] was deleted', stacklevel=2)
        return self._data.pop(key)

    def popitem(self, key):
        self._logger.debug(f'{self._name}[{key}] was deleted', stacklevel=2)
        return self._data.popitem(key)

    def clear(self):
        self._logger.debug(f'{self._name} was cleared')
        self._data.clear()

    def update(self, data, **kwargs):
        if data and kwargs:
            raise ValueError('Can only update via a data object or keyword mapping')
        self._logger.debug(f'{self._name}[{key}] was deleted', stacklevel=2)
        return self._data.popitem(key)

    def set(self, key, value, *, reason=None):
        self._set(key, value)


class SpecMap(Mapping):
    def __init__(
        self,
        *,
        frozen=None,
        history=None,
        neutered=None,
    ):
        # spec pools
        self._frozen = TrackedMap(frozen or {})
        self._history = TrackedMap(history or {})
        self._neutered = TrackedMap(neutered or {})

    @property
    def _pools(self):
        # ordered by priority
        return (
            self._frozen,
            self._history,
            self._neutered,
        )

    @functools.lru_cache
    def _join_pools(self, *pools):
        data = defaultdict(list)
        for pool in pools:
            for key, value in pool.items():
                data[key].append(value)
        return data

    @property
    def _data(self):
        # we don't do this directly here to use lru_cache
        return self._join_pools(self._pools)

    def __getitem__(self, key):
        return self._data[key]

    def __iter__(self):
        yield from self._data

    def __len__(self):
        return len(self._data)

    def pool_items(self):
        """Iterator that goes over the pool items one by one."""
        for pool in self._pools:
            for item in pool:
                yield (pool, item)


class SolverStateContainer:
    def __init__(
        self,
        requested_specs_to_add: Mapping,
        requested_specs_to_remove: Mapping,
        prefix_data: Mapping,
        history: Mapping,
        pinned: Mapping,
    ):
        # immutable properties
        self._requested_specs_to_add = requested_specs_to_add
        self._requested_specs_to_remove = requested_specs_to_remove
        self._prefix_data = prefix_data
        self._history = history
        self._pinned = pinned

        self._map = SpecMap()  # TODO

    @property
    def map(self):
        return self._map

    @property
    def requested_specs_to_add(self) -> Mapping:
        return MappingProxyType(self._requested_specs_to_add)

    @property
    def requested_specs_to_remove(self) -> Mapping:
        return MappingProxyType(self._requested_specs_to_remove)

    @property
    def prefix_data(self) -> Mapping:
        return MappingProxyType(self._prefix_data)

    @property
    def history(self) -> Mapping:
        return MappingProxyType(self._history)

    @property
    def pinned(self) -> Mapping:
        return MappingProxyType(self._pinned)