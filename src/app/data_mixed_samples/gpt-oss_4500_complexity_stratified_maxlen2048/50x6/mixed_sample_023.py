# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3047_human, name=strtime) ===
def strtime (t, func=time.localtime):
    """Return ISO 8601 formatted time."""
    return time.strftime("%Y-%m-%d %H:%M:%S", func(t)) + strtimezone()

# === BLOCK 2 (label=lm, source_idx=line1887_lm, name=status) ===
async def status(cls):
        """
        Returns the current status of the configured API server.
        """
        import aiohttp

        base_url = getattr(cls, "base_url", None)
        if not base_url:
            raise ValueError("Class missing required 'base_url' attribute")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"{base_url.rstrip('/')}/status") as response:
                response.raise_for_status()
                return await response.json()

# === BLOCK 3 (label=human, source_idx=line4970_human, name=make2d) ===
def make2d(array, cols=None, dtype=None):
    """
    Make a 2D array from an array of arrays.  The `cols' and `dtype'
    arguments can be omitted if the array is not empty.

    """
    if not len(array):
        if cols is None or dtype is None:
            raise RuntimeError(
                "cols and dtype must be specified for empty array"
            )
        return _np.empty((0, cols), dtype=dtype)
    return _np.vstack(array)

# === BLOCK 4 (label=human, source_idx=line4520_human, name=set_simulation_duration) ===
def set_simulation_duration(self, simulation_duration):
        """
        set the simulation_duration
        see: http://www.gsshawiki.com/Project_File:Required_Inputs
        """
        self.project_manager.setCard('TOT_TIME', str(simulation_duration.total_seconds()/60.0))
        super(EventMode, self).set_simulation_duration(simulation_duration)
        self.simulation_duration = simulation_duration

# === BLOCK 5 (label=lm, source_idx=line2710_lm, name=copy) ===
def copy(self):
        """
        Make a copy of the SegmentList.

        :return: A copy of the SegmentList instance.
        :rtype: angr.analyses.cfg_fast.SegmentList
        """
        import copy as _copy
        return _copy.deepcopy(self)

# === BLOCK 6 (label=lm, source_idx=line1889_lm, name=get_sampleCross) ===
def get_sampleCross(self, res, DS=None, resMode='abs', ind=None):
        """ Sample, with resolution res, the 2D cross-section

        The sampling domain can be limited by DS or ind
        """
