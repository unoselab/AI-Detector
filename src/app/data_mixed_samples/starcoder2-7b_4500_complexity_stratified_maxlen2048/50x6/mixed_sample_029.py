# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1381_human, name=_get_file_name) ===
def _get_file_name(self, contentDisposition,
                       url, ext=".unknown"):
        """ gets the file name from the header or url if possible """
        if self.PY2:
            if contentDisposition is not None:
                return re.findall(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)',
                                  contentDisposition.strip().replace('"', ''))[0][0]
            elif os.path.basename(url).find('.') > -1:
                return os.path.basename(url)
        elif self.PY3:
            if contentDisposition is not None:
                p = re.compile(r'filename[^;=\n]*=(([\'"]).*?\2|[^;\n]*)')
                return p.findall(contentDisposition.strip().replace('"', ''))[0][0]
            elif os.path.basename(url).find('.') > -1:
                return os.path.basename(url)
        return "%s.%s" % (uuid.uuid4().get_hex(), ext)

# === BLOCK 2 (label=lm, source_idx=line1479_lm, name=snmp_server_engineID_drop_engineID_local) ===
def snmp_server_engineID_drop_engineID_local(self, **kwargs):
        """Auto Generated Code
        """
        config = ET.Element("config")
        snmp = ET.SubElement(config, "snmp", xmlns="urn:brocade.com:mgmt:brocade-snmp")
        server = ET.SubElement(snmp, "server")
        engineID = ET.SubElement(server, "engineID")
        drop = ET.SubElement(engineID, "drop")
        engineID_local = ET.SubElement(drop, "engineID-local")

        callback = kwargs.pop('callback', self._callback)
        return callback(config)

# === BLOCK 3 (label=human, source_idx=line6213_human, name=subscribe) ===
def subscribe(self, request, *args, **kwargs):
        """ Performs the subscribe action. """
        self.object = self.get_object()
        self.object.subscribers.add(request.user)
        messages.success(self.request, self.success_message)
        return HttpResponseRedirect(self.get_success_url())

# === BLOCK 4 (label=lm, source_idx=line5885_lm, name=is_reachable_host) ===
def is_reachable_host(entity_name):
    """
    Returns a bool telling if the entity name is a reachable host (IPv4/IPv6/FQDN/etc).
    :param hostname:
    :return:
    """
    try:
        socket.gethostbyname(entity_name)
        return True
    except socket.gaierror:
        return False

# === BLOCK 5 (label=lm, source_idx=line385_lm, name=register) ===
def register(self, name):
        """
        Register configuration for an editor instance.

        Arguments:
            name (string): Config name from available ones in
                ``settings.CODEMIRROR_SETTINGS``.

        Raises:
            UnknowConfigError: If given config name does not exist in
                ``settings.CODEMIRROR_SETTINGS``.

        Returns:
            dict: Registred config dict.
        """
        if name not in settings.CODEMIRROR_SETTINGS:
            raise UnknowConfigError(
                'Config name "%s" does not exist in '
               'settings.CODEMIRROR_SETTINGS.' % name
            )
        return settings.CODEMIRROR_SETTINGS[name]

# === BLOCK 6 (label=human, source_idx=line2934_human, name=dropfile) ===
def dropfile(cachedir, user=None):
    """
    Set an AES dropfile to request the master update the publish session key
    """
    dfn = os.path.join(cachedir, '.dfn')
    # set a mask (to avoid a race condition on file creation) and store original.
    with salt.utils.files.set_umask(0o277):
        log.info('Rotating AES key')
        if os.path.isfile(dfn):
            log.info('AES key rotation already requested')
            return

        if os.path.isfile(dfn) and not os.access(dfn, os.W_OK):
            os.chmod(dfn, stat.S_IRUSR | stat.S_IWUSR)
        with salt.utils.files.fopen(dfn, 'wb+') as fp_:
            fp_.write(b'')
        os.chmod(dfn, stat.S_IRUSR)
        if user:
            try:
                import pwd
                uid = pwd.getpwnam(user).pw_uid
                os.chown(dfn, uid, -1)
            except (KeyError, ImportError, OSError, IOError):
                pass
