# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3601_human, name=getDataset) ===
def getDataset(self, itemId):
        """gets a dataset class"""
        if self._url.lower().find('datasets') > -1:
            url = self._url
        else:
            url = self._url + "/datasets"
        return OpenDataItem(url=url,
                            itemId=itemId,
                            securityHandler=self._securityHandler,
                            proxy_url=self._proxy_url,
                            proxy_port=self._proxy_port)

# === BLOCK 2 (label=lm, source_idx=line3139_lm, name=get_stats_code_frequency) ===
def get_stats_code_frequency(self):
        """
        :calls: `GET /repos/:owner/:repo/stats/code_frequency <http://developer.github.com/v3/repos/statistics/#get-the-number-of-additions-and-deletions-per-week>`_
        :rtype: None or list of :class:`github.StatsCodeFrequency.StatsCodeFrequency`
        """
        return self._get("/repos/%s/%s/stats/code_frequency" % (self._get_owner(), self._get_repo()))

# === BLOCK 3 (label=human, source_idx=line906_human, name=_build_discrete_cmap) ===
def _build_discrete_cmap(cmap, levels, extend, filled):
    """
    Build a discrete colormap and normalization of the data.
    """
    import matplotlib as mpl

    if not filled:
        # non-filled contour plots
        extend = 'max'

    if extend == 'both':
        ext_n = 2
    elif extend in ['min', 'max']:
        ext_n = 1
    else:
        ext_n = 0

    n_colors = len(levels) + ext_n - 1
    pal = _color_palette(cmap, n_colors)

    new_cmap, cnorm = mpl.colors.from_levels_and_colors(
        levels, pal, extend=extend)
    # copy the old cmap name, for easier testing
    new_cmap.name = getattr(cmap, 'name', cmap)

    return new_cmap, cnorm

# === BLOCK 4 (label=lm, source_idx=line726_lm, name=disable_host_flap_detection) ===
def disable_host_flap_detection(self, host):
        """Disable flap detection for a host
        Format of the line that triggers function call::

        DISABLE_HOST_FLAP_DETECTION;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        self.disable_flap_detection(host)

# === BLOCK 5 (label=lm, source_idx=line5524_lm, name=delete_many) ===
def delete_many(self, uris):
        """
        Simple implementation,
        could be better implemented by backend not hitting db for every uri.
        """
        for uri in uris:
            self.delete(uri)

# === BLOCK 6 (label=human, source_idx=line37_human, name=generate_config_parser) ===
def generate_config_parser(config, include_all=False):
    """
    Generates a config parser from a configuration dictionary.

    The dictionary contains the merged informations of the schema and,
    optionally, of a source configuration file. Values of the source
    configuration file will be stored in the *value* field of an option.
    """

    # The allow_no_value allows us to output commented lines.
    config_parser = SafeConfigParser(allow_no_value=True)
    for section_name, option_name in _get_included_schema_sections_options(config, include_all):

        if not config_parser.has_section(section_name):
            config_parser.add_section(section_name)

        option = config[section_name][option_name]

        if option.get('required'):
            config_parser.set(section_name, '# REQUIRED')

        config_parser.set(section_name, '# ' + option.get('description', 'No description provided.'))

        if option.get('deprecated'):
            config_parser.set(section_name, '# DEPRECATED')

        option_value = _get_value(option)
        config_parser.set(section_name, option_name, option_value)

        config_parser.set(section_name, '')

    return config_parser
