# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2655_lm, name=assignees) ===
def assignees(self):
        """List of assignees to the activity."""

# === BLOCK 2 (label=lm, source_idx=line3155_lm, name=logical_lines) ===
def logical_lines(lines):
    """Merge lines into chunks according to q rules"""

# === BLOCK 3 (label=human, source_idx=line4226_human, name=geodetic2ecef) ===
def geodetic2ecef(lat: float, lon: float, alt: float,
                  ell: Ellipsoid = None, deg: bool = True) -> Tuple[float, float, float]:
    """
    point transformation from Geodetic of specified ellipsoid (default WGS-84) to ECEF

    Parameters
    ----------

    lat : float or numpy.ndarray of float
           target geodetic latitude
    lon : float or numpy.ndarray of float
           target geodetic longitude
    h : float or numpy.ndarray of float
         target altitude above geodetic ellipsoid (meters)
    ell : Ellipsoid, optional
          reference ellipsoid
    deg : bool, optional
          degrees input/output  (False: radians in/out)


    Returns
    -------

    ECEF (Earth centered, Earth fixed)  x,y,z

    x : float or numpy.ndarray of float
        target x ECEF coordinate (meters)
    y : float or numpy.ndarray of float
        target y ECEF coordinate (meters)
    z : float or numpy.ndarray of float
        target z ECEF coordinate (meters)
    """
    if ell is None:
        ell = Ellipsoid()

    if deg:
        lat = radians(lat)
        lon = radians(lon)

    with np.errstate(invalid='ignore'):
        # need np.any() to handle scalar and array cases
        if np.any((lat < -pi / 2) | (lat > pi / 2)):
            raise ValueError('-90 <= lat <= 90')

    # radius of curvature of the prime vertical section
    N = get_radius_normal(lat, ell)
    # Compute cartesian (geocentric) coordinates given  (curvilinear) geodetic
    # coordinates.
    x = (N + alt) * cos(lat) * cos(lon)
    y = (N + alt) * cos(lat) * sin(lon)
    z = (N * (ell.b / ell.a)**2 + alt) * sin(lat)

    return x, y, z

# === BLOCK 4 (label=lm, source_idx=line2256_lm, name=datetime2unix) ===
def datetime2unix(T):
    """
    converts datetime to UT1 unix epoch time
    """
    import datetime, calendar
    if isinstance(T, datetime.datetime):
        if T.tzinfo is None:
            dt_utc = T
        else:
            dt_utc = T.astimezone(datetime.timezone.utc).replace(tzinfo=None)
        return calendar.timegm(dt_utc.timetuple()) + dt_utc.microsecond / 1_000_000
    raise TypeError("Expected datetime.datetime instance")

# === BLOCK 5 (label=human, source_idx=line6004_human, name=unflatten2) ===
def unflatten2(flat_list, cumlen_list):
    """ Rebuilds unflat list from invertible_flatten1

    Args:
        flat_list (list): the flattened list
        cumlen_list (list): the list which undoes flattenting

    Returns:
        unflat_list2: original nested list

    SeeAlso:
        invertible_flatten1
        invertible_flatten2
        unflatten2

    Example:
        >>> # ENABLE_DOCTEST
        >>> from utool.util_list import *  # NOQA
        >>> import utool
        >>> utool.util_list
        >>> flat_list = [5, 2, 3, 12, 3, 3, 9, 13, 3, 5]
        >>> cumlen_list = [ 1,  6,  7,  9, 10]
        >>> unflat_list2 = unflatten2(flat_list, cumlen_list)
        >>> result = (unflat_list2)
        >>> print(result)
        [[5], [2, 3, 12, 3, 3], [9], [13, 3], [5]]
    """
    unflat_list2 = [flat_list[low:high] for low, high in
                    zip(itertools.chain([0], cumlen_list), cumlen_list)]
    return unflat_list2

# === BLOCK 6 (label=human, source_idx=line3585_human, name=EncryptPrivateKey) ===
def EncryptPrivateKey(self, decrypted):
        """
        Encrypt the provided plaintext with the initialized private key.

        Args:
            decrypted (byte string): the plaintext to be encrypted.

        Returns:
            bytes: the ciphertext.
        """
        aes = AES.new(self._master_key, AES.MODE_CBC, self._iv)
        return aes.encrypt(decrypted)
