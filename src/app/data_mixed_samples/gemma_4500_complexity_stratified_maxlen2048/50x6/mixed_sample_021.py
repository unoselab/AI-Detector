# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1033_human, name=get_aggregations) ===
def get_aggregations(metrics_dict, saved_metrics, adhoc_metrics=[]):
        """
            Returns a dictionary of aggregation metric names to aggregation json objects

            :param metrics_dict: dictionary of all the metrics
            :param saved_metrics: list of saved metric names
            :param adhoc_metrics: list of adhoc metric names
            :raise SupersetException: if one or more metric names are not aggregations
        """
        aggregations = OrderedDict()
        invalid_metric_names = []
        for metric_name in saved_metrics:
            if metric_name in metrics_dict:
                metric = metrics_dict[metric_name]
                if metric.metric_type == POST_AGG_TYPE:
                    invalid_metric_names.append(metric_name)
                else:
                    aggregations[metric_name] = metric.json_obj
            else:
                invalid_metric_names.append(metric_name)
        if len(invalid_metric_names) > 0:
            raise SupersetException(
                _('Metric(s) {} must be aggregations.').format(invalid_metric_names))
        for adhoc_metric in adhoc_metrics:
            aggregations[adhoc_metric['label']] = {
                'fieldName': adhoc_metric['column']['column_name'],
                'fieldNames': [adhoc_metric['column']['column_name']],
                'type': DruidDatasource.druid_type_from_adhoc_metric(adhoc_metric),
                'name': adhoc_metric['label'],
            }
        return aggregations

# === BLOCK 2 (label=lm, source_idx=line8539_lm, name=set_select) ===
def set_select(cls, authors):
        """
        Put data into ``<select>`` element.

        Args:
            authors (dict): Dictionary with author informations returned from
                aleph REST API. Format:
                ``{"name": .., "code": .., "linked_forms": ["..",]}``.
        """
        for author in authors:
            option = cls.create_element("option")
            option.set("value", author["code"])
            option.text = author["name"]
            cls.select_element.append(option)

# === BLOCK 3 (label=lm, source_idx=line1830_lm, name=add_sample) ===
def add_sample(self, name, labels, value, timestamp=None, exemplar=None):
        """Add a sample to the metric.

        Internal-only, do not use."""
        if timestamp is None:
            timestamp = time.time()

        sample = {
            'labels': labels,
            'value': value,
            'timestamp': timestamp,
            'exemplar': exemplar
        }

        if name not in self._samples:
            self._samples[name] = []

        self._samples[name].append(sample)

# === BLOCK 4 (label=lm, source_idx=line7633_lm, name=_add_user_source) ===
def _add_user_source(self):
        """Add the configuration options from the YAML file in the
        user's configuration directory (given by `config_dir`) if it
        exists.
        """
        import os
        import yaml

        config_path = os.path.join(self.config_dir, 'config.yaml')
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    self.config.update(user_config)

# === BLOCK 5 (label=human, source_idx=line3257_human, name=parseMultiAttributes) ===
def parseMultiAttributes(self, line):
        """Try parsing compound attribute string.

        Return a dictionary with single attributes in 'line'.
        """

        attrs = line.split(';')
        attrs = [a.strip() for a in attrs]
        attrs = filter(lambda a:len(a)>0, attrs)

        new_attrs = {}
        for a in attrs:
            k, v = a.split(':')
            k, v = [s.strip() for s in (k, v)]
            new_attrs[k] = v

        return new_attrs

# === BLOCK 6 (label=human, source_idx=line7176_human, name=set_cookie) ===
def set_cookie(response, name, value, expiry_seconds=None, secure=False):
    """
    Set cookie wrapper that allows number of seconds to be given as the
    expiry time, and ensures values are correctly encoded.
    """
    if expiry_seconds is None:
        expiry_seconds = 90 * 24 * 60 * 60  # Default to 90 days.
    expires = datetime.strftime(datetime.utcnow() +
                                timedelta(seconds=expiry_seconds),
                                "%a, %d-%b-%Y %H:%M:%S GMT")
    # Django doesn't seem to support unicode cookie keys correctly on
    # Python 2. Work around by encoding it. See
    # https://code.djangoproject.com/ticket/19802
    try:
        response.set_cookie(name, value, expires=expires, secure=secure)
    except (KeyError, TypeError):
        response.set_cookie(name.encode('utf-8'), value, expires=expires,
                            secure=secure)
