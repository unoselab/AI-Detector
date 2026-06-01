# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2665_lm, name=refresh_fqdn_cache) ===
def refresh_fqdn_cache(force=False):
    """
    Force refreshes all FQDNs used in rules.

    force
        Forces all fqdn refresh

    CLI Example:

    .. code-block:: bash

        salt '*' panos.refresh_fqdn_cache
        salt '*' panos.refresh_fqdn_cache force=True

    """
    if not force:
        if not __salt__["panos.is_panorama"]():
            return False

    return __salt__["panos.refresh_fqdn_cache"](force=force)

# === BLOCK 2 (label=lm, source_idx=line1212_lm, name=_get_column) ===
def _get_column(self, column_or_label):
        """Convert label to column and check column length."""
        if isinstance(column_or_label, int):
            column = column_or_label
        else:
            column = self.columns.get_loc(column_or_label)
        if column >= self.shape[1]:
            raise ValueError(
                "Column index out of range: %d, %d columns total"
                % (column, self.shape[1])
            )
        return column

# === BLOCK 3 (label=lm, source_idx=line1215_lm, name=list_nodes_min) ===
def list_nodes_min():
    """
    Return a list of registered VMs, with minimal information

    CLI Example:

    .. code-block:: bash

        salt '*' vboxmanage.list_nodes_min
    """
    return _list_nodes(min_info=True)

# === BLOCK 4 (label=lm, source_idx=line529_lm, name=profile_tilt) ===
def profile_tilt(data, mask):
    """Fit a 2D tilt to `data[mask]`"""
    x = data.x[mask]
    y = data.y[mask]
    z = data.z[mask]
    x_mean = x.mean()
    y_mean = y.mean()
    z_mean = z.mean()
    x_std = x.std()
    y_std = y.std()
    z_std = z.std()
    x_tilt = (x - x_mean) / x_std
    y_tilt = (y - y_mean) / y_std
    z_tilt = (z - z_mean) / z_std
    return x_tilt, y_tilt, z_tilt

# === BLOCK 5 (label=lm, source_idx=line1674_lm, name=clean_dataframe) ===
def clean_dataframe(df):
    """Fill NaNs with the previous value, the next value or if all are NaN then 1.0"""
    df.fillna(method='ffill', inplace=True)
    df.fillna(method='bfill', inplace=True)
    df.fillna(1.0, inplace=True)
    return df

# === BLOCK 6 (label=lm, source_idx=line4125_lm, name=_acquire_request_connection) ===
def _acquire_request_connection(self, request):
        """Return a connection."""
        if request.method == 'GET':
            return self.pool.get_connection(self.pool.get_connection_key(request))
        else:
            return self.pool.get_connection(self.pool.get_connection_key(request, 'write'))
