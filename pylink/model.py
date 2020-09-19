#!/usr/bin/python

import inspect
import math
import os
import pprint
import re
import sys
import tempfile
import traceback

import pylink.utils as utils

from pylink.tagged_attribute import TaggedAttribute


class LoopException(Exception):
    pass


class DAGModel(object):
    """DAG Solver

    After instantiating this class with a series of nodes, those nodes
    (and their recursively-calculated values) can be referenced as
    instance variables.  It also includes a solver, and the ability to
    override values.
    """

    def __init__(self, contrib=[], **extras):
        """Creates a new DAG Model

        contrib -- Iterable of tributaries
        extras -- Any additional node to add/override

        Please note that nodes are processed in the order in which
        they are received.  That means that if you add your node in
        the last tributary, it'll override any previous definition of
        that node.  Similarly, if you add your node in the kwargs,
        you'll override any node definition in the tributaries.
        """

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
        for mod in contrib:
            names += mod.tribute.keys()
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
            self.accept_tribute(t)

        # Record the calculation stack for dependency tracking
        self._stack = []

        self._init_cache()

        # We start with an empty dependency tree and update as able
        self._deps = {}
        self._map_dependencies()

    def accept_tribute(self, t):
        for name, v, in t.items():
            node = self._nodes[name]
            if hasattr(v, '__call__'):
                self._calc[node] = v
            elif isinstance(v, TaggedAttribute):
                self._meta[node] = v.meta
                self._values[node] = v.value
            else:
                self._values[node] = v

    def clear_cache(self):
        """Clears the cache.

        Useful if you do something like accept_tribute().  Currently
        only used in testing.
        """
        self._init_cache()

    def is_calculated_node(self, node):
        """Determines whether or not the given node is calculated.
        """
        return node in self._calc

    def is_static_node(self, node):
        """Determines whether or not the given node is static.
        """
        return not self.is_calculated_node(node)

    def is_overridden(self, node):
        """Determines whether or not the given node is overridden.
        """
        return self.is_calculated_node(node) and node in self._values

    def get_meta(self, node):
        """Returns the metadata dict associated with this node
        """
        if node in self._meta:
            return self._meta[node]
        return None

    def set_meta(self, node, k, v):
        """Sets the desired key/value in this node's metadata dict
        """
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
        """Pretty Prints the dependency information for all nodes.

        First is the one-layer dependencies (ie link_margin_db depends
        upon required_ebn0_db and received_ebn0_db).

        Next the flattened dependencies are printed (so link_margin_db
        ends up depending upon lots and lots of things).

        Finally the flattened reverse dependencies are printed (we
        need these for proper cache invalidation).
        """
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
        """Either return the cached value, or calculate/lookup the node's value.

        You really only need this method if you're introducing a
        cycle.

        clear_stack -- This kwarg permits the calculation with an
        empty stack.  That way the cycle-checker doesn't complain, and
        you can happily introduce cycles.  See the package README for
        more information about how to do this safely.
        """
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
        raise AttributeError("It looks like you're missing a node: %s" % name)

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
        """Returns the name of the node

        node -- this is the integer from the enum
        """    
        return self._names[node]

    def node_num(self, name):
        """Returns the node number from the name
        """    
        return self._nodes[name]

    def override(self, node, value):
        """Overrides a given node's value.

        If it's a static node, it redefines it.  If it's a calculated
        node it'll serve this static value instead of executing node.
        """
        self._cache_clear(node=node)
        self._values[node] = value

    def revert(self, node):
        """Reverts an override on a node.

        Please note that this operation only makes sense if you're
        reverting an override on a calculator.
        """
        if node in self._values:
            if node in self._calc:
                self._cache_clear(node=node)
                del self._values[node]
            else:
                name = self.node_name(node)
                msg = "You can't revert a static value: %s" % name
                raise AttributeError(msg)

    def override_value(self, node):
        """Returns the override value for a node.

        If you override a calculated node, this method will return the
        value to which it was overridden, otherwise None.  And if
        you're overriding the calculated node to return None, well,
        you're out of luck.
        """
        if node in self._values:
            return self._values[node]
        return None

    def _solve_for(self, var, fixed, fixed_value, start, stop, step):

        # The output variable should always be reverted
        self.revert(fixed)

        best_val = start
        self.override(var, start)
        best_diff = abs(fixed_value - self.cached_calculate(fixed))

        for i in range(0, int(math.ceil((stop-start)/step))+1, 1):
            val = min(start + step*i, stop)
            self.override(var, val)
            diff = abs(fixed_value - self.cached_calculate(fixed))
            if diff < best_diff:
                best_diff = diff
                best_val = val

        assert(best_val <= stop)
        return best_val

    def solve_for(self, var, fixed, fixed_value, start, stop, step, rounds=3):
        """Solve for a fixed variable by varying another.

        Using multiple <rounds>, this method solves for <var> by
        searching for the value that results in <fixed> being closest
        to <fixed_value> between <start> and <stop> at intervals of
        <step>.  Subsequent rounds will use the same number of steps
        though the step size will, of course, shrink.  After it will
        search within the winning range at higher precision.

        This method only works for either monotonic functions.  If
        there are two values that satisfy the constraint, it will find
        the one closest to <start>.

        var -- Node number to solve for (from the enum)
        fixed -- Node number constraining the search
        fixed_value -- The target value for the fixed node
        start -- The value for <var> at which to start
        stop -- The value for <var> at which to stop
        step -- The delta between points to try in the search
        rounds -- The total number of rounds to attempt
        """

        # It only makes sense to use a fixed variable that is a
        # calculator, so we check for that here.
        if not self.is_calculated_node(fixed):
            raise AttributeError("Can only solve with calculated outputs")

        # The number of rounds should be a member of Z+ > 0
        if int != type(rounds) or rounds < 1:
            raise AttributeError("Gimme an int number of rounds > 0, please.")

        # The control and response variables cannot be the same
        if fixed == var:
            raise AttributeError("Fixed and Variable nodes cannot be the same")

        # Preserve the original values
        def _static_val(node, is_calc):
            if is_calc: return self.override_value(node)
            return self.cached_calculate(node)
        fix_is_calc = self.is_calculated_node(fixed)
        fix_is_over = self.is_overridden(fixed)
        fix_orig = _static_val(fixed, fix_is_calc)
        var_is_calc = self.is_calculated_node(var)
        var_is_over = self.is_overridden(var)
        var_orig = _static_val(var, var_is_calc)

        if start > stop:
            assert(step < 0)
            tmp = start
            start = stop
            stop = tmp
            step *= -1
        else:
            assert(step > 0)

        n = (stop - start) / step
        for i in range(rounds):
            retval = self._solve_for(var,
                                     fixed, fixed_value,
                                     start,
                                     stop,
                                     step)
            ostep = step
            step = step/n
            if 0 == step:
                break
            start = max(retval - ostep/2.0 - 2*step, start)
            stop = min(retval + ostep/2.0 + 2*step, stop)


        # Restoration action truth table
        #
        # override, calculated, action
        #    0           0      restore
        #    0           1      nothing
        #    1           0      ERROR (can only override calculated nodes)
        #    1           1      restore

        restore_fix = not (fix_is_over ^ fix_is_calc)
        restore_var = not (var_is_over ^ var_is_calc)

        if restore_fix:
            self.override(fixed, fix_orig)

        if restore_var:
            self.override(var, var_orig)

        return retval

    def nodes(self):
        return self._names.keys()

    def export_deps_dot(self):
        retval = ['digraph {']

        for node, deps in self._deps.items():
            for dep in deps:
                retval.append('  %s -> %s' % (self.node_name(node),
                                              self.node_name(dep)))
        retval.append('}')
        return '\n'.join(retval)

    def export_deps_png(self, path):
        dot = self.export_deps_dot()
        n, dotpath = tempfile.mkstemp()
        fd = open(dotpath, 'w')
        fd.write(dot)
        fd.close()

        # build the graph
        # subprocess.call(['gv', '-o', path, dotpath])

        os.unlink(dotpath)
