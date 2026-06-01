# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4077_human, name=from_envvar) ===
def from_envvar(self, variable_name):
        """Load a configuration from an environment variable pointing to
        a configuration file.

        :param variable_name: name of the environment variable
        :return: bool. ``True`` if able to load config, ``False`` otherwise.
        """
        config_file = os.environ.get(variable_name)
        if not config_file:
            raise RuntimeError(
                "The environment variable %r is not set and "
                "thus configuration could not be loaded." % variable_name
            )
        return self.from_pyfile(config_file)

# === BLOCK 2 (label=lm, source_idx=line2428_lm, name=on_new_line) ===
def on_new_line(self):
        """On new input line"""

        self.current_line += 1
        self.current_column = 0

# === BLOCK 3 (label=lm, source_idx=line3648_lm, name=from_localhost) ===
def from_localhost(self) -> bool:
        """True if :attr:`.peername` is a connection from a ``localhost``
        address.

        """
        return self.peername[0] in ('127.0.0.1', '::1')

# === BLOCK 4 (label=lm, source_idx=line4061_lm, name=expand) ===
def expand(self, repex_vars, fields):
        r"""Receive a dict of variables and a dict of fields
        and iterates through them to expand a variable in an field, then
        returns the fields dict with its variables expanded.

        This will fail if not all variables expand (due to not providing
        all necessary ones).

        fields:

        type: VERSION
        path: resources
        excluded:
            - excluded_file.file
        base_directory: '{{ .base_dir }}'
        match: '"version": "\d+\.\d+(\.\d+)?(-\w\d+)?'
        replace: \d+\.\d+(\.\d+)?(-\w\d+)?
        with: "{{ .version }}"
        must_include:
            - {{ .my_var }}/{{ .another_var }}
            - {{ .my_other_var }}
            - version
        validator:
            type: per_file
            path: {{ .my_validator_path }}
            function: validate

        variables:

        {
            'version': 3,
            'base_dir': .
            ...
        }

        :param dict vars: dict of variables
        :param dict fields: dict of fields as shown above.
        """
        for field in fields:
            if field == 'variables':
                continue
            for key, value in fields[field].items():
                if isinstance(value, str):
                    for var_name, var_value in repex_vars.items():
                        value = value.replace(f'{{{var_name}}}', str(var_value))
                    fields[field][key] = value
        return fields

# === BLOCK 5 (label=human, source_idx=line3597_human, name=timeseries) ===
def timeseries(self):
        """
        Feed-in time series of generator

        It returns the actual time series used in power flow analysis. If
        :attr:`_timeseries` is not :obj:`None`, it is returned. Otherwise,
        :meth:`timeseries` looks for generation and curtailment time series
        of the according type of technology (and weather cell) in
        :class:`~.grid.network.TimeSeries`.

        Returns
        -------
        :pandas:`pandas.DataFrame<dataframe>`
            DataFrame containing active power in kW in column 'p' and
            reactive power in kVA in column 'q'.

        """
        if self._timeseries is None:

            # get time series for active power depending on if they are
            # differentiated by weather cell ID or not
            if isinstance(self.grid.network.timeseries.generation_fluctuating.
                                  columns, pd.MultiIndex):
                if self.weather_cell_id:
                    try:
                        timeseries = self.grid.network.timeseries.\
                            generation_fluctuating[
                            self.type, self.weather_cell_id].to_frame('p')
                    except KeyError:
                        logger.exception("No time series for type {} and "
                                         "weather cell ID {} given.".format(
                            self.type, self.weather_cell_id))
                        raise
                else:
                    logger.exception("No weather cell ID provided for "
                                     "fluctuating generator {}.".format(
                        repr(self)))
                    raise KeyError
            else:
                try:
                    timeseries = self.grid.network.timeseries.\
                        generation_fluctuating[self.type].to_frame('p')
                except KeyError:
                    logger.exception("No time series for type {} "
                                     "given.".format(self.type))
                    raise

            timeseries = timeseries * self.nominal_capacity

            # subtract curtailment
            if self.curtailment is not None:
                timeseries = timeseries.join(
                    self.curtailment.to_frame('curtailment'), how='left')
                timeseries.p = timeseries.p - timeseries.curtailment.fillna(0)

            if self.timeseries_reactive is not None:
                timeseries['q'] = self.timeseries_reactive
            else:
                timeseries['q'] = timeseries['p'] * self.q_sign * tan(acos(
                    self.power_factor))

            return timeseries
        else:
            return self._timeseries.loc[
                   self.grid.network.timeseries.timeindex, :]

# === BLOCK 6 (label=human, source_idx=line2009_human, name=read_checksum_digest) ===
def read_checksum_digest(path, checksum_cls=hashlib.sha256):
  """Given a hash constructor, returns checksum digest and size of file."""
  checksum = checksum_cls()
  size = 0
  with tf.io.gfile.GFile(path, "rb") as f:
    while True:
      block = f.read(io.DEFAULT_BUFFER_SIZE)
      size += len(block)
      if not block:
        break
      checksum.update(block)
  return checksum.hexdigest(), size
