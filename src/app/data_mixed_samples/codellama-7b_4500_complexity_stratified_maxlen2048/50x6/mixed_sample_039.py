# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line495_lm, name=when_closed) ===
def when_closed(self):
        """
        Returns a Deferred that callback()'s (with this Circuit instance)
        when this circuit hits CLOSED or FAILED.
        """
        d = Deferred()
        self.add_callback(d.callback, self)
        self.add_errback(d.errback, self)
        return d

# === BLOCK 2 (label=human, source_idx=line6296_human, name=_normalize_sort_SQL) ===
def _normalize_sort_SQL(self, field_name, field_vals, sort_dir_str):
        """
        allow sorting by a set of values

        http://stackoverflow.com/questions/3303851/sqlite-and-custom-order-by
        """
        fvi = None
        if sort_dir_str == 'ASC':
            fvi = (t for t in enumerate(field_vals)) 

        else:
            fvi = (t for t in enumerate(reversed(field_vals))) 

        query_sort_str = ['  CASE {}'.format(self._normalize_name(field_name))]
        query_args = []
        for i, v in fvi:
            query_sort_str.append('    WHEN {} THEN {}'.format(self.val_placeholder, i))
            query_args.append(v)

        query_sort_str.append('  END')
        query_sort_str = "\n".join(query_sort_str)
        return query_sort_str, query_args

# === BLOCK 3 (label=lm, source_idx=line1529_lm, name=stash) ===
def stash(self, stash_name: str):
        """
        Stashes the current working tree changes

        :param stash_name: name of the stash
        :type stash_name: str
        """
        self.git.stash(stash_name)

# === BLOCK 4 (label=lm, source_idx=line5721_lm, name=save) ===
def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        """ Set html field with correct iframe. """
        if not self.html:
            self.html = self.get_default_html()
        super(Iframe, self).save(force_insert, force_update, using, update_fields)

# === BLOCK 5 (label=human, source_idx=line2444_human, name=poi_coords) ===
def poi_coords(poi_id, *, raw=False):
    """
    DVB Map Coordinates
    (GET https://www.dvb.de/apps/map/coordinates)

    :param poi_id: Id of poi
    :param raw: Return raw response
    :return: Coordinates of poi
    """
    try:
        r = requests.get(
            url='https://www.dvb.de/apps/map/coordinates',
            params={
                'id': poi_id,
            },
        )
        if r.status_code == 200:
            response = json.loads(r.content.decode('utf-8'))
        else:
            raise requests.HTTPError('HTTP Status: {}'.format(r.status_code))
    except requests.RequestException as e:
        print('Failed to access DVB map coordinates app. Request Exception', e)
        response = None

    if response is None or raw:
        return response

    coords = [int(i) for i in response.split('|')]
    lat, lng = gk4_to_wgs(coords[0], coords[1])
    return {
        'lat': lat,
        'lng': lng
    }

# === BLOCK 6 (label=human, source_idx=line1472_human, name=create_contentkey_authorization_policy) ===
def create_contentkey_authorization_policy(access_token, content):
    """Create Media Service Content Key Authorization Policy.

    Args:
        access_token (str): A valid Azure authentication token.
        content (str): Content Payload.

    Returns:
        HTTP response. JSON body.
    """
    path = '/ContentKeyAuthorizationPolicies'
    endpoint = ''.join([ams_rest_endpoint, path])
    body = content
    return do_ams_post(endpoint, path, body, access_token)
