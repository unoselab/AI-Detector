# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6229_human, name=download_series_gui) ===
def download_series_gui(frame, urls, directory, min_file_size, max_file_size, no_redirects):
	"""
	called when user wants serial downloading
	"""

	# create directory to save files
	if not os.path.exists(directory):
		os.makedirs(directory)
	app = progress_class(frame, urls, directory, min_file_size, max_file_size, no_redirects)

# === BLOCK 2 (label=lm, source_idx=line2283_lm, name=set_encode_key_value) ===
def set_encode_key_value(self, value, store_type):
        """Save the key value base on it's storage type."""
        if store_type == 'memory':
            self.memory_store[self.key] = value
        elif store_type == 'disk':
            self.disk_store.save(self.key, value)
        else:
            raise ValueError(f"Unsupported store_type: {store_type}")

# === BLOCK 3 (label=lm, source_idx=line3836_lm, name=_iterbfs) ===
def _iterbfs(self, start, end=None, forward=True):
        """
        The forward parameter specifies whether it is a forward or backward
        traversal.  Returns a list of tuples where the first value is the hop
        value the second value is the node id.
        """
        queue = [(0, start)]
        visited = {start}
        result = []

        while queue:
            dist, node = queue.pop(0)
            result.append((dist, node))

            if end is not None and node == end:
                return result

            neighbors = self.get_neighbors(node, forward) if hasattr(self, 'get_neighbors') else []
            for neighbor in neighbors:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((dist + 1, neighbor))

        return result

# === BLOCK 4 (label=lm, source_idx=line3493_lm, name=wrap_get_user) ===
def wrap_get_user(cls, response):
        """Wrap the response from getting a user into an instance
        and return it

        :param response: The response from getting a user
        :type response: :class:`requests.Response`
        :returns: the new user instance
        :rtype: :class:`list` of :class:`User`
        :raises: None
        """
        data = response.json()
        if isinstance(data, list):
            return [cls(**user) for user in data]
        return [cls(**data)]

# === BLOCK 5 (label=human, source_idx=line5806_human, name=dict2DingoObjDict) ===
def dict2DingoObjDict(data):
    """
    Turn a dictionary of the form used by DINGO
    (i.e., a key is mapped to either another dictionary,
    a list or a value) into a DingoObjDict.
    """
    info_tuple = dict2tuple(data)
    info_dict = tuple2dict(info_tuple, constructor=DingoObjDict)
    return info_dict

# === BLOCK 6 (label=human, source_idx=line5672_human, name=remove_nio) ===
def remove_nio(self, port_number):
        """
        Removes the specified NIO as member of this ATM switch.

        :param port_number: allocated port number
        """

        if port_number not in self._nios:
            raise DynamipsError("Port {} is not allocated".format(port_number))

        # remove VCs mapped with the port
        for source, destination in self._active_mappings.copy().items():
            if len(source) == 3 and len(destination) == 3:
                # remove the virtual channels mapped with this port/nio
                source_port, source_vpi, source_vci = source
                destination_port, destination_vpi, destination_vci = destination
                if port_number == source_port:
                    log.info('ATM switch "{name}" [{id}]: unmapping VCC between port {source_port} VPI {source_vpi} VCI {source_vci} and port {destination_port} VPI {destination_vpi} VCI {destination_vci}'.format(name=self._name,
                                                                                                                                                                                                                     id=self._id,
                                                                                                                                                                                                                     source_port=source_port,
                                                                                                                                                                                                                     source_vpi=source_vpi,
                                                                                                                                                                                                                     source_vci=source_vci,
                                                                                                                                                                                                                     destination_port=destination_port,
                                                                                                                                                                                                                     destination_vpi=destination_vpi,
                                                                                                                                                                                                                     destination_vci=destination_vci))
                    yield from self.unmap_pvc(source_port, source_vpi, source_vci, destination_port, destination_vpi, destination_vci)
                    yield from self.unmap_pvc(destination_port, destination_vpi, destination_vci, source_port, source_vpi, source_vci)
            else:
                # remove the virtual paths mapped with this port/nio
                source_port, source_vpi = source
                destination_port, destination_vpi = destination
                if port_number == source_port:
                    log.info('ATM switch "{name}" [{id}]: unmapping VPC between port {source_port} VPI {source_vpi} and port {destination_port} VPI {destination_vpi}'.format(name=self._name,
                                                                                                                                                                              id=self._id,
                                                                                                                                                                              source_port=source_port,
                                                                                                                                                                              source_vpi=source_vpi,
                                                                                                                                                                              destination_port=destination_port,
                                                                                                                                                                              destination_vpi=destination_vpi))
                    yield from self.unmap_vp(source_port, source_vpi, destination_port, destination_vpi)
                    yield from self.unmap_vp(destination_port, destination_vpi, source_port, source_vpi)

        nio = self._nios[port_number]
        if isinstance(nio, NIOUDP):
            self.manager.port_manager.release_udp_port(nio.lport, self._project)
        log.info('ATM switch "{name}" [{id}]: NIO {nio} removed from port {port}'.format(name=self._name,
                                                                                         id=self._id,
                                                                                         nio=nio,
                                                                                         port=port_number))

        del self._nios[port_number]
        return nio
