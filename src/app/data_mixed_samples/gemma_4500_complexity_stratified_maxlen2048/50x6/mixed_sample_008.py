# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line373_lm, name=_kendall_tau_diff) ===
def _kendall_tau_diff(self, a: np.ndarray, b: np.ndarray, i) -> Tuple[int, int]:
        """Compute difference in concordance of pairs in split sequences.

        Consider splitting a and b at index i.

        Parameters
        ----------
        a
            ?
        b
            ?

        Returns
        -------
        diff_pos
            Difference between concordant pairs for both subsequences.
        diff_neg
            Difference between non-concordant pairs for both subsequences.
        """
        a_left, a_right = a[:i], a[i:]
        b_left, b_right = b[:i], b[i:]

        pos, neg = 0, 0
        for val_a_l, val_b_l in zip(a_left, b_left):
            for val_a_r, val_b_r in zip(a_right, b_right):
                # Check if the pair (l, r) is concordant in both sequences
                # Concordant if (a[l] < a[r] and b[l] < b[r]) or (a[l] > a[r] and b[l] > b[r])
                a_diff = val_a_r - val_a_l
                b_diff = val_b_r - val_b_l

                if a_diff * b_diff > 0:
                    pos += 1
                elif a_diff * b_diff < 0:
                    neg += 1

        return pos, neg

# === BLOCK 2 (label=lm, source_idx=line7676_lm, name=_mkpart) ===
def _mkpart(root, fs_format, fs_opts, mount_dir):
    """
    Make a partition, and make it bootable

    .. versionadded:: Beryllium
    """
    import subprocess

    # This is a conceptual implementation based on common Linux partition/fs tools
    # as the specific environment (Beryllium) implies a specific system context.

    # 1. Format the partition
    # Example: mkfs.ext4 -O fs_opts /dev/partition
    cmd_format = ["mkfs", fs_format]
    if fs_opts:
        cmd_format.extend(["-O", fs_opts])
    cmd_format.append(root)
    subprocess.run(cmd_format, check=True)

    # 2. Create mount directory
    import os
    if not os.path.exists(mount_dir):
        os.makedirs(mount_dir)

    # 3. Mount the partition
    subprocess.run(["mount", root, mount_dir], check=True)

    # 4. Make bootable (Example: setting boot flag via parted or similar)
    # This varies by disk type, but typically involves setting the boot flag
    subprocess.run(["parted", "-s", root, "set", "1", "boot", "on"], check=False)

# === BLOCK 3 (label=human, source_idx=line7391_human, name=update) ===
def update(self, **kwds):
        """
        Endpoint: /photo/<id>/update.json

        Updates this photo with the specified parameters.
        """
        result = self._client.photo.update(self, **kwds)
        self._replace_fields(result.get_fields())

# === BLOCK 4 (label=human, source_idx=line3109_human, name=set_values) ===
def set_values(self, values):
        """expects a list of 2-tuples"""
        self.values = values
        self.height = len(self.values) * 14
        self._max = max(rec[1] for rec in values) if values else dt.timedelta(0)

# === BLOCK 5 (label=human, source_idx=line4431_human, name=format_ring_double_bond) ===
def format_ring_double_bond(mol):
    """Set double bonds around the ring.
    """
    mol.require("Topology")
    mol.require("ScaleAndCenter")
    for r in sorted(mol.rings, key=len, reverse=True):
        vertices = [mol.atom(n).coords for n in r]
        try:
            if geometry.is_clockwise(vertices):
                cpath = iterator.consecutive(itertools.cycle(r), 2)
            else:
                cpath = iterator.consecutive(itertools.cycle(reversed(r)), 2)
        except ValueError:
            continue
        for _ in r:
            u, v = next(cpath)
            b = mol.bond(u, v)
            if b.order == 2:
                b.type = int((u > v) == b.is_lower_first)

# === BLOCK 6 (label=lm, source_idx=line7540_lm, name=_taskdict) ===
def _taskdict(task):
    """
    Note: No locking is provided.  Under normal circumstances, like the other task is not running (e.g. this is running
    from the same event loop as the task) or task is the current task, this is fine.
    """
    return {
        'coro': task.get_coro(),
        'stack': task.get_stack(),
        'exception': task.get_exception(),
        'name': task.get_name()
    }
