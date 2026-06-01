# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6081_human, name=set_requested_intervals) ===
def set_requested_intervals(self, workflow_id, requested_intervals):
        """
        Sets the requested intervals for a given workflow
        :param workflow_id: The workflow id
        :param requested_intervals: The requested intervals
        :return: None
        :type requested_intervals: TimeIntervals
        """
        if workflow_id not in self.workflows:
            raise ValueError("Workflow {} not found".format(workflow_id))

        self.workflows[workflow_id].requested_intervals = requested_intervals

# === BLOCK 2 (label=lm, source_idx=line2020_lm, name=_get_dataobject) ===
def _get_dataobject(self, name, multivalued):
        """This function only gets called if the decorated property
        doesn't have a value in the cache."""
        if multivalued:
            return self._get_multivalued_dataobject(name)
        else:
            return self._get_singlevalued_dataobject(name)

# === BLOCK 3 (label=human, source_idx=line6553_human, name=options) ===
def options(self, url, **kwargs):
        r"""Sends a OPTIONS request. Returns :class:`Response` object.

        :param url: URL for the new :class:`Request` object.
        :param \*\*kwargs: Optional arguments that ``request`` takes.
        :rtype: requests.Response
        """

        kwargs.setdefault('allow_redirects', True)
        return self.request('OPTIONS', url, **kwargs)

# === BLOCK 4 (label=human, source_idx=line2756_human, name=tomof) ===
def tomof(self, indent=0, maxline=MAX_MOF_LINE):
        """
        Return a MOF string with the declaration of this CIM method for use in
        a CIM class declaration.

        The order of parameters and qualifiers is preserved.

        Parameters:

          indent (:term:`integer`): Number of spaces to indent each line of
            the returned string, counted in the line with the method name.

        Returns:

          :term:`unicode string`: MOF string.
        """

        mof = []

        if self.qualifiers:
            mof.append(_qualifiers_tomof(self.qualifiers, indent + MOF_INDENT,
                                         maxline))

        mof.append(_indent_str(indent))
        # return_type is ensured not to be None or reference
        mof.append(moftype(self.return_type, None))
        mof.append(u' ')
        mof.append(self.name)

        if self.parameters.values():
            mof.append(u'(\n')

            mof_parms = []
            for p in self.parameters.itervalues():
                mof_parms.append(p.tomof(indent + MOF_INDENT, maxline))
            mof.append(u',\n'.join(mof_parms))

            mof.append(u');\n')
        else:
            mof.append(u'();\n')

        return u''.join(mof)

# === BLOCK 5 (label=lm, source_idx=line4248_lm, name=compose) ===
def compose(self, bbox=None, **kwargs):
        """
        Compose the artboard.

        See :py:func:`~psd_tools.compose` for available extra arguments.

        :param bbox: Viewport tuple (left, top, right, bottom).
        :return: :py:class:`PIL.Image`, or `None` if there is no pixel.
        """
        return compose(self, bbox=bbox, **kwargs)

# === BLOCK 6 (label=lm, source_idx=line6618_lm, name=_parse_mode) ===
def _parse_mode(mode):
    """
    Converts ls mode output (rwxrwxrwx) -> integer (755).
    """
    return int(mode[0], 8)
