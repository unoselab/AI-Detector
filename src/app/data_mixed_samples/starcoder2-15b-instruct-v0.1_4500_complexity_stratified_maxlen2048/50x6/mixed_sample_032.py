# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3658_lm, name=make_label) ===
def make_label(self, path):
        """
        this borrows too much from the internals of ofs
        maybe expose different parts of the api?
        """
        return f"ofs://{self.ofs_host}:{self.ofs_port}/{path}"

# === BLOCK 2 (label=human, source_idx=line832_human, name=enable) ===
def enable(ctx):
    """Enable an existing user"""

    if ctx.obj['username'] is None:
        log('Specify the username with "iso db user --username ..."')
        return

    change_user = ctx.obj['db'].objectmodels['user'].find_one({
        'name': ctx.obj['username']
    })

    change_user.active = True
    change_user.save()
    log('Done')

# === BLOCK 3 (label=human, source_idx=line3152_human, name=_se_all) ===
def _se_all(self):
        """Standard errors (SE) for all parameters, including the intercept."""
        x = np.atleast_2d(self.x)
        err = np.atleast_1d(self.ms_err)
        se = np.sqrt(np.diagonal(np.linalg.inv(x.T @ x)) * err[:, None])
        return np.squeeze(se)

# === BLOCK 4 (label=lm, source_idx=line2896_lm, name=set_constraint_bound) ===
def set_constraint_bound(self, name, value):
        """Set the upper bound of a constraint."""
        if name not in self.constraints:
            raise ValueError(f"Constraint {name} not found.")
        self.constraints[name].upper_bound = value

# === BLOCK 5 (label=human, source_idx=line2590_human, name=get_power_state) ===
def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        LOG.debug('Querying power stat of %s' % userid)
        requestData = "PowerVM " + userid + " status"
        action = "query power state of '%s'" % userid
        with zvmutils.log_and_reraise_smt_request_failed(action):
            results = self._request(requestData)
        with zvmutils.expect_invalid_resp_data(results):
            status = results['response'][0].partition(': ')[2]
        return status

# === BLOCK 6 (label=lm, source_idx=line1938_lm, name=find_overlapping_slots) ===
def find_overlapping_slots(all_slots):
    """Find any slots that overlap"""
    overlapping_slots = []
    for i in range(len(all_slots)):
        for j in range(i + 1, len(all_slots)):
            if all_slots[i].start_time < all_slots[j].end_time and all_slots[i].end_time > all_slots[j].start_time:
                overlapping_slots.append((all_slots[i], all_slots[j]))
    return overlapping_slots
