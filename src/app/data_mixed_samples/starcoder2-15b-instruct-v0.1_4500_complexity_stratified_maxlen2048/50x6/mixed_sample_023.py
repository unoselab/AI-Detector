# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2428_human, name=on_new_line) ===
def on_new_line(self):
        """On new input line"""
        self.set_cursor_position('eof')
        self.current_prompt_pos = self.get_position('cursor')
        self.new_input_line = False

# === BLOCK 2 (label=lm, source_idx=line1678_lm, name=rasterize) ===
def rasterize(self,
                  pitch,
                  origin,
                  resolution=None,
                  fill=True,
                  width=None,
                  **kwargs):
        """
        Rasterize a Path2D object into a boolean image ("mode 1").

        Parameters
        ------------
        pitch:      float, length in model space of a pixel edge
        origin:     (2,) float, origin position in model space
        resolution: (2,) int, resolution in pixel space
        fill:       bool, if True will return closed regions as filled
        width:      int, if not None will draw outline this wide (pixels)

        Returns
        ------------
        raster: PIL.Image object, mode 1
        """
        if resolution is None:
            resolution = self.resolution
        raster = Image.new('1', resolution)
        rasterize_path(self.path, raster, pitch, origin, fill=fill, width=width)

        return raster

# === BLOCK 3 (label=human, source_idx=line3871_human, name=execute_code) ===
def execute_code(self, code, filename=None, isolate=False):
        """Execute code within the execution context.

        Args:
            code (str or SourceCode): Rex code to execute.
            filename (str): Filename to report if there are syntax errors.
            isolate (bool): If True, do not affect `self.globals` by executing
                this code.
        """
        def _apply():
            self.compile_code(code=code,
                              filename=filename,
                              exec_namespace=self.globals)

        # we want to execute the code using self.globals - if for no other
        # reason that self.formatter is pointing at self.globals, so if we
        # passed in a copy, we would also need to make self.formatter "look" at
        # the same copy - but we don't want to "pollute" our namespace, because
        # the same executor may be used to run multiple packages. Therefore,
        # we save a copy of self.globals before execution, and restore it after
        #
        if isolate:
            saved_globals = dict(self.globals)

            try:
                _apply()
            finally:
                self.globals.clear()
                self.globals.update(saved_globals)
        else:
            _apply()

# === BLOCK 4 (label=human, source_idx=line3459_human, name=_surface) ===
def _surface(self, T):
        """Generic equation for the surface tension

        Parameters
        ----------
        T : float
            Temperature, [K]

        Returns
        -------
        σ : float
            Surface tension, [N/m]

        Notes
        -----
        Need a _surf dict in the derived class with the parameters keys:
            sigma: coefficient
            exp: exponent
        """
        tau = 1-T/self.Tc
        sigma = 0
        for n, t in zip(self._surf["sigma"], self._surf["exp"]):
            sigma += n*tau**t
        return sigma

# === BLOCK 5 (label=lm, source_idx=line2194_lm, name=make_cos_vects) ===
def make_cos_vects(lon_vect, lat_vect):
    """ Convert from longitude (RA or GLON) and latitude (DEC or GLAT) values to directional cosines

    Parameters
    ----------
    lon_vect,lat_vect : np.ndarray(nsrc)  
       Input values

    returns (np.ndarray(3,nsrc)) with the directional cosine (i.e., x,y,z component) values
    """
    cos_lon = np.cos(np.radians(lon_vect))
    cos_lat = np.cos(np.radians(lat_vect))
    sin_lat = np.sin(np.radians(lat_vect))
    x = cos_lon * cos_lat
    y = sin_lat
    z = np.sin(np.radians(lon_vect))
    return np.array([x, y, z]).T

# === BLOCK 6 (label=lm, source_idx=line168_lm, name=plugin_get_rfu) ===
def plugin_get_rfu(plugin):
    """
    Returns "regular file urls" for a particular plugin.
    @param plugin: plugin class.
    """
    return plugin.regular_file_urls
