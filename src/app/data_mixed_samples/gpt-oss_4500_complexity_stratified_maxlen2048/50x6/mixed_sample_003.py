# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5616_human, name=powerupIndirector) ===
def powerupIndirector(interface):
    """
    A decorator for a powerup indirector from a single interface to a single
    in-memory implementation.

    The in-memory implementation that is being indirected to must be created
    in the ``activate`` callback, and then assigned to ``self.indirected``,
    which is an ``inmemory`` attribute.
    """
    def decorator(cls):
        zi.implementer(iaxiom.IPowerupIndirector)(cls)
        cls.powerupInterfaces = [interface]
        cls.indirect = _indirect
        return cls

    return decorator

# === BLOCK 2 (label=lm, source_idx=line2692_lm, name=geometry) ===
def geometry(self, value):
        """gets/sets a feature's geometry"""
        if value is None:
            return getattr(self, "_geometry", None)
        self._geometry = value
        return self

# === BLOCK 3 (label=human, source_idx=line6100_human, name=tasks) ===
def tasks():
    """Display registered tasks with their queue"""
    tasks = get_tasks()
    longest = max(tasks.keys(), key=len)
    size = len(longest)
    for name, queue in sorted(tasks.items()):
        print('* {0}: {1}'.format(name.ljust(size), queue))

# === BLOCK 4 (label=human, source_idx=line6012_human, name=parse_reading) ===
def parse_reading(val: str) -> Optional[float]:
    """ Convert reading value to float (if possible) """
    try:
        return float(val)
    except ValueError:
        logging.warning('Reading of "%s" is not a number', val)
        return None

# === BLOCK 5 (label=lm, source_idx=line422_lm, name=setCurrentDate) ===
def setCurrentDate( self, date ):
        """
        Sets the current date displayed by this calendar widget.

        :return     <QDate>
        """
        if isinstance(date, QDate):
            qdate = date
        else:
            try:
                qdate = QDate(date.year, date.month, date.day)
            except Exception as e:
                raise TypeError("date must be a QDate or a datetime.date-like object") from e
        self.setSelectedDate(qdate)
        return qdate

# === BLOCK 6 (label=lm, source_idx=line5029_lm, name=_post_data) ===
def _post_data(options=None, xml=None):
    """
    Post data to Nagios NRDP
    """
    import requests

    if xml is None:
        raise ValueError("xml payload is required")
    if not isinstance(options, dict):
        raise ValueError("options must be a dict containing 'url' and 'token'")
    url = options.get('url')
    token = options.get('token')
    if not url:
        raise ValueError("options must include 'url'")
    if not token:
        raise ValueError("options must include 'token'")
    timeout = options.get('timeout', 10)
    verify = options.get('verify', True)

    payload = {
        'token': token,
        'XMLDATA': xml
    }

    try:
        resp = requests.post(url, data=payload, timeout=timeout, verify=verify)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as e:
        raise RuntimeError(f"Failed to post data to NRDP: {e}")
