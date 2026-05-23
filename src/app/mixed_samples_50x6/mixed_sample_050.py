# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2423_human, name=_get_script) ===
def _get_script(self):
        """Returns fixed commands script.

        If `settings.repeat` is `True`, appends command with second attempt
        of running fuck in case fixed command fails again.

        """
        if settings.repeat:
            repeat_fuck = '{} --repeat {}--force-command {}'.format(
                get_alias(),
                '--debug ' if settings.debug else '',
                shell.quote(self.script))
            return shell.or_(self.script, repeat_fuck)
        else:
            return self.script

# === BLOCK 2 (label=human, source_idx=line2893_human, name=V) ===
def V(self,*args,**kwargs):
        """
        NAME:

           V

        PURPOSE:

           return Heliocentric Galactic rectangular y-velocity (aka "V")

        INPUT:

           t - (optional) time at which to get V (can be Quantity)

           obs=[X,Y,Z,vx,vy,vz] - (optional) position and velocity of observer 
                         in the Galactocentric frame
                         (in kpc and km/s) (default=[8.0,0.,0.,0.,220.,0.]; entries can be Quantity)
                         OR Orbit object that corresponds to the orbit
                         of the observer
                         Y is ignored and always assumed to be zero

           ro= (Object-wide default) physical scale for distances to use to convert (can be Quantity)

           vo= (Object-wide default) physical scale for velocities to use to convert (can be Quantity)

        OUTPUT:

           V(t) in km/s

        HISTORY:

           2011-02-24 - Written - Bovy (NYU)

        """
        out= self._orb.V(*args,**kwargs)
        if len(out) == 1: return out[0]
        else: return out

# === BLOCK 3 (label=human, source_idx=line1925_human, name=image_request_response) ===
def image_request_response(self, path):
        """Parse image request and create response."""
        # Parse the request in path
        if (len(path) > 1024):
            raise IIIFError(code=414,
                            text="URI Too Long: Max 1024 chars, got %d\n" % len(path))
        try:
            self.iiif.identifier = self.identifier
            self.iiif.parse_url(path)
        except IIIFRequestPathError as e:
            # Reraise as IIIFError with code=404 because we can't tell
            # whether there was an encoded slash in the identifier or
            # whether there was a bad number of path segments.
            raise IIIFError(code=404, text=e.text)
        except IIIFError as e:
            # Pass through
            raise e
        except Exception as e:
            # Something completely unexpected => 500
            raise IIIFError(code=500,
                            text="Internal Server Error: unexpected exception parsing request (" + str(e) + ")")
        dr = degraded_request(self.identifier)
        if (dr):
            self.logger.info("image_request: degraded %s -> %s" %
                             (self.identifier, dr))
            self.degraded = self.identifier
            self.identifier = dr
            self.iiif.quality = 'gray'
        else:
            # Parsed request OK, attempt to fulfill
            self.logger.info("image_request: %s" % (self.identifier))
        file = self.file
        self.manipulator.srcfile = file
        self.manipulator.do_first()
        if (self.api_version < '2.0' and
                self.iiif.format is None and
                'Accept' in request.headers):
            # In 1.0 and 1.1 conneg was specified as an alternative to format, see:
            # http://iiif.io/api/image/1.0/#format
            # http://iiif.io/api/image/1.1/#parameters-format
            formats = {'image/jpeg': 'jpg', 'image/tiff': 'tif',
                       'image/png': 'png', 'image/gif': 'gif',
                       'image/jp2': 'jps', 'application/pdf': 'pdf'}
            accept = do_conneg(request.headers['Accept'], list(formats.keys()))
            # Ignore Accept header if not recognized, should this be an error
            # instead?
            if (accept in formats):
                self.iiif.format = formats[accept]
        (outfile, mime_type) = self.manipulator.derive(file, self.iiif)
        # FIXME - find efficient way to serve file with headers
        self.add_compliance_header()
        return send_file(outfile, mimetype=mime_type)

# === BLOCK 4 (label=lm, source_idx=line2880_lm, name=parse_pkg_info) ===
def parse_pkg_info(fn):
    """
    :param str fn:
    :rtype: dict[str,str]
    """
    with open(fn) as f:
        lines = f.readlines()

    pkg_info = {}
    for line in lines:
        if line.strip():
            key, value = line.split('=', 1)
            pkg_info[key] = value.strip()

    return pkg_info

# === BLOCK 5 (label=lm, source_idx=line2266_lm, name=add_manager) ===
def add_manager(self, manager):
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        if not isinstance(manager, str):
            raise TypeError("manager must be a string")

        self.managers.append(manager)

# === BLOCK 6 (label=lm, source_idx=line739_lm, name=create_pool) ===
def create_pool(self):
        """
        Return a ConnectionPool instance of given host
        :param socket_timeout:
            socket timeout for each connection in seconds
        """
        return ConnectionPool(host=self.host, port=self.port, socket_timeout=socket_timeout)
