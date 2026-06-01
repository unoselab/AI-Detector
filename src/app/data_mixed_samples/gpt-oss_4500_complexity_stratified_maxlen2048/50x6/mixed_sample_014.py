# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6718_lm, name=config_name_from_full_name) ===
def config_name_from_full_name(full_name):
    """Extract the config name from a full resource name.

      >>> config_name_from_full_name('projects/my-proj/configs/my-config')
      "my-config"

    :type full_name: str
    :param full_name:
        The full resource name of a config. The full resource name looks like
        ``projects/project-name/configs/config-name`` and is returned as the
        ``name`` field of a config resource.  See
        https://cloud.google.com/deployment-manager/runtime-configurator/reference/rest/v1beta1/projects.configs

    :rtype: str
    :returns: The config's short name, given its full resource name.
    :raises: :class:`ValueError` if ``full_name`` is not the expected format
    """
    parts = full_name.split('/')
    if len(parts) < 4 or parts[0] != 'projects' or parts[2] != 'configs':
        raise ValueError(f"Invalid config full name: {full_name!r}")
    return parts[3]

# === BLOCK 2 (label=human, source_idx=line3016_human, name=nuc_v) ===
def nuc_v(msg):
    """Calculate NUCv, Navigation Uncertainty Category - Velocity (ADS-B version 1)

    Args:
        msg (string): 28 bytes hexadecimal message string,

    Returns:
        int or string: 95% Horizontal Velocity Error
        int or string: 95% Vertical Velocity Error
    """
    tc = typecode(msg)

    if tc != 19:
        raise RuntimeError("%s: Not an airborne velocity message, expecting TC = 19" % msg)


    msgbin = common.hex2bin(msg)
    NUCv = common.bin2int(msgbin[42:45])

    try:
        HVE = uncertainty.NUCv[NUCv]['HVE']
        VVE = uncertainty.NUCv[NUCv]['VVE']
    except KeyError:
        HVE, VVE = uncertainty.NA, uncertainty.NA

    return HVE, VVE

# === BLOCK 3 (label=lm, source_idx=line1093_lm, name=client_updates_config) ===
def client_updates_config(artwork=True, now_playing=True,
                          volume=True, keyboard=True):
    """Create a new CLIENT_UPDATES_CONFIG_MESSAGE."""
    return {
        "type": "CLIENT_UPDATES_CONFIG_MESSAGE",
        "artwork": artwork,
        "now_playing": now_playing,
        "volume": volume,
        "keyboard": keyboard,
    }

# === BLOCK 4 (label=human, source_idx=line5263_human, name=connect) ===
def connect(
            self, login, password, authz_id=b"", starttls=False,
            authmech=None):
        """Establish a connection with the server.

        This function must be used. It read the server capabilities
        and wraps calls to STARTTLS and AUTHENTICATE commands.

        :param login: username
        :param password: clear password
        :param starttls: use a TLS connection or not
        :param authmech: prefered authenticate mechanism
        :rtype: boolean
        """
        try:
            self.sock = socket.create_connection((self.srvaddr, self.srvport))
            self.sock.settimeout(Client.read_timeout)
        except socket.error as msg:
            raise Error("Connection to server failed: %s" % str(msg))

        if not self.__get_capabilities():
            raise Error("Failed to read capabilities from server")
        if starttls and not self.__starttls():
            return False
        if self.__authenticate(login, password, authz_id, authmech):
            return True
        return False

# === BLOCK 5 (label=lm, source_idx=line6367_lm, name=handler) ===
def handler(key_file=None, cert_file=None, timeout=None, verify=False):
    """This class returns an instance of the default HTTP request handler using
    the values you provide.

    :param `key_file`: A path to a PEM (Privacy Enhanced Mail) formatted file containing your private key (optional).
    :type key_file: ``string``
    :param `cert_file`: A path to a PEM (Privacy Enhanced Mail) formatted file containing a certificate chain file (optional).
    :type cert_file: ``string``
    :param `timeout`: The request time-out period, in seconds (optional).
    :type timeout: ``integer`` or "None"
    :param `verify`: Set to False to disable SSL verification on https connections.
    :type verify: ``Boolean``
    """

# === BLOCK 6 (label=human, source_idx=line5131_human, name=bgrewriteaof) ===
def bgrewriteaof(host=None, port=None, db=None, password=None):
    """
    Asynchronously rewrite the append-only file

    CLI Example:

    .. code-block:: bash

        salt '*' redis.bgrewriteaof
    """
    server = _connect(host, port, db, password)
    return server.bgrewriteaof()
