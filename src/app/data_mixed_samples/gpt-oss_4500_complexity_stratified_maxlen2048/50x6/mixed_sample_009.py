# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6144_lm, name=degree) ===
def degree(self, nbunch=None, t=None):
        """Return the degree of a node or nodes at time t.

        The node degree is the number of interaction adjacent to that node in a given time frame.

        Parameters
        ----------
        nbunch : iterable container, optional (default=all nodes)
            A container of nodes.  The container will be iterated
            through once.

        t : snapshot id (default=None)
            If None will be returned the degree of nodes on the flattened graph.


        Returns
        -------
        nd : dictionary, or number
            A dictionary with nodes as keys and degree as values or
            a number if a single node is specified.

        Examples
        --------
        >>> G = dn.DynGraph()
        >>> G.add_path([0,1,2,3], t=0)
        >>> G.degree(0, t=0)
        1
        >>> G.degree([0,1], t=1)
        {0: 0, 1: 0}
        >>> list(G.degree([0,1], t=0).values())
        [1, 2]
        """

# === BLOCK 2 (label=lm, source_idx=line317_lm, name=from_json) ===
def from_json(cls, data, result=None):
        """
        Create new Relation element from JSON data

        :param data: Element data from JSON
        :type data: Dict
        :param result: The result this element belongs to
        :type result: overpy.Result
        :return: New instance of Relation
        :rtype: overpy.Relation
        :raises overpy.exception.ElementDataWrongType: If type value of the passed JSON data does not match.
        """

# === BLOCK 3 (label=human, source_idx=line2311_human, name=const) ===
def const(const):
    """Convenience wrapper to yield the value of a constant"""
    try:
        return getattr(_c, const)
    except AttributeError:
        raise FSQEnvError(errno.EINVAL, u'No such constant:'\
                               u' {0}'.format(const))
    except TypeError:
        raise TypeError(errno.EINVAL, u'const name must be a string or'\
                        u' unicode object, not:'\
                        u' {0}'.format(const.__class__.__name__))

# === BLOCK 4 (label=human, source_idx=line4038_human, name=M) ===
def M(self, t, tips=None, gaps=None):
        """See docs for method in `Model` abstract base class."""
        assert isinstance(t, float) and t > 0, "Invalid t: {0}".format(t)
        with scipy.errstate(under='ignore'): # don't worry if some values 0
            if ('expD', t) not in self._cached:
                self._cached[('expD', t)] = scipy.exp(self.D * self.mu * t)
            expD = self._cached[('expD', t)]
            if tips is None:
                # swap axes to broadcast multiply D as diagonal matrix
                M = broadcastMatrixMultiply((self.A.swapaxes(0, 1) *
                        expD).swapaxes(1, 0), self.Ainv)
            else:
                M = broadcastMatrixVectorMultiply((self.A.swapaxes(0, 1)
                        * expD).swapaxes(1, 0), broadcastGetCols(
                        self.Ainv, tips))
                if gaps is not None:
                    M[gaps] = scipy.ones(N_CODON, dtype='float')
        #if M.min() < -0.01:
        #    warnings.warn("Large negative value in M(t) being set to 0. "
        #            "Value is {0}, t is {1}".format(M.min(), t))
        M[M < 0] = 0.0
        return M

# === BLOCK 5 (label=human, source_idx=line4612_human, name=search_indices) ===
def search_indices(values, source):
    """
    Given a set of values returns the indices of each of those values
    in the source array.
    """
    orig_indices = source.argsort()
    return orig_indices[np.searchsorted(source[orig_indices], values)]

# === BLOCK 6 (label=lm, source_idx=line5735_lm, name=_make_key) ===
def _make_key(self):
        """Make a key for caching files in the LRU cache."""
