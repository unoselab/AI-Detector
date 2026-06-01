# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8789_lm, name=arcball_map_to_sphere) ===
def arcball_map_to_sphere(point, center, radius):
    """Return unit sphere coordinates from window coordinates."""
    x = (point[0] - center[0]) / radius
    y = (point[1] - center[1]) / radius
    z = 0.0

    norm_sq = x*x + y*y
    if norm_sq <= 1.0:
        z = (1.0 - norm_sq)**0.5
    else:
        scale = 1.0 / (norm_sq**0.5)
        x *= scale
        y *= scale
        z = 0.0

    mag = (x*x + y*y + z*z)**0.5
    if mag == 0:
        return (0.0, 0.0, 0.0)
    return (x/mag, y/mag, z/mag)

# === BLOCK 2 (label=human, source_idx=line1882_human, name=upper_band) ===
def upper_band(close_data, high_data, low_data, period):
    """
    Upper Band.

    Formula:
    UB = CB + BW
    """
    cb = center_band(close_data, high_data, low_data, period)
    bw = band_width(high_data, low_data, period)
    ub = cb + bw
    return ub

# === BLOCK 3 (label=human, source_idx=line5913_human, name=closeEvent) ===
def closeEvent(self, event):
        """
        things to be done when gui closes, like save the settings
        """

        self.save_config(self.gui_settings['gui_settings'])
        self.script_thread.quit()
        self.read_probes.quit()
        event.accept()

        print('\n\n======================================================')
        print('================= Closing B26 Python LAB =============')
        print('======================================================\n\n')

# === BLOCK 4 (label=lm, source_idx=line1795_lm, name=idctii) ===
def idctii(x, axes=None):
    """
    Compute a multi-dimensional inverse DCT-II over specified array axes.
    This function is implemented by calling the one-dimensional inverse
    DCT-II :func:`scipy.fftpack.idct` with normalization mode 'ortho'
    for each of the specified axes.

    Parameters
    ----------
    a : array_like
      Input array
    axes : sequence of ints, optional (default None)
      Axes over which to compute the inverse DCT-II.

    Returns
    -------
    y : ndarray
      Inverse DCT-II of input array
    """
    from scipy.fftpack import idct
    x = np.asarray(x)
    if axes is None:
        axes = tuple(range(x.ndim))
    elif isinstance(axes, int):
        axes = (axes,)

    y = x
    for axis in axes:
        y = idct(y, axis=axis, norm='ortho')
    return y

# === BLOCK 5 (label=lm, source_idx=line6501_lm, name=update) ===
def update(self, id=None, new_data={}, **kwargs):
        """Update an object on the server.

        Args:
            id: ID of the object to update (can be None if not required)
            new_data: the update data for the object
            **kwargs: Extra options to send to the server (e.g. sudo)

        Returns:
            dict: The new object data (*not* a RESTObject)

        Raises:
            GitlabAuthenticationError: If authentication is not correct
            GitlabUpdateError: If the server cannot perform the request
        """
        url = self.get_url(id)
        payload = {**new_data, **kwargs}
        try:
            response = self.session.put(url, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                raise GitlabAuthenticationError(e)
            raise GitlabUpdateError(e)

# === BLOCK 6 (label=human, source_idx=line8539_human, name=set_select) ===
def set_select(cls, authors):
        """
        Put data into ``<select>`` element.

        Args:
            authors (dict): Dictionary with author informations returned from
                aleph REST API. Format:
                ``{"name": .., "code": .., "linked_forms": ["..",]}``.
        """
        cls.select_el.html = ""

        if not authors:
            cls.select_el.disabled = True
            cls.select_el <= html.OPTION("Nic nenalezeno!")
            return

        cls.select_el.disabled = False
        for author_dict in authors:
            name = author_dict.get("name")
            code = author_dict.get("code")
            alt_name = author_dict.get("alt_name", name)

            if not (name and code):
                continue

            cls.code_to_data[code] = author_dict
            cls.select_el <= html.OPTION(alt_name, value=code)
