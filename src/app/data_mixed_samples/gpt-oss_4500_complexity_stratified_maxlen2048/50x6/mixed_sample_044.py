# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line376_human, name=_fulfillment_from_details) ===
def _fulfillment_from_details(data, _depth=0):
    """Load a fulfillment for a signing spec dictionary

    Args:
        data: tx.output[].condition.details dictionary
    """
    if _depth == 100:
        raise ThresholdTooDeep()

    if data['type'] == 'ed25519-sha-256':
        public_key = base58.b58decode(data['public_key'])
        return Ed25519Sha256(public_key=public_key)

    if data['type'] == 'threshold-sha-256':
        threshold = ThresholdSha256(data['threshold'])
        for cond in data['subconditions']:
            cond = _fulfillment_from_details(cond, _depth+1)
            threshold.add_subfulfillment(cond)
        return threshold

    raise UnsupportedTypeError(data.get('type'))

# === BLOCK 2 (label=human, source_idx=line6832_human, name=_serializeNT) ===
def _serializeNT(data):
    """
    Serialize namedtuples (and other basic python types) to dictionary with
    some special properties.

    Args:
        data (namedtuple/other python types): Data which will be serialized to
             dict.

    Data can be later automatically de-serialized by calling _deserializeNT().
    """
    if isinstance(data, list):
        return [_serializeNT(item) for item in data]

    elif isinstance(data, tuple) and hasattr(data, "_fields"):  # is namedtuple
        serialized = _serializeNT(dict(data._asdict()))
        serialized["__nt_name"] = data.__class__.__name__

        return serialized

    elif isinstance(data, tuple):
        return tuple(_serializeNT(item) for item in data)

    elif isinstance(data, dict):
        return {
            key: _serializeNT(data[key])
            for key in data
        }

    return data

# === BLOCK 3 (label=lm, source_idx=line721_lm, name=new_session) ===
def new_session(self, user_name=None, session_name=None,
                    kill_existing=False, analytics=None):
        """Create a new test session.

        The test session is identified by the specified user_name and optional
        session_name parameters.  If a session name is not specified, then the
        server will create one.

        Arguments:
        user_name     -- User name part of session ID.
        session_name  -- Session name part of session ID.
        kill_existing -- If there is an existing session, with the same session
                         name and user name, then terminate it before creating
                         a new session
        analytics     -- Optional boolean value to disable or enable analytics
                         for new session.  None will use setting configured on
                         server.

        Return:
        True is session started, False if session was already started.

        """

# === BLOCK 4 (label=lm, source_idx=line2386_lm, name=update_connector_resource) ===
def update_connector_resource(name, server=None, **kwargs):
    """
    Update a connection resource
    """
    if server is None:
        raise ValueError("server must be provided")
    # Try common update method signatures on the server object
    for method_name in ("update_connector_resource", "update_resource", "update"):
        if hasattr(server, method_name):
            method = getattr(server, method_name)
            if callable(method):
                return method(name, **kwargs)
    # Fallback: treat server as a mutable mapping of resources
    if isinstance(server, dict):
        if name not in server:
            raise KeyError(f"Resource {name!r} not found")
        resource = server[name]
        if not isinstance(resource, dict):
            raise TypeError("Resource must be a dict to apply updates")
        resource.update(kwargs)
        return resource
    raise

# === BLOCK 5 (label=lm, source_idx=line5456_lm, name=overwrites) ===
def overwrites(self):
        """Returns all of the channel's overwrites.

        This is returned as a dictionary where the key contains the target which
        can be either a :class:`Role` or a :class:`Member` and the key is the
        overwrite as a :class:`PermissionOverwrite`.

        Returns
        --------
        Mapping[Union[:class:`Role`, :class:`Member`], :class:`PermissionOverwrite`]:
            The channel's permission overwrites.
        """
        overwrites = getattr(self, "_overwrites", None)
        if overwrites is None:
            return {}
        return dict(overwrites)

# === BLOCK 6 (label=human, source_idx=line1331_human, name=main) ===
def main():
    """Run the core."""
    parser = ArgumentParser()
    subs = parser.add_subparsers(dest='cmd')

    setup_parser = subs.add_parser('test')
    setup_parser.add_argument('--interface', default=None,
                              help='Manually pass in the USB connection.')
    args = parser.parse_args()

    if args.cmd == 'test':
        ht = Hottop()
        try:
            if args.interface:
                ht.connect(interface=args.interface)
            ht.connect()
        except SerialConnectionError as e:
            print("[!] Serial interface not accessible: %s" % str(e))
            sys.exit(1)
        print("[*] Successfully connected to the roaster!")
