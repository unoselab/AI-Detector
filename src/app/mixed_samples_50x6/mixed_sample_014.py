# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1843_human, name=get_cassandra_connections) ===
def get_cassandra_connections():
    """
    :return: List of tuples (db_alias, connection) for all cassandra
    connections in DATABASES dict.
    """

    from django.db import connections
    for alias in connections:
        engine = connections[alias].settings_dict.get('ENGINE', '')
        if engine == 'django_cassandra_engine':
            yield alias, connections[alias]

# === BLOCK 2 (label=human, source_idx=line959_human, name=in_region) ===
def in_region(rname, rstart, target_chr, target_start, target_end):
    """
    Quick check if a point is within the target region.
    """
    return (rname == target_chr) and \
           (target_start <= rstart <= target_end)

# === BLOCK 3 (label=lm, source_idx=line947_lm, name=get_details_from_inst_literal) ===
def get_details_from_inst_literal(self, institute_literal, institution_id, institution_instance_id, paper_key):
        """
        This method parses the institute literal to get the following
        1. Department naame
        2. Country
        3. University name
        4. ZIP, STATE AND CITY (Only if the country is USA. For other countries the standard may vary. So parsing these
        values becomes very difficult. However, the complete address can be found in the column "AddressLine1"

        Parameters
        ----------
        institute_literal -> The literal value of the institute
        institution_id  -> the Primary key value which is to be added in the fixture
        institution_instance_id -> Primary key value which is to be added in the fixture
        paper_key -> The Paper key which is used for the Institution Instance

        Returns
        -------

        """
        department_name = None
        country = None
        university_name = None
        zip_state_city = None

        if institute_literal:
            parts = institute_literal.split(',')
            if len(parts) > 0:
                university_name = parts[0]
            if len(parts) > 1:
                country = parts[1]
            if len(parts) > 2:
                department_name = parts[2]
            if len(parts) > 3:
                zip_state_city = parts[3]

        return {
            'department_name': department_name,
            'country': country,
            'university_name': university_name,
            'zip_state_city': zip_state_city,
            'institution_id': institution_id,
            'institution_instance_id': institution_instance_id,
            'paper_key': paper_key
        }

# === BLOCK 4 (label=human, source_idx=line460_human, name=is_applicable) ===
def is_applicable(cls, conf):
        """Return whether this promoter is applicable for given conf"""
        return all((
            URLPromoter.is_applicable(conf),
            not cls.needs_firefox(conf),
        ))

# === BLOCK 5 (label=lm, source_idx=line2332_lm, name=libvlc_media_parse_with_options) ===
def libvlc_media_parse_with_options(p_md, parse_flag):
    """Parse the media asynchronously with options.
    This fetches (local or network) art, meta data and/or tracks information.
    This method is the extended version of L{libvlc_media_parse_async}().
    To track when this is over you can listen to libvlc_MediaParsedChanged
    event. However if this functions returns an error, you will not receive this
    event.
    It uses a flag to specify parse options (see libvlc_media_parse_flag_t). All
    these flags can be combined. By default, media is parsed if it's a local
    file.
    See libvlc_MediaParsedChanged
    See L{libvlc_media_get_meta}
    See L{libvlc_media_tracks_get}
    See libvlc_media_parse_flag_t.
    @param p_md: media descriptor object.
    @param parse_flag: parse options:
    @return: -1 in case of error, 0 otherwise.
    @version: LibVLC 3.0.0 or later.
    """
    if parse_flag & 1:
        return 0
    else:
        return -1

# === BLOCK 6 (label=lm, source_idx=line833_lm, name=_op) ===
def _op(self, method, path='', data=None, headers=None):
        """Overrides the base method to support retrying the operation.

        :param method: The HTTP method to be used, e.g: GET, POST,
            PUT, PATCH, etc...
        :param path: The sub-URI path to the resource.
        :param data: Optional JSON data.
        :param headers: Optional dictionary of headers.
        :returns: The response from the connector.Connector's _op method.
        """
        for _ in range(self.MAX_RETRIES):
            try:
                return super()._op(method, path, data, headers)
            except Exception as e:
                if isinstance(e, connector.ConnectorError):
                    raise
                logger.warning('Failed to execute operation, retrying. Error: %s', e)
        raise connector.ConnectorError('Failed to execute operation after %s retries' % self.MAX_RETRIES)
