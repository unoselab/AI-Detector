# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line592_human, name=destroy_domain_record) ===
def destroy_domain_record(self, domain_id, record_id):
        """
        This method deletes the specified domain record.

        Required parameters

            domain_id:
                Integer or Domain Name (e.g. domain.com), specifies the domain
                for which to destroy a record.

            record_id:
                Integer, specifies the record_id to destroy.
        """
        json = self.request('/domains/%s/records/%s/destroy' % (domain_id, record_id),
                            method='GET')
        status = json.get('status')
        return status

# === BLOCK 2 (label=lm, source_idx=line2006_lm, name=add_argument) ===
def add_argument(parser, dest, info):
    """ Add an argument to an `argparse.ArgumentParser` object

    Parameters
    ----------
    parser : `argparse.ArgumentParser`
        The parser in question

    dest : str
        The destination for the argument

    info : `tuple`
        The information associated with the argument in question.

    """
    # Determine the command‑line flag name (e.g. "--output-file")
    flag = f'--{dest.replace("_", "-")}'

    # Prepare keyword arguments for add_argument based on

# === BLOCK 3 (label=human, source_idx=line6393_human, name=_disconnect) ===
def _disconnect(self, mqttc, userdata, rc):
        """
        The callback for when a DISCONNECT occurs.

        :param mqttc: The client instance for this callback
        :param userdata: The private userdata for the mqtt client. Not used in Polyglot
        :param rc: Result code of connection, 0 = Graceful, anything else is unclean
        """
        self.connected = False
        if rc != 0:
            LOGGER.info("MQTT Unexpected disconnection. Trying reconnect.")
            try:
                self._mqttc.reconnect()
            except Exception as ex:
                template = "An exception of type {0} occured. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                LOGGER.error("MQTT Connection error: " + message)
        else:
            LOGGER.info("MQTT Graceful disconnection.")

# === BLOCK 4 (label=human, source_idx=line2692_human, name=geometry) ===
def geometry(self, value):
        """gets/sets a feature's geometry"""
        if isinstance(value, (Polygon, Point, Polyline, MultiPoint)):
            if value.type == self.geometryType:
                self._geom = value
        elif arcpyFound:
            if isinstance(value, arcpy.Geometry):
                if value.type == self.geometryType:
                    self._dict['geometry']=json.loads(value.JSON)
                    self._geom = None
                    self._geom = self.geometry

# === BLOCK 5 (label=lm, source_idx=line4353_lm, name=cumsum) ===
def cumsum(self, axis=0, *args, **kwargs):
        """
        Cumulative sum of non-NA/null values.

        When performing the cumulative summation, any non-NA/null values will
        be skipped. The resulting SparseSeries will preserve the locations of
        NaN values, but the fill value will be `np.nan` regardless.

        Parameters
        ----------
        axis : {0}

        Returns
        -------
        cumsum : SparseSeries
        """

# === BLOCK 6 (label=lm, source_idx=line650_lm, name=retry) ===
def retry(*dargs, **dkw):
    """
    Decorator function that instantiates the Retrying object
    @param *dargs: positional arguments passed to Retrying object
    @param **dkw: keyword arguments passed to the Retrying object
    """
    import functools
    from tenacity import Retrying

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return Retrying(*dargs, **dkw).call(func, *args, **kwargs)
        return wrapper
    return decorator
