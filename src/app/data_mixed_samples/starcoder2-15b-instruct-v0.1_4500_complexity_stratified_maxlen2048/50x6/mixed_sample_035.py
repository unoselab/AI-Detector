# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line869_human, name=set_default_unit_all) ===
def set_default_unit_all(self, twig=None, unit=None, **kwargs):
        """
        TODO: add documentation
        """
        if twig is not None and unit is None:
            # then try to support value as the first argument if no matches with twigs
            if isinstance(unit, u.Unit) or not isinstance(twig, str):
                unit = twig
                twig = None

            elif not len(self.filter(twig=twig, check_default=check_default, **kwargs)):
                unit = twig
                twig = None

        for param in self.filter(twig=twig, **kwargs).to_list():
            param.set_default_unit(unit)

# === BLOCK 2 (label=human, source_idx=line1925_human, name=_get_whole_subtrees) ===
def _get_whole_subtrees(self):
        """Returns an array of nodes in the tree that have balanced subtrees beneath them,
        moving from left to right.
        """
        subtrees = []
        loose_leaves = len(self.leaves) - 2**int(log(len(self.leaves), 2))
        the_node = self.root
        while loose_leaves:
            subtrees.append(the_node.l)
            the_node = the_node.r
            loose_leaves = loose_leaves - 2**int(log(loose_leaves, 2))
        subtrees.append(the_node)
        return subtrees

# === BLOCK 3 (label=lm, source_idx=line2951_lm, name=delete_property) ===
def delete_property(self, content_id, property_key, callback=None):
        """
        Deletes a content property.
        :param content_id (string): The ID for the content that owns the property to be deleted.
        :param property_key (string): The name of the property to be deleted.
        :param callback: OPTIONAL: The callback to execute on the resulting data, before the method returns.
                         Default: None (no callback, raw data returned).
        :return: Empty if successful, or the results of the callback.
                 Will raise requests.HTTPError on bad input, potentially.
        """
        url = f"{self.base_url}/content/{content_id}/property/{property_key}"
        response = requests.delete(url, headers=self.headers)
        response.raise_for_status()
        if callback:
            return callback(response.json())
        return

# === BLOCK 4 (label=human, source_idx=line1792_human, name=_format_envvars) ===
def _format_envvars(ctx):
    """Format all envvars for a `click.Command`."""
    params = [x for x in ctx.command.params if getattr(x, 'envvar')]

    for param in params:
        yield '.. _{command_name}-{param_name}-{envvar}:'.format(
            command_name=ctx.command_path.replace(' ', '-'),
            param_name=param.name,
            envvar=param.envvar,
        )
        yield ''
        for line in _format_envvar(param):
            yield line
        yield ''

# === BLOCK 5 (label=lm, source_idx=line1884_lm, name=_param_to_matrix) ===
def _param_to_matrix(self):
        """
        Convert parameters defined in `self._params` to `cvxopt.matrix`

        :return None
        """
        self._params = cvxopt.matrix(self._params)

# === BLOCK 6 (label=lm, source_idx=line1846_lm, name=mr_dim_ind) ===
def mr_dim_ind(self):
        """Return int, tuple of int, or None, representing MR indices.

        The return value represents the index of each multiple-response (MR)
        dimension in this cube. Return value is None if there are no MR
        dimensions, and int if there is one MR dimension, and a tuple of int
        when there are more than one. The index is the (zero-based) position
        of the MR dimensions in the _ApparentDimensions sequence returned by
        the :attr"`.dimensions` property.
        """
        mr_dims = []
        for i, dim in enumerate(self.dimensions):
            if dim.is_mr:
                mr_dims.append(i)

        if len(mr_dims) == 0:
            return None
        elif len(mr_dims) == 1:
            return mr_dims[0]
        else:
            return tuple(mr_dims)
