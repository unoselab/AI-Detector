# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line7641_lm, name=add_function) ===
def add_function(self, func):
        """ Record line profiling information for the given Python function.
        """
        if not callable(func):
            raise TypeError("func must be callable")
        self._add_function(func)

# === BLOCK 2 (label=lm, source_idx=line1818_lm, name=release) ===
async def release(self) -> None:
        """Like read(), but reads all the data to the void."""
        self.read()

# === BLOCK 3 (label=human, source_idx=line1126_human, name=wxRect_to_Rect) ===
def wxRect_to_Rect(self, wr):
        """ Return a shrunk fitz.Rect for given wx.Rect."""
        r = fitz.Rect(wr.x, wr.y, wr.x + wr.width, wr.y + wr.height)
        return r * self.shrink

# === BLOCK 4 (label=human, source_idx=line8192_human, name=assign_variable_names) ===
def assign_variable_names(self):
        """
        Assign default names to all variables.

        :return: None
        """

        for var in self._variables:
            if isinstance(var, SimStackVariable):
                if var.name is not None:
                    continue
                if var.ident.startswith('iarg'):
                    var.name = 'arg_%x' % var.offset
                else:
                    var.name = 's_%x' % (-var.offset)
                    # var.name = var.ident
            elif isinstance(var, SimRegisterVariable):
                if var.name is not None:
                    continue
                var.name = var.ident

# === BLOCK 5 (label=human, source_idx=line6338_human, name=changeTarget) ===
def changeTarget(self, vehID, edgeID):
        """changeTarget(string, string) -> None

        The vehicle's destination edge is set to the given edge id. The route is rebuilt.
        """
        self._connection._sendStringCmd(
            tc.CMD_SET_VEHICLE_VARIABLE, tc.CMD_CHANGETARGET, vehID, edgeID)

# === BLOCK 6 (label=lm, source_idx=line2223_lm, name=imagetransformer_base_10l_16h_big_dr01_moe_imgnet) ===
def imagetransformer_base_10l_16h_big_dr01_moe_imgnet():
  """big 1d model for conditional image generation."""
