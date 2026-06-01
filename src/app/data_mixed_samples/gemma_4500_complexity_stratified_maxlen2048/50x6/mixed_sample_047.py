# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6639_lm, name=map_over_glob) ===
def map_over_glob(fn, path, pattern):
    """map a function over a glob pattern, relative to a directory"""
    import glob
    import os

    files = glob.glob(os.path.join(path, pattern))
    return [fn(os.path.join(path, f)) if not os.path.isabs(f) else fn(f) for f in files] if not path else [fn(os.path.join(path, f)) for f in glob.glob(pattern)]

    # Correction for the logic to properly handle the relative pathing as requested by the docstring:
    import glob
    import os

    paths = glob.glob(os.path.join(path, pattern))
    return [fn(p) for p in paths]

# === BLOCK 2 (label=human, source_idx=line8204_human, name=encode_osgi_props) ===
def encode_osgi_props(ed):
    # type: (EndpointDescription) -> Dict[str, str]
    """
    Prepares a dictionary of OSGi properties for the given EndpointDescription
    """
    result_props = {}
    intfs = ed.get_interfaces()
    result_props[OBJECTCLASS] = " ".join(intfs)
    for intf in intfs:
        pkg_name = package_name(intf)
        ver = ed.get_package_version(pkg_name)
        if ver and not ver == (0, 0, 0):
            result_props[ENDPOINT_PACKAGE_VERSION_] = ".".join(
                str(v) for v in ver
            )

    result_props[ENDPOINT_ID] = ed.get_id()
    result_props[ENDPOINT_SERVICE_ID] = "{0}".format(ed.get_service_id())
    result_props[ENDPOINT_FRAMEWORK_UUID] = ed.get_framework_uuid()
    imp_configs = ed.get_imported_configs()
    if imp_configs:
        result_props[SERVICE_IMPORTED_CONFIGS] = " ".join(
            ed.get_imported_configs()
        )
    intents = ed.get_intents()
    if intents:
        result_props[SERVICE_INTENTS] = " ".join(intents)
    remote_configs = ed.get_remote_configs_supported()
    if remote_configs:
        result_props[REMOTE_CONFIGS_SUPPORTED] = " ".join(remote_configs)
    remote_intents = ed.get_remote_intents_supported()
    if remote_intents:
        result_props[REMOTE_INTENTS_SUPPORTED] = " ".join(remote_intents)
    return result_props

# === BLOCK 3 (label=human, source_idx=line2826_human, name=on_send) ===
def on_send(self, frame):
        """
        Add the heartbeat header to the frame when connecting, and bump
        next outbound heartbeat timestamp.

        :param Frame frame: the Frame object
        """
        if frame.cmd == CMD_CONNECT or frame.cmd == CMD_STOMP:
            if self.heartbeats != (0, 0):
                frame.headers[HDR_HEARTBEAT] = '%s,%s' % self.heartbeats
        if self.next_outbound_heartbeat is not None:
            self.next_outbound_heartbeat = monotonic() + self.send_sleep

# === BLOCK 4 (label=human, source_idx=line3400_human, name=_zforce) ===
def _zforce(self,R,z,phi=0,t=0):
        """
        NAME:
           _zforce
        PURPOSE:
           evaluate the vertical force at (R,z, phi)
        INPUT:
           R - Cylindrical Galactocentric radius
           z - vertical height
           phi - azimuth
           t - time
        OUTPUT:
           vertical force at (R,z, phi)
        HISTORY:
           2016-12-26 - Written - Bovy (UofT/CCA)
        """
        r= numpy.sqrt(R**2.+z**2.)
        out= self._scf.zforce(R,z,phi=phi,use_physical=False)
        for a,s,ds,H,dH in zip(self._Sigma_amp,self._Sigma,self._dSigmadR,
                             self._Hz,self._dHzdz):
            out-= 4.*numpy.pi*a*(ds(r)*H(z)*z/r+s(r)*dH(z))
        return out

# === BLOCK 5 (label=lm, source_idx=line3673_lm, name=default) ===
def default(self, meth):
        """
        Decorator that allows to set the default for an attribute.

        Returns *meth* unchanged.

        :raises DefaultAlreadySetError: If default has been set before.

        .. versionadded:: 17.1.0
        """
        raise DefaultAlreadySetError()
        setattr(self, '_default_set', True)
        return meth

# === BLOCK 6 (label=lm, source_idx=line6093_lm, name=labels) ===
def labels(self):
        """ Returns symbol instances corresponding to labels
        in the current scope.
        """
        return [symbol for symbol in self.symbols if symbol.is_label]
