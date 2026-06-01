# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3155_human, name=logical_lines) ===
def logical_lines(lines):
    """Merge lines into chunks according to q rules"""
    if isinstance(lines, string_types):
        lines = StringIO(lines)
    buf = []
    for line in lines:
        if buf and not line.startswith(' '):
            chunk = ''.join(buf).strip()
            if chunk:
                yield chunk
            buf[:] = []

        buf.append(line)
    chunk = ''.join(buf).strip()
    if chunk:
        yield chunk

# === BLOCK 2 (label=lm, source_idx=line4615_lm, name=get_urlclass_from) ===
def get_urlclass_from (scheme, assume_local_file=False):
    """Return checker class for given URL scheme. If the scheme
    cannot be matched and assume_local_file is True, assume a local file.
    """

# === BLOCK 3 (label=lm, source_idx=line2892_lm, name=finish_plot) ===
def finish_plot():
    """Helper for plotting."""
    import matplotlib.pyplot as plt
    plt.tight_layout()
    plt.show()

# === BLOCK 4 (label=human, source_idx=line5791_human, name=_clear) ===
def _clear(self):
        """Resets all assigned data for the current message."""
        self._finished = False
        self._measurement = None
        self._message = None
        self._message_body = None

# === BLOCK 5 (label=human, source_idx=line5215_human, name=create) ===
def create(gandi, fqdn, name, type, value, ttl):
    """Create new record entry for a domain.

    multiple value parameters can be provided.
    """
    domains = gandi.dns.list()
    domains = [domain['fqdn'] for domain in domains]
    if fqdn not in domains:
        gandi.echo('Sorry domain %s does not exist' % fqdn)
        gandi.echo('Please use one of the following: %s' % ', '.join(domains))
        return

    result = gandi.dns.add_record(fqdn, name, type, value, ttl)
    gandi.echo(result['message'])

# === BLOCK 6 (label=lm, source_idx=line5391_lm, name=order) ===
def order(self, order):
    """Adds an Order to this query.

    Args:
      see :py:class:`Order <datastore.query.Order>` constructor

    Returns self for JS-like method chaining::

      query.order('+age').order('-home')

    """
    self._orders = []
self._orders.append(order)
return self
