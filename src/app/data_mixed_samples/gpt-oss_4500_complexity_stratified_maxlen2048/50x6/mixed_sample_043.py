# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6393_lm, name=_disconnect) ===
def _disconnect(self, mqttc, userdata, rc):
        """
        The callback for when a DISCONNECT occurs.

        :param mqttc: The client instance for this callback
        :param userdata: The private userdata for the mqtt client. Not used in Polyglot
        :param rc: Result code of connection, 0 = Graceful, anything else is unclean
        """
        # Mark the client as disconnected
        setattr(self, "_connected", False)

        # Determine logging facilities
        logger = getattr(self, "logger", None)
        if logger is None:
            # Fallback to a simple print if no logger is configured
            def _log(level, msg):
                print(f"[{level}] {msg}")
        else:
            def _log(level, msg):
                getattr(logger, level, logger.info)(msg)

        if rc == 0:
            _log("info", "MQTT client disconnected gracefully.")
        else:
            _log("warning", f"MQTT client disconnected unexpectedly (rc={rc}).")

            # Attempt automatic reconnection if the class provides a reconnect method
            reconnect = getattr(self, "_reconnect", None)
            if callable(reconnect):
                try:
                    reconnect()
                    _log("info", "Reconnection attempt initiated.")
                except Exception as exc:  # pragma: no cover
                    _log("error", f"Reconnection failed: {exc}")

# === BLOCK 2 (label=lm, source_idx=line6041_lm, name=get_rate_from_db) ===
def get_rate_from_db(currency: str) -> Decimal:
    """
    Fetch currency conversion rate from the database
    """
    from decimal import Decimal
    import sqlite3

    conn = sqlite3.connect('currency_rates.db')
    try:
        cur = conn.execute(
            "SELECT rate FROM rates WHERE currency = ?",
            (currency.upper(),)
        )
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"Rate for currency '{currency}' not found")
        # Ensure the rate is converted to Decimal accurately
        return Decimal(str(row[0]))
    finally:
        conn.close()

# === BLOCK 3 (label=human, source_idx=line3884_human, name=decode_network) ===
def decode_network(objects):
    """Return root object from ref-containing obj table entries"""
    def resolve_ref(obj, objects=objects):
        if isinstance(obj, Ref):
            # first entry is 1
            return objects[obj.index - 1]
        else:
            return obj

    # Reading the ObjTable backwards somehow makes more sense.
    for i in xrange(len(objects)-1, -1, -1):
        obj = objects[i]

        if isinstance(obj, Container):
            obj.update((k, resolve_ref(v)) for (k, v) in obj.items())

        elif isinstance(obj, Dictionary):
            obj.value = dict(
                (resolve_ref(field), resolve_ref(value))
                for (field, value) in obj.value.items()
            )

        elif isinstance(obj, dict):
            obj = dict(
                (resolve_ref(field), resolve_ref(value))
                for (field, value) in obj.items()
            )

        elif isinstance(obj, list):
            obj = [resolve_ref(field) for field in obj]

        elif isinstance(obj, Form):
            for field in obj.value:
                value = getattr(obj, field)
                value = resolve_ref(value)
                setattr(obj, field, value)

        elif isinstance(obj, ContainsRefs):
            obj.value = [resolve_ref(field) for field in obj.value]

        objects[i] = obj

    for obj in objects:
        if isinstance(obj, Form):
            obj.built()

    root = objects[0]
    return root

# === BLOCK 4 (label=lm, source_idx=line516_lm, name=checksum) ===
def checksum(symbol, doc):
    """
    Checksum the passed in dictionary
    """
    import hashlib, json
    if not isinstance(doc, dict):
        raise TypeError("doc must be a dictionary")
    # Ensure deterministic ordering of keys
    serialized = json.dumps(doc, sort_keys=True, separators=(',', ':'))
    # Include the symbol in the checksum to differentiate contexts
    payload = f"{symbol}:{serialized}".encode('utf-8')
    return hashlib.sha256(payload).hexdigest()

# === BLOCK 5 (label=human, source_idx=line1751_human, name=bisect_left) ===
def bisect_left(self, val):
        """
        Similar to the *bisect* module in the standard library, this returns an
        appropriate index to insert *val*. If *val* is already present, the
        insertion point will be before (to the left of) any existing entries.
        """
        _maxes = self._maxes

        if not _maxes:
            return 0

        pos = bisect_left(_maxes, val)

        if pos == len(_maxes):
            return self._len

        idx = bisect_left(self._lists[pos], val)

        return self._loc(pos, idx)

# === BLOCK 6 (label=human, source_idx=line460_human, name=bearing_to) ===
def bearing_to(self, point):
        """
        Return the bearing to another point.

        :param point: Point to measure bearing to
        :type point: Point

        :returns: The bearing to the other point
        :rtype: Bearing
        """
        delta_long = point.long_radians - self.long_radians
        y = sin(delta_long) * cos(point.lat_radians)
        x = (
            cos(self.lat_radians) * sin(point.lat_radians) -
            sin(self.lat_radians) * cos(point.lat_radians) * cos(delta_long)
        )
        radians = math.atan2(y, x)
        return Bearing.from_radians(radians)
