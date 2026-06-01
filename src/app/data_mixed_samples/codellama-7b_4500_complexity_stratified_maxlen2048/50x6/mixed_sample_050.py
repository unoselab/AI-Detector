# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line136_lm, name=service_name_from_scope_name) ===
def service_name_from_scope_name(scope_name):
    """Translate scope name to service name which can be used in dns.

    230 = 253 - len('replica.') - len('.service.consul')
    """
    return scope_name[len('replica.'):-len('.service.consul')]

# === BLOCK 2 (label=human, source_idx=line3644_human, name=clean_text) ===
def clean_text(self, domain, **kwargs):
        """Try to extract only the domain bit from the """
        try:
            # handle URLs by extracting the domain name
            domain = urlparse(domain).hostname or domain
            domain = domain.lower()
            # get rid of port specs
            domain = domain.rsplit(':', 1)[0]
            domain = domain.rstrip('.')
            # handle unicode
            domain = domain.encode("idna").decode('ascii')
        except ValueError:
            return None
        if self.validate(domain):
            return domain

# === BLOCK 3 (label=lm, source_idx=line1620_lm, name=serialize) ===
def serialize(ms, version=_default_version, properties=True,
              pretty_print=False, color=False):
    """Serialize an MRS structure into a SimpleMRS string."""
    if version is _default_version:
        version = ms.version
    if version is None:
        version = _default_version
    if version not in _serializers:
        raise ValueError("Unknown MRS version: %s" % version)
    return _serializers[version](ms, properties, pretty_print, color)

# === BLOCK 4 (label=human, source_idx=line5277_human, name=parse_block) ===
def parse_block(self, block_id, txs):
        """
        Given the sequence of transactions in a block, turn them into a
        sequence of virtual chain operations.

        Return the list of successfully-parsed virtualchain transactions
        """
        ops = []
        for i in range(0,len(txs)):
            tx = txs[i]
            op = self.parse_transaction(block_id, tx)
            if op is not None:
                ops.append( op )

        return ops

# === BLOCK 5 (label=lm, source_idx=line3386_lm, name=unhook) ===
def unhook(self, addr):
        """
        Remove a hook.

        :param addr:    The address of the hook.
        """
        self.hooks.pop(addr, None)

# === BLOCK 6 (label=human, source_idx=line4025_human, name=geojson) ===
def geojson(self, feature_id):
        """GeoJSON representation of the marker as a point."""
        lat, lon = self.lat_lon
        return {
            'type': 'Feature',
            'id': feature_id,
            'geometry': {
                'type': 'Point',
                'coordinates': (lon, lat),
            },
        }
