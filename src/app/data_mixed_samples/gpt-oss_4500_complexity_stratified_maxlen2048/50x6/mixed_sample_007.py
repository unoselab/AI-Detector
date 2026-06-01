# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1848_lm, name=deep_compare) ===
def deep_compare(obj1, obj2):
    """
    >>> deep_compare({'1': None}, {})
    False
    >>> deep_compare({'1': {}}, {'1': None})
    False
    >>> deep_compare({'1': [1]}, {'1': [2]})
    False
    >>> deep_compare({'1': 2}, {'1': '2'})
    True
    >>> deep_compare({'1': {'2': [3, 4]}}, {'1': {'2': [3, 4]}})
    True
    """
    if isinstance(obj1, dict) and isinstance(obj2, dict):
        if obj1.keys() != obj2.keys():
            return False
        return all(deep_compare(obj1[k], obj2[k]) for k in obj1)
    if isinstance(obj1, (list, tuple)) and isinstance(obj2, (list, tuple)):
        if len(obj1) != len(obj2):
            return False
        return

# === BLOCK 2 (label=human, source_idx=line3184_human, name=stop) ===
def stop(cls):
        """Change back the normal stdout after the end"""
        if any(cls.streams):
            sys.stdout = cls.streams.pop(-1)
        else:
            sys.stdout = sys.__stdout__

# === BLOCK 3 (label=human, source_idx=line6787_human, name=install) ===
def install(bld):
	"""installs the build files"""
	bld=check_configured(bld)
	Options.commands['install']=True
	Options.commands['uninstall']=False
	Options.is_install=True
	bld.is_install=INSTALL
	build_impl(bld)
	bld.install()

# === BLOCK 4 (label=lm, source_idx=line4011_lm, name=_get_previous_mz) ===
def _get_previous_mz(self, mzs):
        """given an mz array, return the mz_data (disk location)
        if the mz array was not previously written, write to disk first"""
        import os, hashlib, numpy as np

        # Ensure the mz array is a NumPy array
        mz_array = np.asarray(mzs)

        # Compute a stable hash based on dtype, shape and raw bytes
        hasher = hashlib.sha256()
        hasher.update(mz_array.dtype.str.encode())
        hasher.update(mz_array.shape.__repr__().encode())
        hasher.update(mz_array.tobytes())
        mz_hash = hasher.hexdigest()

        # Initialize cache dict if not present
        if not hasattr(self, "_mz_cache"):
            self._mz_cache = {}

        # Return cached location if we have seen this array before
        if mz_hash in self._mz_cache:
            return self._mz_cache[mz_hash]

        # Determine directory to store mz data
        mz_dir = getattr(self, "_mz_dir", ".")
        os.makedirs(mz_dir, exist_ok=True)

        # Build file path using the hash
        file_path = os.path.join(mz_dir, f"{mz_hash}.npy")

        # Write the array

# === BLOCK 5 (label=lm, source_idx=line2872_lm, name=_send) ===
def _send(self, command):
        """
        Sends a raw line to the server.

        :param command: line to send.
        :type command: unicode
        """
        if not isinstance(command, str):
            raise TypeError("command must be a unicode string")
        # Ensure the line ends with CRLF as required by the protocol
        line = command.rstrip("\r\n") + "\r\n"
        data = line.encode("utf-8")
        # Send the data; use sendall to guarantee the whole message is transmitted
        self.socket.sendall(data)

# === BLOCK 6 (label=human, source_idx=line1625_human, name=create_tcp_socket) ===
def create_tcp_socket (self, host):
        """Create tcp socket, connect to it and return socket object."""
        port = int(self['TCPSocket'])
        sockinfo = get_sockinfo(host, port=port)
        sock = create_socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.connect(sockinfo[0][4])
        except socket.error:
            sock.close()
            raise
        return sock
