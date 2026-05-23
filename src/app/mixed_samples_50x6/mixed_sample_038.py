# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line315_human, name=rate) ===
def rate(self):
        """Returns the rate of the progress as a float. Selects the unstable rate if eta_every > 1 for performance."""
        return float(self._eta.rate_unstable if self.eta_every > 1 else self._eta.rate)

# === BLOCK 2 (label=human, source_idx=line1574_human, name=tlog) ===
def tlog(x, th=1, r=_display_max, d=_l_mmax):
    """
    Truncated log10 transform.

    Parameters
    ----------
    x : num | num iterable
        values to be transformed.
    th : num
        values below th are transormed to 0.
        Must be positive.
    r : num (default = 10**4)
        maximal transformed value.
    d : num (default = log10(2**18))
        log10 of maximal possible measured value.
        tlog(10**d) = r

    Returns
    -------
    Array of transformed values.
    """
    if th <= 0:
        raise ValueError('Threshold value must be positive. %s given.' % th)
    return where(x <= th, log10(th) * 1. * r / d, log10(x) * 1. * r / d)

# === BLOCK 3 (label=lm, source_idx=line2324_lm, name=get_default_sticker_id) ===
def get_default_sticker_id(self):
        """
        Gets the default sticker for that content type depending on the
        requested size.

        :return: An sticker ID as string
        """
        if self.content_type == 'image':
            return '12345'
        elif self.content_type == 'video':
            return '67890'
        else:
            raise ValueError('Unsupported content type')

# === BLOCK 4 (label=human, source_idx=line1044_human, name=msg) ===
def msg(self, message, title=None, title_color=None, color='BLUE', ident=0):
        """
        Hint message.

        :param message:
        :param title:
        :param title_color:
        :param color:
        :param ident:
        :return:
        """
        if title and not title_color:
            title_color = color
        if title_color and not title:
            title_color = None

        self.__colored_output(title, message, title_color, color, ident=ident)

# === BLOCK 5 (label=lm, source_idx=line2510_lm, name=add_area) ===
def add_area(self, uri):
        """
        Record information about a new Upload Area

        :param UploadAreaURI uri: An Upload Area URI.
        """
        self.areas[uri] = {
            "uri": uri,
            "files": [],
            "size": 0,
            "last_updated": datetime.utcnow(),
        }

# === BLOCK 6 (label=lm, source_idx=line924_lm, name=push_broks) ===
def push_broks(self, broks):
        """Send a HTTP request to the satellite (POST /push_broks)
        Send broks to the satellite

        :param broks: Brok list to send
        :type broks: list
        :return: True on success, False on failure
        :rtype: bool
        """
        data = json.dumps(broks)
        headers = {'Content-Type': 'application/json'}
        response = requests.post(self.url + '/push_broks', data=data, headers=headers)
        if response.status_code == 200:
            return True
        else:
            return False
