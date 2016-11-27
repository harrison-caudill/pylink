#!/usr/bin/python

import inspect
import math
import os
import pprint
import re
import sys
import traceback
import utils

from tagged_attribute import TaggedAttribute


class LoopException(Exception):
    pass


class DAGModel(object):

    def __init__(self, contrib=[], **extras):

        # Make sure the input looks sane
        for t in contrib:
            try:
                t.tribute
            except AttributeError:
                msg = ("One of your Tributaries doesn't have "
                       + "'tribute' defined: %s" % t.__class__.__name__)
                raise AttributeError(msg)

        # calculate the list of node names & enum
        names = []
        map(lambda x: names.extend(x.tribute.keys()), contrib)
        names.extend(extras.keys())
        self.enum = utils.sequential_enum(*names)

        # associate names to nodes
        (self._names, self._nodes,) = utils.node_associations(self.enum)

        # merge the contributions
        self._calc = {}
        self._values = {}
        self._meta = {}
        tributes = [m.tribute for m in contrib]
        tributes.append(extras)
        for t in tributes:
            for name, v, in t.iteritems():
                node = self._nodes[name]
                if hasattr(v, '__call__'):
                    self._calc[node] = v
                elif isinstance(v, TaggedAttribute):
                    self._meta[node] = v.meta
                    self._values[node] = v.value
                else:
                    self._values[node] = v

        # Record the calculation stack for dependency tracking
        self._stack = []

        self._init_cache()

        # We start with an empty dependency tree and update as able
        self._deps = {}
        self._map_dependencies()

    def get_meta(self, node):
        if node in self._meta:
            return self._meta[node]
        return None

    def set_meta(self, node, k, v):
        self._meta.setdefault(node, {k:v})
        self._meta[node][k] = v

    def _map_dependencies(self):
        # nodes => list of direct dependencies
        # self._deps is maintained by the cache system
        self._dep_names = self._named_deplist(self._deps)

        # nodes => flattened dependency list
        self._flat_deps = self._flattened_deps()
        self._flat_dep_names = self._named_deplist(self._flat_deps)

        # nodes => flattened list of nodes depending upon it
        self._clients = self._client_list(self._flat_deps)
        self._client_names = self._named_deplist(self._clients)

        self._deps_are_stale = False

    def _init_cache(self):
        self._cache = {}

    def _record_parent(self, node):
        if len(self._stack):
            dep = self._stack[-1]
            self._add_dependency_impl(node, dep)

    def print_dependencies(self):
        if self._deps_are_stale:
            # This call is quite expensive, so we only want to do so
            # if necessary.
            self._map_dependencies()
        pprint.pprint(self._dep_names)
        pprint.pprint(self._flat_dep_names)
        pprint.pprint(self._client_names)

    def _add_dependency_impl(self, node, dep):
        self._deps.setdefault(dep, {node:0})
        self._deps[dep].setdefault(node, 0)
        self._deps[dep][node] += 1
        if self._deps[dep][node] == 1:
            self._deps_are_stale = True

    def cached_calculate(self, node, clear_stack=False):
        if clear_stack:
            orig_stack = self._stack
            self._stack = []

        self._record_parent(node)
        if node in self._cache:
            retval = self._cache[node]
        else:
            retval = self._calculate(node)

        if clear_stack:
            self._stack = orig_stack
        return retval


    def _calculate(self, node, stack=None):

        if stack:
            orig_stack = self._stack
            self._stack = stack

        if node in self._stack:
            stack = self._stack + [node]
            stack = [self.node_name(n) for n in stack]
            s = pprint.pformat(stack)
            raise LoopException("\n=== LOOP DETECTED ===\n%s" % s)

        self._stack.append(node)

        if node in self._values:
            retval = self._values[node]
        else:
            retval = self._calc[node](self)

        self._cache_put(node, retval)
        self._stack.pop()

        if stack:
            self._stack = orig_stack

        return retval

    def _cache_clear(self, node=None):
        if self._deps_are_stale:
            # This call is quite expensive, so we only want to do so
            # if necessary.
            self._map_dependencies()

        if node is not None:
            if node in self._cache:
                del self._cache[node]
            for client in self._clients[node]:
                if client in self._cache:
                    del self._cache[client]
        else:
            self._init_cache()

    def _cache_put(self, node, value):
        self._cache[node] = value

    def __getattr__(self, name):
        if name in self._nodes:
            node = self.node_num(name)
            if node not in self._values and node not in self._calc:
                name = self.node_name(node)
                msg = "It looks like you're missing an item: %s" % name
                raise AttributeError(msg)
            return self.cached_calculate(node)
        raise AttributeError("No attribute found: %s" % name)

    def _top_client_list(self):
        retval = {}
        for node in self._clients:
            if self.is_top_node(node):
                retval[node] = self._clients[node]
        return retval

    def _client_list(self, flat_deps):
        retval = {}
        for dep in self._names:
            retval[dep] = []
            for node in flat_deps:
                if dep in flat_deps[node]:
                    retval[dep].append(node)
        return retval

    def _named_deplist(self, deps):
        retval = {}
        for node in deps:
            n = self.node_name(node)
            retval[n] = [ self.node_name(x) for x in deps[node] ]
        return retval

    def __flattened_deps_r(self, node, res={}):
        if node in self._deps:
            # We only register dependencies for dependent items
            for dep in self._deps[node]:
                res[dep] = 1
                self.__flattened_deps_r(dep, res=res)
        return res.keys()

    def _flattened_deps(self):
        retval = {}
        for node in self._deps:
            retval[node] = self.__flattened_deps_r(node, res={})
        return retval

    def node_name(self, node):
        return self._names[node]

    def node_num(self, name):
        return self._nodes[name]

    def is_top_node(self, node):
        # if it doesn't have any dependencies, it's a top-level node
        return node not in self._deps or 0 == len(self._deps[node])

    def override(self, node, value):
        self._cache_clear(node=node)
        self._values[node] = value

    def revert(self, node):
        if node in self._values:
            self._cache_clear(node=node)
            del self._values[node]

    def override_value(self, node):
        if node in self._values:
            return self._values[node]
        return None

    def _solve_for(self, var, fixed, fixed_value, start, stop, step):
        original_variable_value = self.override_value(var)
        original_fixed_value = self.override_value(fixed)
        self.revert(fixed)

        best_val = start
        best_diff = abs(fixed_value - self.cached_calculate(fixed))
        
        for i in xrange(0, int((stop-start)/step), 1):
            val = start + step*i
            self.override(var, val)
            diff = abs(fixed_value - self.cached_calculate(fixed))
            if diff < best_diff:
                best_diff = diff
                best_val = val

        self.revert(fixed)
        if original_fixed_value is not None:
            self.override(fixed, original_fixed_value)
        
        self.revert(var)
        if original_variable_value is not None:
            self.override(var, original_variable_value)

        return best_val

    def solve_for(self, var, fixed, fixed_value, start, stop, step, rounds=3):
        n = (stop - start) / step
        for i in range(rounds):
            retval = self._solve_for(var,
                                     fixed, fixed_value,
                                     start,
                                     stop,
                                     step)
            ostep = step
            step = step/n
            start = max(retval - ostep/2.0 - 2*step, start)
            stop = min(retval + ostep/2.0 + 2*step, stop)

        return retval

    def nodes(self):
        return self._names.keys()
