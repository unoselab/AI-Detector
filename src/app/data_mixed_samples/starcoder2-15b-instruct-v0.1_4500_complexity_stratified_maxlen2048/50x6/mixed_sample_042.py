# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4311_human, name=get_absolute) ===
def get_absolute(self, points):
        """Given a set of points geo referenced to this instance,
        return the points as absolute values.
        """

        # remember if we got a list
        is_list = isinstance(points, list)

        points = ensure_numeric(points, num.float)
        if len(points.shape) == 1:
            # One point has been passed
            msg = 'Single point must have two elements'
            if not len(points) == 2:
                raise ValueError(msg)


        msg = 'Input must be an N x 2 array or list of (x,y) values. '
        msg += 'I got an %d x %d array' %points.shape
        if not points.shape[1] == 2:
            raise ValueError(msg)


        # Add geo ref to points
        if not self.is_absolute():
            points = copy.copy(points) # Don't destroy input
            points[:,0] += self.xllcorner
            points[:,1] += self.yllcorner


        if is_list:
            points = points.tolist()

        return points

# === BLOCK 2 (label=human, source_idx=line3202_human, name=atlas_make_zonefile_inventory) ===
def atlas_make_zonefile_inventory( bit_offset, bit_length, con=None, path=None ):
    """
    Get a summary description of the list of zonefiles we have
    for the given block range (a "zonefile inventory")

    Zonefile present/absent bits are ordered left-to-right,
    where the leftmost bit is the earliest zonefile in the blockchain.

    Offset and length are in bytes.

    This is slow.  Use the in-RAM zonefile inventory vector whenever possible
    (see atlas_get_zonefile_inventory).
    """

    listing = atlasdb_zonefile_inv_list( bit_offset, bit_length, con=con, path=path )

    # serialize to inv
    bool_vec = [l['present'] for l in listing]
    if len(bool_vec) % 8 != 0: 
        # pad 
        bool_vec += [False] * (8 - (len(bool_vec) % 8))

    inv = ""
    for i in xrange(0, len(bool_vec), 8):
        bit_vec = map( lambda b: 1 if b else 0, bool_vec[i:i+8] )
        next_byte = (bit_vec[0] << 7) | \
                    (bit_vec[1] << 6) | \
                    (bit_vec[2] << 5) | \
                    (bit_vec[3] << 4) | \
                    (bit_vec[4] << 3) | \
                    (bit_vec[5] << 2) | \
                    (bit_vec[6] << 1) | \
                    (bit_vec[7])
        inv += chr(next_byte)

    return inv

# === BLOCK 3 (label=lm, source_idx=line2797_lm, name=get_blueprint_params) ===
async def get_blueprint_params(request, left: int, right: int) -> str:
    """
    API Description: Multiply, left * right. This will show in the swagger page (localhost:8000/api/v1/).
    """
    return str(left * right)

# === BLOCK 4 (label=lm, source_idx=line2845_lm, name=get_mapping) ===
def get_mapping(self, doc_type=None, indices=None, raw=False):
        """
        Register specific mapping definition for a specific type against one or more indices.
        (See :ref:`es-guide-reference-api-admin-indices-get-mapping`)

        """
        params = {}

        if doc_type:
            params['type'] = doc_type
        if indices:
            params['index'] = indices
        if raw:
            params['raw'] = raw

        return self.transport.perform_request('GET', '/_mapping', params=params)

# === BLOCK 5 (label=human, source_idx=line3510_human, name=list_scripts) ===
def list_scripts(zap_helper):
    """List scripts currently loaded into ZAP."""
    scripts = zap_helper.zap.script.list_scripts
    output = []
    for s in scripts:
        if 'enabled' not in s:
            s['enabled'] = 'N/A'

        output.append([s['name'], s['type'], s['engine'], s['enabled']])

    click.echo(tabulate(output, headers=['Name', 'Type', 'Engine', 'Enabled'], tablefmt='grid'))

# === BLOCK 6 (label=lm, source_idx=line1268_lm, name=decimal) ===
def decimal(self, var, default=NOTSET, force=True):
        """Convenience method for casting to a decimal.Decimal

        Note:
            Casting
        """
        if var is None:
            return default
        if not isinstance(var, Decimal):
            var = Decimal(var)
        if force:
            var = var.quantize(Decimal('0.00'))
        return var
