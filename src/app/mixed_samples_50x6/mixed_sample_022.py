# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1686_lm, name=is_valid) ===
def is_valid(self, request_data, request_id=None, raise_exceptions=False):
        """
        Determines if the SAML LogoutResponse is valid
        :param request_id: The ID of the LogoutRequest sent by this SP to the IdP
        :type request_id: string

        :param raise_exceptions: Whether to return false on failure or raise an exception
        :type raise_exceptions: Boolean

        :return: Returns if the SAML LogoutResponse is or not valid
        :rtype: boolean
        """
        if not request_data:
            if raise_exceptions:
                raise ValueError("Request data is required")
            return False
        if request_id and request_id!= request_data.get("LogoutRequestID"):
            if raise_exceptions:
                raise ValueError("Request ID does not match")
            return False

        return True

# === BLOCK 2 (label=lm, source_idx=line2964_lm, name=encode_aes256) ===
def encode_aes256(key, plaintext):
    """
    Utility method to encode some given plaintext with the given key. Important thing to note:

    This is not a general purpose encryption method - it has specific semantics (see below for
    details).

    Takes the given hex string key and converts it to a 256 bit binary blob. Then pads the given
    plaintext to AES block size which is always 16 bytes, regardless of AES key size. Then
    encrypts using AES-256-CBC using a random IV. Then converts both the IV and the ciphertext
    to hex. Finally returns the IV appended by the ciphertext.

    :param key: string, 64 hex chars long
    :param plaintext: string, any amount of data
    """
    def encode_aes256(key, plaintext):
        key_bytes = bytes.fromhex(key)
        plaintext_bytes = pad(plaintext.encode(), 16)
        iv = os.urandom(16)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv)
        ciphertext = cipher.encrypt(plaintext_bytes)
        iv_hex = iv.hex()
        ciphertext_hex = ciphertext.hex()
        return iv_hex + ciphertext_hex

# === BLOCK 3 (label=human, source_idx=line293_human, name=_compute_precision) ===
def _compute_precision(references, translation, n):
    """Compute ngram precision.

    Parameters
    ----------
    references: list(list(str))
        A list of references.
    translation: list(str)
        A translation.
    n: int
        Order of n-gram.

    Returns
    -------
    matches: int
        Number of matched nth order n-grams
    candidates
        Number of possible nth order n-grams
    """
    matches = 0
    candidates = 0
    ref_ngram_counts = Counter()

    for reference in references:
        ref_ngram_counts |= _ngrams(reference, n)
    trans_ngram_counts = _ngrams(translation, n)
    overlap_ngram_counts = trans_ngram_counts & ref_ngram_counts
    matches += sum(overlap_ngram_counts.values())
    possible_matches = len(translation) - n + 1
    if possible_matches > 0:
        candidates += possible_matches

    return matches, candidates

# === BLOCK 4 (label=lm, source_idx=line590_lm, name=and_next) ===
def and_next(e):
    """
    Create a PEG function for positive lookahead.
    """
    def and_next_func(s, i):
        match = e(s, i)
        if match is not None:
            return match[1]
        return None
    return and_next_func

# === BLOCK 5 (label=human, source_idx=line2907_human, name=create_hosting_device_resources) ===
def create_hosting_device_resources(self, context, complementary_id,
                                        tenant_id, mgmt_context, max_hosted):
        """Create resources for a hosting device in a plugin specific way."""
        mgmt_port = None
        if mgmt_context and mgmt_context.get('mgmt_nw_id') and tenant_id:
            # Create port for mgmt interface
            p_spec = {'port': {
                'tenant_id': tenant_id,
                'admin_state_up': True,
                'name': 'mgmt',
                'network_id': mgmt_context['mgmt_nw_id'],
                'mac_address': bc.constants.ATTR_NOT_SPECIFIED,
                'fixed_ips': self._mgmt_subnet_spec(context, mgmt_context),
                'device_id': "",
                # Use device_owner attribute to ensure we can query for these
                # ports even before Nova has set device_id attribute.
                'device_owner': complementary_id}}
            try:
                mgmt_port = self._core_plugin.create_port(context, p_spec)
            except n_exc.NeutronException as e:
                LOG.error('Error %s when creating management port. '
                          'Cleaning up.', e)
                self.delete_hosting_device_resources(
                    context, tenant_id, mgmt_port)
                mgmt_port = None
        # We are setting the 'ports' to an empty list as it is expected by
        # the callee: device_handling_db._create_svc_vm_hosting_devices()
        return {'mgmt_port': mgmt_port, 'ports': []}

# === BLOCK 6 (label=human, source_idx=line2468_human, name=install) ===
def install(runas=None, path=None):
    """
    Install rbenv systemwide

    CLI Example:

    .. code-block:: bash

        salt '*' rbenv.install
    """
    path = path or _rbenv_path(runas)
    path = os.path.expanduser(path)
    return _install_rbenv(path, runas) and _install_ruby_build(path, runas)
