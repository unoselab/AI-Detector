# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6295_human, name=chuid) ===
def chuid(name, uid):
    """
    Change the uid for a named user

    CLI Example:

    .. code-block:: bash

        salt '*' user.chuid foo 4376
    """
    if not isinstance(uid, int):
        raise SaltInvocationError('uid must be an integer')
    pre_info = info(name)
    if not pre_info:
        raise CommandExecutionError('User \'{0}\' does not exist'.format(name))
    if uid == pre_info['uid']:
        return True
    _dscl(
        ['/Users/{0}'.format(name), 'UniqueID', pre_info['uid'], uid],
        ctype='change'
    )
    # dscl buffers changes, sleep 1 second before checking if new value
    # matches desired value
    time.sleep(1)
    return info(name).get('uid') == uid

# === BLOCK 2 (label=lm, source_idx=line3559_lm, name=chord_counts) ===
def chord_counts(im):
    r"""
    Finds the length of each chord in the supplied image and returns a list
    of their individual sizes

    Parameters
    ----------
    im : ND-array
        An image containing chords drawn in the void space.

    Returns
    -------
    result : 1D-array
        A 1D array with one element for each chord, containing its length.

    Notes
    ----
    The returned array can be passed to ``plt.hist`` to plot the histogram,
    or to ``sp.histogram`` to get the histogram data directly. Another useful
    function is ``sp.bincount`` which gives the number of chords of each
    length in a format suitable for ``plt.plot``.
    """
    import numpy as np
    from scipy.ndimage import label

    labeled_array, num_features = label(im)
    counts = np.bincount(labeled_array.ravel())
    return counts[1:]

# === BLOCK 3 (label=lm, source_idx=line5642_lm, name=get_resource) ===
def get_resource(self):
        """Return the associated resource."""
        return self._resource

# === BLOCK 4 (label=lm, source_idx=line6239_lm, name=load_addresses) ===
def load_addresses(self):
        """
        Loads member addresses from Hazelcast.cloud endpoint.

        :return: (Sequence), The possible member addresses to connect to.
        """
        import requests

        endpoint = f"https://{self.cloud_name}.hazelcast.cloud/api/v1/clusters/{self.cluster_id}/members"
        headers = {"Authorization": f"Bearer {self.api_token}"}

        response = requests.get(endpoint, headers=headers)
        response.raise_for_status()

        data = response.json()
        return [member['address'] for member in data.get('members', [])]

# === BLOCK 5 (label=human, source_idx=line5541_human, name=get_work_artifact_link_types) ===
def get_work_artifact_link_types(self):
        """GetWorkArtifactLinkTypes.
        [Preview API] Get the list of work item tracking outbound artifact link types.
        :rtype: [WorkArtifactLink]
        """
        response = self._send(http_method='GET',
                              location_id='1a31de40-e318-41cd-a6c6-881077df52e3',
                              version='5.0-preview.1')
        return self._deserialize('[WorkArtifactLink]', self._unwrap_collection(response))

# === BLOCK 6 (label=human, source_idx=line2913_human, name=fetch) ===
def fetch(self, card_id, data={}, **kwargs):
        """"
        Fetch Card for given Id

        Args:
            card_id : Id for which card object has to be retrieved

        Returns:
            Card dict for given card Id
        """
        return super(Card, self).fetch(card_id, data, **kwargs)
