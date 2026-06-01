# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1057_human, name=get_tim) ===
def get_tim(_, data):
    """http://git.kernel.org/cgit/linux/kernel/git/jberg/iw.git/tree/scan.c?id=v3.17#n874.

    Positional arguments:
    data -- bytearray data to read.

    Returns:
    Dict.
    """
    answers = {
        'DTIM Count': data[0],
        'DTIM Period': data[1],
        'Bitmap Control': data[2],
        'Bitmap[0]': data[3],
    }
    if len(data) - 4:
        answers['+ octets'] = len(data) - 4
    return answers

# === BLOCK 2 (label=lm, source_idx=line6917_lm, name=_add_offsets_to_token_nodes) ===
def _add_offsets_to_token_nodes(self):
        """
        Adds primary text string onsets/offsets to all nodes that represent
        tokens. In SaltDocuments, this data was stored in TextualRelation
        edges only.
        """

# === BLOCK 3 (label=lm, source_idx=line1640_lm, name=string_to_response) ===
def string_to_response(content_type):
    """
    Wrap a view-like function that returns a string and marshalls it into an
    HttpResponse with the given Content-Type
    If the view raises an HttpBadRequestException, it will be converted into
    an HttpResponseBadRequest.
    """
    import functools
    from django.http import Http

# === BLOCK 4 (label=lm, source_idx=line6179_lm, name=upload_object) ===
def upload_object(file_path, container_name, object_name, profile, extra=None,
                  verify_hash=True, headers=None, **libcloud_kwargs):
    """
    Upload an object currently located on a disk.

    :param file_path: Path to the object on disk.
    :type file_path: ``str``

    :param container_name: Destination container.
    :type container_name: ``str``

    :param object_name: Object name.
    :type object_name: ``str``

    :param profile: The profile key
    :type  profile: ``str``

    :param verify_hash: Verify hash
    :type verify_hash: ``bool``

    :param extra: Extra attributes (driver specific). (optional)
    :type extra: ``dict``

    :param headers: (optional) Additional request headers,
        such as CORS headers. For example:
        headers = {'Access-Control-Allow-Origin': 'http://mozilla.com'}
    :type headers: ``dict``

    :param libcloud_kwargs: Extra arguments for the driver's upload_object method
    :type  libcloud_kwargs: ``dict``

    :return: The object name in the cloud
    :rtype: ``str``

    CLI Example:

    .. code-block:: bash

        salt myminion libcloud_storage.upload_object /file/to/me.jpg MyFolder me.jpg profile1

    """
    from libcloud.storage.types import Provider
    from libcloud.storage.providers import get_driver

    # Resolve provider enum from profile string
    try:
        provider_enum = getattr(Provider, profile.upper())
    except AttributeError as exc:
        raise ValueError(f"Unsupported libcloud storage profile: {profile}") from exc

    # Instantiate

# === BLOCK 5 (label=human, source_idx=line2805_human, name=_output) ===
def _output(self, message, verbosity, exact, stream):
        """ Output a message if the config's verbosity is >= to the given verbosity. If exact == True, the message
        will only be outputted if the given verbosity exactly matches the config's verbosity. """
        if exact:
            if self.config.verbosity == verbosity:
                stream.write(message + "\n")
        else:
            if self.config.verbosity >= verbosity:
                stream.write(message + "\n")

# === BLOCK 6 (label=human, source_idx=line5697_human, name=night_utc) ===
def night_utc(self, date, latitude, longitude, observer_elevation=0):
        """Calculate night start and end times in the UTC timezone.

        Night is calculated to be between astronomical dusk on the
        date specified and astronomical dawn of the next day.

        :param date:       Date to calculate for.
        :type date:        :class:`datetime.date`
        :param latitude:   Latitude - Northern latitudes should be positive
        :type latitude:    float
        :param longitude:  Longitude - Eastern longitudes should be positive
        :type longitude:   float
        :param observer_elevation:  Elevation in metres to calculate night for
        :type observer_elevation:   int

        :return: A tuple of the UTC date and time at which night starts and ends.
        :rtype: (:class:`~datetime.datetime`, :class:`~datetime.datetime`)
        """

        start = self.dusk_utc(date, latitude, longitude, 18, observer_elevation)
        tomorrow = date + datetime.timedelta(days=1)
        end = self.dawn_utc(tomorrow, latitude, longitude, 18, observer_elevation)

        return start, end
