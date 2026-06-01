# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line8737_human, name=get_sidecar_nodes) ===
def get_sidecar_nodes(self) -> Iterator[PostSidecarNode]:
        """Sidecar nodes of a Post with typename==GraphSidecar."""
        if self.typename == 'GraphSidecar':
            for edge in self._field('edge_sidecar_to_children', 'edges'):
                node = edge['node']
                is_video = node['is_video']
                yield PostSidecarNode(is_video=is_video, display_url=node['display_url'],
                                      video_url=node['video_url'] if is_video else None)

# === BLOCK 2 (label=human, source_idx=line2726_human, name=missing_optional_tagfiles) ===
def missing_optional_tagfiles(self):
        """
        From v0.97 we need to validate any tagfiles listed
        in the optional tagmanifest(s). As there is no mandatory
        directory structure for additional tagfiles we can
        only check for entries with missing files (not missing
        entries for existing files).
        """
        for tagfilepath in list(self.tagfile_entries().keys()):
            if not os.path.isfile(os.path.join(self.path, tagfilepath)):
                yield tagfilepath

# === BLOCK 3 (label=lm, source_idx=line4329_lm, name=peek) ===
def peek(self, n=1):
        """Returns buffered bytes without advancing the position."""
        if n <= 0:
            return b""
        return self.buffer[self.pos : self.pos + n]

# === BLOCK 4 (label=human, source_idx=line2283_human, name=set_encode_key_value) ===
def set_encode_key_value(self, value, store_type):
        """Save the key value base on it's storage type."""
        self._store_type = store_type
        if store_type == PUBLIC_KEY_STORE_TYPE_HEX:
            self._value = value.hex()
        elif store_type == PUBLIC_KEY_STORE_TYPE_BASE64:
            self._value = b64encode(value).decode()
        elif store_type == PUBLIC_KEY_STORE_TYPE_BASE85:
            self._value = b85encode(value).decode()
        elif store_type == PUBLIC_KEY_STORE_TYPE_JWK:
            # TODO: need to decide on which jwk library to import?
            raise NotImplementedError
        else:
            self._value = value
        return value

# === BLOCK 5 (label=lm, source_idx=line2645_lm, name=get) ===
def get(identifier, namespace='cid', domain='compound', operation=None, output='JSON', searchtype=None, **kwargs):
    """Request wrapper that automatically handles async requests."""
    import requests
    import asyncio

    def sync_request():
        url = f"https://pubchem.ncbi.nlm.nih.gov/rest/{namespace}/{identifier}/{domain}"
        if operation:
            url += f"/{operation}"
        if output:
            url += f"/{output.lower()}"

        params = {}
        if searchtype:
            params['searchtype'] = searchtype
        params.update(kwargs)

        response = requests.get(url, params=params)
        response.raise_for_status()

        if output.upper() == 'JSON':
            return response.json()
        return response.text

    if asyncio.get_event_loop().is_running():
        return asyncio.to_thread(sync_request)
    return sync_request()

# === BLOCK 6 (label=lm, source_idx=line2426_lm, name=_process_get_cal_resp) ===
def _process_get_cal_resp(url, post_response, campus):
    """
    :return: a dictionary of {calenderid, TrumbaCalendar}
             None if error, {} if not exists
    If the request is successful, process the response data
    and load the json data into the return object.
    """
    import json
    try:
        if post_response.status_code != 200:
            return None

        data = post_response.json()
        if not data or 'calendars' not in data:
            return {}

        from trumba_client import TrumbaCalendar
        calendars = {}
        for cal_data in data['calendars']:
            cal_id = cal_data.get('calendarId')
            if cal_id:
                calendars[cal_id] = TrumbaCalendar(cal_id, cal_data)
        return calendars
    except (ValueError, KeyError, AttributeError):
        return None
