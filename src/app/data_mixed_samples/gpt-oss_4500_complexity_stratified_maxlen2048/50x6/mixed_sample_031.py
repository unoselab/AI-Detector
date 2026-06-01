# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6648_lm, name=default_dtype) ===
def default_dtype(field=None):
        """Return the default data type of this class for a given field.

        Parameters
        ----------
        field : `Field`, optional
            Set of numbers to be represented by a data type.
            Currently supported : `RealNumbers`, `ComplexNumbers`
            The default ``None`` means `RealNumbers`

        Returns
        -------
        dtype : `numpy.dtype`
            Numpy data type specifier. The returned defaults are:

                ``RealNumbers()`` : ``np.dtype('float64')``

                ``ComplexNumbers()`` : ``np.dtype('complex128')``
        """
        import numpy as np
        if field is None:
            return np.dtype('float64')
        cls = field if isinstance(field, type) else type(field)
        name = getattr(cls, '__name__', str(cls))
        if name == 'RealNumbers':
            return np.dtype('float64')
        if name == 'ComplexNumbers':
            return

# === BLOCK 2 (label=human, source_idx=line6179_human, name=upload_object) ===
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
    conn = _get_driver(profile=profile)
    libcloud_kwargs = salt.utils.args.clean_kwargs(**libcloud_kwargs)
    container = conn.get_container(container_name)
    obj = conn.upload_object(file_path, container, object_name, extra, verify_hash, headers, **libcloud_kwargs)
    return obj.name

# === BLOCK 3 (label=human, source_idx=line6367_human, name=handler) ===
def handler(key_file=None, cert_file=None, timeout=None, verify=False):
    """This class returns an instance of the default HTTP request handler using
    the values you provide.

    :param `key_file`: A path to a PEM (Privacy Enhanced Mail) formatted file containing your private key (optional).
    :type key_file: ``string``
    :param `cert_file`: A path to a PEM (Privacy Enhanced Mail) formatted file containing a certificate chain file (optional).
    :type cert_file: ``string``
    :param `timeout`: The request time-out period, in seconds (optional).
    :type timeout: ``integer`` or "None"
    :param `verify`: Set to False to disable SSL verification on https connections.
    :type verify: ``Boolean``
    """

    def connect(scheme, host, port):
        kwargs = {}
        if timeout is not None: kwargs['timeout'] = timeout
        if scheme == "http":
            return six.moves.http_client.HTTPConnection(host, port, **kwargs)
        if scheme == "https":
            if key_file is not None: kwargs['key_file'] = key_file
            if cert_file is not None: kwargs['cert_file'] = cert_file

            # If running Python 2.7.9+, disable SSL certificate validation
            if (sys.version_info >= (2,7,9) and key_file is None and cert_file is None) and not verify:
                kwargs['context'] = ssl._create_unverified_context()
            return six.moves.http_client.HTTPSConnection(host, port, **kwargs)
        raise ValueError("unsupported scheme: %s" % scheme)

    def request(url, message, **kwargs):
        scheme, host, port, path = _spliturl(url)
        body = message.get("body", "")
        head = {
            "Content-Length": str(len(body)),
            "Host": host,
            "User-Agent": "splunk-sdk-python/1.6.6",
            "Accept": "*/*",
            "Connection": "Close",
        } # defaults
        for key, value in message["headers"]:
            head[key] = value
        method = message.get("method", "GET")

        connection = connect(scheme, host, port)
        is_keepalive = False
        try:
            connection.request(method, path, body, head)
            if timeout is not None:
                connection.sock.settimeout(timeout)
            response = connection.getresponse()
            is_keepalive = "keep-alive" in response.getheader("connection", default="close").lower()
        finally:
            if not is_keepalive:
                connection.close()

        return {
            "status": response.status,
            "reason": response.reason,
            "headers": response.getheaders(),
            "body": ResponseReader(response, connection if is_keepalive else None),
        }

    return request

# === BLOCK 4 (label=human, source_idx=line1324_human, name=dec) ===
def dec(self, byts):
        """
        Decode an envelope dict and decrypt the given bytes.

        Args:
            byts (bytes): Bytes to decrypt.

        Returns:
            bytes: Decrypted message.
        """
        envl = s_msgpack.un(byts)
        iv = envl.get('iv', b'')
        asscd = envl.get('asscd', b'')
        data = envl.get('data', b'')

        decryptor = AESGCM(self.ekey)

        try:
            data = decryptor.decrypt(iv, data, asscd)
        except Exception:
            logger.exception('Error decrypting data')
            return None
        return data

# === BLOCK 5 (label=lm, source_idx=line1835_lm, name=push_irq_registers) ===
def push_irq_registers(self):
        """
        push PC, U, Y, X, DP, B, A, CC on System stack pointer
        """

# === BLOCK 6 (label=lm, source_idx=line4776_lm, name=kill) ===
def kill(self, block=False):
        """
        Kill the daemon process.

        Sends the SIGKILL signal to the daemon process, killing it. You
        probably want to try :py:meth:`stop` first.

        If ``block`` is true then the call blocks until the daemon
        process has exited. ``block`` can either be ``True`` (in which
        case it blocks indefinitely) or a timeout in seconds.

        Returns ``True`` if the daemon process has (already) exited and
        ``False`` otherwise.

        The PID file is always removed, whether the process has already
        exited or not. Note that this means that subsequent calls to
        :py:meth:`is_running` and :py:meth:`get_pid` will behave as if
        the process has exited. If you need to be sure that the process
        has already exited, set ``block`` to ``True``.

        .. versionadded:: 0.5.1
            The ``block`` parameter
        """
