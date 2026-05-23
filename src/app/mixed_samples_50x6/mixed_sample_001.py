# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line195_human, name=_raise_bad_scheme) ===
def _raise_bad_scheme(cls, scheme, valid, msg):
        """
            Raise :attr:`BadScheme` error for ``scheme``, possible valid scheme are
            in ``valid``, the error message is ``msg``

            :param bytes scheme: A bad scheme
            :param list valid: A list a valid scheme
            :param str msg: The error template message
            :raises LdapHashUserPassword.BadScheme: always
        """
        valid_schemes = [s.decode() for s in valid]
        valid_schemes.sort()
        raise cls.BadScheme(msg % (scheme, u", ".join(valid_schemes)))

# === BLOCK 2 (label=human, source_idx=line924_human, name=push_broks) ===
def push_broks(self, broks):
        """Send a HTTP request to the satellite (POST /push_broks)
        Send broks to the satellite

        :param broks: Brok list to send
        :type broks: list
        :return: True on success, False on failure
        :rtype: bool
        """
        logger.debug("[%s] Pushing %d broks", self.name, len(broks))
        return self.con.post('_push_broks', {'broks': broks}, wait=True)

# === BLOCK 3 (label=human, source_idx=line1355_human, name=eeg_to_all_evokeds) ===
def eeg_to_all_evokeds(all_epochs, conditions=None):
    """
    Convert all_epochs to all_evokeds.

    DOCS INCOMPLETE :(
    """
    if conditions is None:
        # Get event_id
        conditions = {}
        for participant, epochs in all_epochs.items():
            conditions.update(epochs.event_id)

    all_evokeds = {}
    for participant, epochs in all_epochs.items():
        evokeds = {}
        for cond in conditions:
            try:
                evokeds[cond] = epochs[cond].average()
            except KeyError:
                pass
        all_evokeds[participant] = evokeds

    return(all_evokeds)

# === BLOCK 4 (label=human, source_idx=line2583_human, name=copy_data_ext) ===
def copy_data_ext(self, model, field, dest=None, idx=None, astype=None):
        """
        Retrieve the field of another model and store it as a field.

        :param model: name of the source model being a model name or a group name
        :param field: name of the field to retrieve
        :param dest: name of the destination field in ``self``
        :param idx: idx of elements to access
        :param astype: type cast

        :type model: str
        :type field: str
        :type dest: str
        :type idx: list, matrix
        :type astype: None, list, matrix

        :return: None

        """
        # use default destination

        if not dest:
            dest = field
        assert dest not in self._states + self._algebs

        self.__dict__[dest] = self.read_data_ext(
            model, field, idx, astype=astype)

        if idx is not None:
            if len(idx) == self.n:
                self.link_to(model, idx, self.idx)

# === BLOCK 5 (label=human, source_idx=line739_human, name=create_pool) ===
def create_pool(self):
        """
        Return a ConnectionPool instance of given host
        :param socket_timeout:
            socket timeout for each connection in seconds
        """

        service = self.dao.service_name()

        ca_certs = self.dao.get_setting("CA_BUNDLE",
                                        "/etc/ssl/certs/ca-bundle.crt")
        cert_file = self.dao.get_service_setting("CERT_FILE", None)
        host = self.dao.get_service_setting("HOST")
        key_file = self.dao.get_service_setting("KEY_FILE", None)
        max_pool_size = int(self.dao.get_service_setting("POOL_SIZE", 10))
        socket_timeout = int(self.dao.get_service_setting("TIMEOUT", 2))
        verify_https = self.dao.get_service_setting("VERIFY_HTTPS")

        if verify_https is None:
            verify_https = True

        kwargs = {
            "retries": Retry(total=1, connect=0, read=0, redirect=1),
            "timeout": socket_timeout,
            "maxsize": max_pool_size,
            "block": True,
        }

        if key_file is not None and cert_file is not None:
            kwargs["key_file"] = key_file
            kwargs["cert_file"] = cert_file

        if urlparse(host).scheme == "https":
            kwargs["ssl_version"] = self.dao.get_service_setting(
                "SSL_VERSION", ssl.PROTOCOL_TLSv1)
            if verify_https:
                kwargs["cert_reqs"] = "CERT_REQUIRED"
                kwargs["ca_certs"] = ca_certs

        return connection_from_url(host, **kwargs)

# === BLOCK 6 (label=human, source_idx=line2676_human, name=update_value) ===
def update_value(self, uid, **kwargs):
        """
        Updates contact's custom field value.
        Returns :class:`Contact` object contains id and link to Contact.

        :Example:

        client.custom_fields.update_value(uid=1900901, contact_id=192012, value="abc")

        :param int uid:        The unique id of the CustomField to update a value. Required.
        :param int contactId:  The unique id of the Contact to update value. Required.
        :param str value:      Value of CustomField. Required.
        """
        contacts = Contacts(self.base_uri, self.auth)
        return self.update_subresource_instance(uid, body=kwargs,
                                                subresource=contacts,
                                                slug="update")
