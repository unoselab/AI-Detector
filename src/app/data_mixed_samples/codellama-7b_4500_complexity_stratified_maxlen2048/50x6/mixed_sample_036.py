# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line35_human, name=to_data) ===
def to_data(self, value):
        """
        Coerce python data type to simple form for serialization.
        If default value was defined returns the default value if None was passed.
        Throw exception is value is ``None`` is ``required`` is set to ``True``
        """
        try:
            if value is None and self._default is not None:
                return self._export(self.default)
            self._check_required(value)
            value = self._export(value)
            return value
        except ValueError as ex:
            raise ValueError(ex, self._errors['to_data'])

# === BLOCK 2 (label=lm, source_idx=line430_lm, name=from_dict) ===
def from_dict(cls, d):
        """Create cache hierarchy from dictionary."""
        return cls(**d)

# === BLOCK 3 (label=human, source_idx=line815_human, name=strip_linebreaks) ===
def strip_linebreaks(s):
    """ Strip excess line breaks from a string """
    return u"\n".join([c for c in s.split(u'\n') if c])

# === BLOCK 4 (label=human, source_idx=line504_human, name=resize) ===
def resize(self, size=None):
        """
        Resize the container's PTY.

        If `size` is not None, it must be a tuple of (height,width), otherwise
        it will be determined by the size of the current TTY.
        """

        if not self.israw():
            return

        size = size or tty.size(self.stdout)

        if size is not None:
            rows, cols = size
            try:
                self.client.resize(self.container, height=rows, width=cols)
            except IOError: # Container already exited
                pass

# === BLOCK 5 (label=lm, source_idx=line3757_lm, name=get_absolute_name) ===
def get_absolute_name(self):
        """ Returns the full dotted name of this field """
        return self.model._meta.app_label + '.' + self.name

# === BLOCK 6 (label=lm, source_idx=line8791_lm, name=get_input) ===
def get_input(self):
        """ Loads web input, initialise default values and check/sanitise some inputs from users """
        self.input = {}
        self.input['url'] = self.get_url()
        self.input['username'] = self.get_username()
        self.input['password'] = self.get_password()
        self.input['proxy'] = self.get_proxy()
        self.input['proxy_username'] = self.get_proxy_username()
        self.input['proxy_password'] = self.get_proxy_password()
        self.input['timeout'] = self.get_timeout()
        self.input['verify_ssl'] = self.get_verify_ssl()
        self.input['proxy_type'] = self.get_proxy_type()
        self.input['headers'] = self.get_headers()
        self.input['cookies'] = self.get_cookies()
        self.input['data'] = self.get_data()
        self.input['json'] = self.get_json()
        self.input['files'] = self.get_files()
        self.input['params'] = self.get_params()
        self.input['auth'] = self.get_auth()
        self.input['cert'] = self.get_cert()
        self.input['key'] = self.get_key()
        self.input['ca_cert'] = self.get_ca_cert()
        self.input['client_cert'] = self.get_client_cert()
        self.input['client_key'] = self.get_client_key()
        self.input['client_ca_cert'] = self.get_client_ca_cert()
        self.input['client_key_pass'] = self.get_client_key_pass()
        self.input['client_cert_pass'] = self.get_client_cert_pass()
        self.input['auth_type'] = self.get_auth_type()
        self.input['auth_credentials'] = self.get_auth_credentials()
        self.input['auth_extra_kwargs'] = self.get_auth_extra_kwargs()
        self.input['auth_extra_kwargs_value'] = self.get_auth_extra_kwargs_value()
