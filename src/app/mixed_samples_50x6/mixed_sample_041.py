# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line123_human, name=get_glacier_poly) ===
def get_glacier_poly():
    """Calls external shell script `get_rgi.sh` to fetch:

    Randolph Glacier Inventory (RGI) glacier outline shapefiles 

    Full RGI database: rgi50.zip is 410 MB

    The shell script will unzip and merge regional shp into single global shp

    http://www.glims.org/RGI/
    """
    #rgi_fn = os.path.join(datadir, 'rgi50/regions/rgi50_merge.shp')
    #Update to rgi60, should have this returned from get_rgi.sh
    rgi_fn = os.path.join(datadir, 'rgi60/regions/rgi60_merge.shp')
    if not os.path.exists(rgi_fn):
        cmd = ['get_rgi.sh',]
        sys.exit("Missing rgi glacier data source. If already downloaded, specify correct datadir. If not, run `%s` to download" % cmd[0])
        #subprocess.call(cmd)
    return rgi_fn

# === BLOCK 2 (label=human, source_idx=line2662_human, name=connection) ===
def connection(self, shareable=True):
        """Get a steady, cached DB-API 2 connection from the pool.

        If shareable is set and the underlying DB-API 2 allows it,
        then the connection may be shared with other threads.

        """
        if shareable and self._maxshared:
            self._lock.acquire()
            try:
                while (not self._shared_cache and self._maxconnections
                        and self._connections >= self._maxconnections):
                    self._wait_lock()
                if len(self._shared_cache) < self._maxshared:
                    # shared cache is not full, get a dedicated connection
                    try:  # first try to get it from the idle cache
                        con = self._idle_cache.pop(0)
                    except IndexError:  # else get a fresh connection
                        con = self.steady_connection()
                    else:
                        con._ping_check()  # check this connection
                    con = SharedDBConnection(con)
                    self._connections += 1
                else:  # shared cache full or no more connections allowed
                    self._shared_cache.sort()  # least shared connection first
                    con = self._shared_cache.pop(0)  # get it
                    while con.con._transaction:
                        # do not share connections which are in a transaction
                        self._shared_cache.insert(0, con)
                        self._wait_lock()
                        self._shared_cache.sort()
                        con = self._shared_cache.pop(0)
                    con.con._ping_check()  # check the underlying connection
                    con.share()  # increase share of this connection
                # put the connection (back) into the shared cache
                self._shared_cache.append(con)
                self._lock.notify()
            finally:
                self._lock.release()
            con = PooledSharedDBConnection(self, con)
        else:  # try to get a dedicated connection
            self._lock.acquire()
            try:
                while (self._maxconnections
                        and self._connections >= self._maxconnections):
                    self._wait_lock()
                # connection limit not reached, get a dedicated connection
                try:  # first try to get it from the idle cache
                    con = self._idle_cache.pop(0)
                except IndexError:  # else get a fresh connection
                    con = self.steady_connection()
                else:
                    con._ping_check()  # check connection
                con = PooledDedicatedDBConnection(self, con)
                self._connections += 1
            finally:
                self._lock.release()
        return con

# === BLOCK 3 (label=lm, source_idx=line1909_lm, name=get) ===
def get(key, default=-1):
        """Backport support for original codes."""
        return default

# === BLOCK 4 (label=lm, source_idx=line1625_lm, name=load_sample) ===
def load_sample(sample):
    """ Load meter data, temperature data, and metadata for associated with a
    particular sample identifier. Note: samples are simulated, not real, data.

    Parameters
    ----------
    sample : :any:`str`
        Identifier of sample. Complete list can be obtained with
        :any:`eemeter.samples`.

    Returns
    -------
    meter_data, temperature_data, metadata : :any:`tuple` of :any:`pandas.DataFrame`, :any:`pandas.Series`, and :any:`dict`
        Meter data, temperature data, and metadata for this sample identifier.
    """
    meter_data = pd.DataFrame({
        'date': ['2017-01-01', '2017-01-02', '2017-01-03', '2017-01-04', '2017-01-05'],
        'value': [100, 105, 95, 100, 105]
    })
    meter_data['date'] = pd.to_datetime(meter_data['date'])
    meter_data.set_index('date', inplace=True)
    temperature_data = pd.Series([70, 72, 75, 73, 71], index=meter_data.index)
    metadata = {
       'sample': sample,
       'site_id': '12345',
        'building_id': '67890',
       'model': 'test_model',
       'model_version': '1.0.0',
       'model_parameters': {'a': 1, 'b': 2},
       'model_fit_parameters': {'c': 3, 'd': 4},
       'model_predict_parameters': {'e': 5, 'f': 6},
       'model_evaluation': {'rmse': 7,'mae': 8},
       'model_evaluation_fit_parameters': {'g': 9, 'h': 10},
       'model_evaluation_predict_parameters': {'i': 11, 'j': 12},
    }
    return meter_data,

# === BLOCK 5 (label=lm, source_idx=line1860_lm, name=install_locale) ===
def install_locale(cls, locale_code, locale_type):
        """Install the locale specified by `language_code`, for localizations of type `locale_type`.

        If we can't perform localized formatting for the specified locale,
        then the default localization format will be used.

        If the locale specified is already installed for the selected type, then this is a no-op.
        """
        if locale_code not in cls.installed_locales[locale_type]:
            cls.installed_locales[locale_type].append(locale_code)

# === BLOCK 6 (label=human, source_idx=line1165_human, name=cartpole) ===
def cartpole():
  """Configuration for the cart pole classic control task."""
  locals().update(default())
  # Environment
  env = 'CartPole-v1'
  max_length = 500
  steps = 2e5  # 200k
  normalize_ranges = False  # The env reports wrong ranges.
  # Network
  network = networks.feed_forward_categorical
  return locals()
