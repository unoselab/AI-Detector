# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4237_human, name=resolve_service_spec) ===
def resolve_service_spec(self, name, lineno):
        """Finds and links the ServiceSpec with the given name."""

        if name in self.service_specs:
            return self.service_specs[name].link(self)

        if '.' in name:
            include_name, component = name.split('.', 2)
            if include_name in self.included_scopes:
                return self.included_scopes[
                    include_name
                ].resolve_service_spec(component, lineno)

        raise ThriftCompilerError(
            'Unknown service "%s" referenced at line %d%s' % (
                name, lineno, self.__in_path()
            )
        )

# === BLOCK 2 (label=lm, source_idx=line3644_lm, name=clean_text) ===
def clean_text(self, domain, **kwargs):
        """Try to extract only the domain bit from the """
        if domain is None:
            return None
        if domain.startswith('http://'):
            domain = domain[7:]
        if domain.startswith('https://'):
            domain = domain[8:]
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain

# === BLOCK 3 (label=human, source_idx=line969_human, name=reply_inform) ===
def reply_inform(self, connection, inform, orig_req):
        """Send an inform as part of the reply to an earlier request.

        Parameters
        ----------
        connection : ClientConnection object
            The client to send the inform to.
        inform : Message object
            The inform message to send.
        orig_req : Message object
            The request message being replied to. The inform message's
            id is overridden with the id from orig_req before the
            inform is sent.

        """
        if isinstance(connection, ClientRequestConnection):
            self._logger.warn(
                'Deprecation warning: do not use self.reply_inform() '
                'within a reply handler context -- '
                'use req.inform(*inform_arguments)\n'
                'Traceback:\n %s', "".join(traceback.format_stack()))
            # Get the underlying ClientConnection instance
            connection = connection.client_connection
        connection.reply_inform(inform, orig_req)

# === BLOCK 4 (label=lm, source_idx=line8714_lm, name=cache_key_exist) ===
def cache_key_exist(self, key):
        """Returns if a key from cache exist"""
        return self.cache.exists(key)

# === BLOCK 5 (label=lm, source_idx=line6753_lm, name=clock_resized_cb) ===
def clock_resized_cb(self, viewer, width, height):
        """This method is called when an individual clock is resized.
        It deletes and reconstructs the placement of the text objects
        in the canvas.
        """
        self.clock_resized(viewer, width, height)

# === BLOCK 6 (label=human, source_idx=line4305_human, name=_getphoto_originalsize) ===
def _getphoto_originalsize(self,pid):
        """Asks flickr for photo original size
        returns tuple with width,height
        """

        logger.debug('%s - Getting original size from flickr'%(pid))

        width=None
        height=None

        resp=self.flickr.photos_getSizes(photo_id=pid)
        if resp.attrib['stat']!='ok':
            logger.error("%s - flickr: photos_getSizes failed with status: %s",\
                    resp.attrib['stat']);
            return (None,None)

        for size in resp.find('sizes').findall('size'):
            if size.attrib['label']=="Original":
                width=int(size.attrib['width'])
                height=int(size.attrib['height'])
                logger.debug('Found pid %s original size of %s,%s'\
                    %(pid,width,height))

        return (width,height)
