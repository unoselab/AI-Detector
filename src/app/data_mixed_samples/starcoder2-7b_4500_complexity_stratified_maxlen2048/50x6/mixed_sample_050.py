# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line128_lm, name=write_channel) ===
def write_channel(self, out_data):
        """Generic handler that will write to both SSH and telnet channel.

        :param out_data: data to be written to the channel
        :type out_data: str (can be either unicode/byte string)
        """
        if self.ssh_channel:
            self.ssh_channel.write(out_data)
        if self.telnet_channel:
            self.telnet_channel.write(out_data)

# === BLOCK 2 (label=human, source_idx=line3139_human, name=get_stats_code_frequency) ===
def get_stats_code_frequency(self):
        """
        :calls: `GET /repos/:owner/:repo/stats/code_frequency <http://developer.github.com/v3/repos/statistics/#get-the-number-of-additions-and-deletions-per-week>`_
        :rtype: None or list of :class:`github.StatsCodeFrequency.StatsCodeFrequency`
        """
        headers, data = self._requester.requestJsonAndCheck(
            "GET",
            self.url + "/stats/code_frequency"
        )
        if not data:
            return None
        else:
            return [
                github.StatsCodeFrequency.StatsCodeFrequency(self._requester, headers, attributes, completed=True)
                for attributes in data
            ]

# === BLOCK 3 (label=lm, source_idx=line1421_lm, name=tally) ===
def tally(self, name, value):
        """Adds to the "used" metric for the given quota."""
        self.used[name] = self.used.get(name, 0) + value

# === BLOCK 4 (label=human, source_idx=line4351_human, name=license_install) ===
def license_install(self, license_file):
        """
        Install a new license.

        :param str license_file: fully qualified path to the
            license jar file.
        :raises: ActionCommandFailed
        :return: None
        """
        self.make_request(
            method='update',
            resource='license_install',
            files={
                'license_file': open(license_file, 'rb')
            })

# === BLOCK 5 (label=lm, source_idx=line2915_lm, name=centroid_refine_triangulation_by_triangles) ===
def centroid_refine_triangulation_by_triangles(self, triangles):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation that are associated with the triangles in the list provided.

        Notes
        -----
         The triangles are here represented as a single index.
         The vertices of triangle i are given by self.simplices[i].
        """
        # TODO: this is a very inefficient implementation.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It would be better to use the adjacency matrix of the triangulation.
        #       This is a bit more complicated to implement.
        #       It

# === BLOCK 6 (label=human, source_idx=line3458_human, name=_compose) ===
def _compose(self, name, args, mkdir=True):
        """Get a named filesystem entry, and extend it into a path with additional
        path arguments"""
        from os.path import normpath
        from ambry.dbexceptions import ConfigurationError

        root = p = self._config.filesystem[name].format(root=self._root)

        if args:
            args = [e.strip() for e in args]
            p = join(p, *args)

        if not isdir(p) and mkdir:
            makedirs(p)

        p = normpath(p)

        if not p.startswith(root):
            raise ConfigurationError("Path for name='{}', args={} resolved outside of define filesystem root"
                                 .format(name, args))

        return p
