# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2732_lm, name=require_flush) ===
def require_flush(fun):
    """Decorator for methods that need to query security.

    It ensures all security related operations are flushed to DB, but
    avoids unneeded flushes.
    """
    import functools

    @functools.wraps(fun)
    def _wrapper(self, *args, **kwargs):
        # Try common attribute names for a SQLAlchemy session
        session = getattr(self, "session", None) or getattr(self, "db_session", None)
        if session is not None:
            # Flush only if there are pending changes
            if session.new or session.dirty or session.deleted:
                session.flush()
        return fun(self, *args, **kwargs)

    return _wrapper

# === BLOCK 2 (label=human, source_idx=line4901_human, name=stop_request) ===
def stop_request(self, stop_now='0'):
        """Request the daemon to stop

        If `stop_now` is set to '1' the daemon will stop now. Else, the daemon
        will enter the stop wait mode. In this mode the daemon stops its activity and
        waits until it receives a new `stop_now` request to stop really.

        :param stop_now: stop now or go to stop wait mode
        :type stop_now: bool
        :return: None
        """
        self.app.interrupted = (stop_now == '1')
        self.app.will_stop = True

        return True

# === BLOCK 3 (label=human, source_idx=line453_human, name=is_all_field_none) ===
def is_all_field_none(self):
        """
        :rtype: bool
        """

        if self._user_alias is not None:
            return False

        if self._alias is not None:
            return False

        if self._counterparty_alias is not None:
            return False

        if self._status is not None:
            return False

        if self._sub_status is not None:
            return False

        if self._time_start_desired is not None:
            return False

        if self._time_start_actual is not None:
            return False

        if self._time_end is not None:
            return False

        if self._attachment is not None:
            return False

        return True

# === BLOCK 4 (label=lm, source_idx=line729_lm, name=__remote_path_rewrite) ===
def __remote_path_rewrite(self, dataset_path, dataset_path_type, name=None):
        """ Return remote path of this file (if staging is required) else None.
        """
        import os

        remote_schemes = ("s3://", "gs://", "http://", "https://", "ftp://")
        # If the path already looks like a remote URL, just return it.
        if isinstance(dataset_path, str) and dataset_path.startswith(remote_schemes):
            return dataset_path

        # Types that do not require staging – return None.
        if dataset_path_type in ("local", "inline", "memory"):
            return None

        # Build a remote path; optionally append

# === BLOCK 5 (label=lm, source_idx=line3585_lm, name=EncryptPrivateKey) ===
def EncryptPrivateKey(self, decrypted):
        """
        Encrypt the provided plaintext with the initialized private key.

        Args:
            decrypted (byte string): the plaintext to be encrypted.

        Returns:
            bytes: the ciphertext.
        """
        from cryptography.hazmat.primitives import hashes

# === BLOCK 6 (label=human, source_idx=line6405_human, name=_send_request) ===
def _send_request(self, enforce_json, method, raise_for_status,
                      url, **kwargs):
        """Send HTTP request.

        Args:
             enforce_json (bool): Require properly-formatted JSON or raise :exc:`~pancloud.exceptions.PanCloudError`. Defaults to ``False``.
             method (str): HTTP method.
             raise_for_status (bool): If ``True``, raises :exc:`~pancloud.exceptions.HTTPError` if status_code not in 2XX. Defaults to ``False``.
             url (str): Request URL.
             **kwargs (dict): Re-packed key-word arguments.

         Returns:
            requests.Response: Requests Response() object

        """
        r = self.session.request(method, url, **kwargs)
        if raise_for_status:
            r.raise_for_status()
        if enforce_json:
            if 'application/json' in self.session.headers.get(
                'Accept', ''
            ):
                try:
                    r.json()
                except ValueError as e:
                    raise PanCloudError(
                        "Invalid JSON: {}".format(e)
                    )
        return r
