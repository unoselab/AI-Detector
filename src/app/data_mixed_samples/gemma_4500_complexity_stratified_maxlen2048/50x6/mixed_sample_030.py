# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1866_lm, name=sense) ===
def sense(self):
        """
            Launches a few "sensing" commands such as 'ls', or 'pwd'
            and updates the current bait state.
        """
        commands = ['pwd', 'ls', 'whoami', 'uname -a']
        for cmd in commands:
            try:
                result = self.execute(cmd)
                self.state[cmd] = result
            except Exception as e:
                self.state[cmd] = f"Error: {str(e)}"

# === BLOCK 2 (label=human, source_idx=line1974_human, name=next_trials) ===
def next_trials(self):
        """Provides a batch of Trial objects to be queued into the TrialRunner.

        A batch ends when self._trial_generator returns None.

        Returns:
            trials (list): Returns a list of trials.
        """
        trials = []

        for trial in self._trial_generator:
            if trial is None:
                return trials
            trials += [trial]

        self._finished = True
        return trials

# === BLOCK 3 (label=lm, source_idx=line7679_lm, name=_connect) ===
def _connect(host=None, port=None, db=None, password=None):
    """
    Returns an instance of the redis client
    """
    import redis
    return redis.Redis(host=host, port=port, db=db, password=password)

# === BLOCK 4 (label=lm, source_idx=line3278_lm, name=save) ===
def save(self, file_path):
        """Save epw object as an epw file.

        args:
            file_path: A string representing the path to write the epw file to.
        """
        f.write(self.to_epw_string())

# === BLOCK 5 (label=human, source_idx=line6772_human, name=add_platform) ===
def add_platform(name, platform_set, server_url):
    """
    To add an ASAM platform using the specified ASAM platform set on the Novell
    Fan-Out Driver

    CLI Example:

    .. code-block:: bash

        salt-run asam.add_platform my-test-vm test-platform-set prov1.domain.com
    """
    config = _get_asam_configuration(server_url)
    if not config:
        return False

    platforms = list_platforms(server_url)
    if name in platforms[server_url]:
        return {name: "Specified platform already exists on {0}".format(server_url)}

    platform_sets = list_platform_sets(server_url)
    if platform_set not in platform_sets[server_url]:
        return {name: "Specified platform set does not exist on {0}".format(server_url)}

    url = config['platform_edit_url']

    data = {
        'platformName': name,
        'platformSetName': platform_set,
        'manual': 'false',
        'previousURL': '/config/platformAdd.html',
        'postType': 'PlatformAdd',
        'Submit': 'Apply'
    }

    auth = (
        config['username'],
        config['password']
    )

    try:
        html_content = _make_post_request(url, data, auth, verify=False)
    except Exception as exc:
        err_msg = "Failed to add platform on {0}".format(server_url)
        log.error('%s:\n%s', err_msg, exc)
        return {name: err_msg}

    platforms = list_platforms(server_url)
    if name in platforms[server_url]:
        return {name: "Successfully added platform on {0}".format(server_url)}
    else:
        return {name: "Failed to add platform on {0}".format(server_url)}

# === BLOCK 6 (label=human, source_idx=line1639_human, name=_setuint) ===
def _setuint(self, uint, length=None):
        """Reset the bitstring to have given unsigned int interpretation."""
        try:
            if length is None:
                # Use the whole length. Deliberately not using .len here.
                length = self._datastore.bitlength
        except AttributeError:
            # bitstring doesn't have a _datastore as it hasn't been created!
            pass
        # TODO: All this checking code should be hoisted out of here!
        if length is None or length == 0:
            raise CreationError("A non-zero length must be specified with a "
                                "uint initialiser.")
        if uint >= (1 << length):
            msg = "{0} is too large an unsigned integer for a bitstring of length {1}. "\
                  "The allowed range is [0, {2}]."
            raise CreationError(msg, uint, length, (1 << length) - 1)
        if uint < 0:
            raise CreationError("uint cannot be initialsed by a negative number.")
        s = hex(uint)[2:]
        s = s.rstrip('L')
        if len(s) & 1:
            s = '0' + s
        try:
            data = bytes.fromhex(s)
        except AttributeError:
            # the Python 2.x way
            data = binascii.unhexlify(s)
        # Now add bytes as needed to get the right length.
        extrabytes = ((length + 7) // 8) - len(data)
        if extrabytes > 0:
            data = b'\x00' * extrabytes + data
        offset = 8 - (length % 8)
        if offset == 8:
            offset = 0
        self._setbytes_unsafe(bytearray(data), length, offset)
