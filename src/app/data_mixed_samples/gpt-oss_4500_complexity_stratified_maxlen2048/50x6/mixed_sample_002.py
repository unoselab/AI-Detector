# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2624_lm, name=censor) ===
def censor(self, input_text):
        """Returns input_text with any profane words censored."""
        import re
        words = getattr(self, "profane_words", [])
        if not words:
            return input_text
        pattern = re.compile(r'\b(' + '|'.join(map(re.escape, words)) + r')\b', flags=re.IGNORECASE)
        return pattern.sub(lambda m: '*' * len(m.group()), input_text)

# === BLOCK 2 (label=lm, source_idx=line1282_lm, name=transformToNative) ===
def transformToNative(obj):
        """
        Turn obj.value into a list of dates, datetimes, or
        (datetime, timedelta) tuples.
        """

# === BLOCK 3 (label=lm, source_idx=line1291_lm, name=safe_record) ===
def safe_record(ctx, item):
    """Make sure we get a record instance even if we pass an xmlid."""
    # Resolve environment from ctx (could be an object with

# === BLOCK 4 (label=lm, source_idx=line5205_lm, name=get_signalcheck) ===
def get_signalcheck(self, sar, **params):
        """get_signalcheck -  perform a signal check.

        Parameters
        ----------
        sar : dict
            signal-api-request specified as a dictionary of parameters.
            All of these parameters are optional. For details
            check https://api.postcode.nl/documentation/signal-api-example.

        returns :
            a response dictionary
        """
        # Prepare request payload by merging SAR dict with any additional parameters
        payload = {} if sar is None else dict(sar)
        if params:
            payload.update(params)

        # Determine the endpoint URL; assume the base URL is stored in self.base_url
        base = getattr(self, "base_url", "").rstrip("/")
        url = f"{base}/signalcheck"

        # Use an existing session if available, otherwise fall back to requests module
        session = getattr(self, "session", None)
        try:
            if session is not None:
                resp = session.post(url, json=payload)
            else:
                import requests
                resp = requests.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            # Return a consistent error structure
            return {"error": str(exc), "status_code": getattr(resp, "status_code", None)}

# === BLOCK 5 (label=lm, source_idx=line1742_lm, name=set_attachments_order) ===
def set_attachments_order(self, order):
        """Remember the attachments order
        """
        if not isinstance(order, (list, tuple)):
            raise TypeError("order must be a list or tuple")
        # Store a shallow copy to avoid external mutations
        self._attachments_order = list(order)

# === BLOCK 6 (label=lm, source_idx=line4184_lm, name=load_alias_hash) ===
def load_alias_hash(self):
        """
        Load (create, if not exist) the alias hash file.
        """
        import os, json

        path = getattr(self, "alias_hash_path", None)
        if path is None:
            raise AttributeError("alias_hash_path attribute is missing")

        if not os.path.exists(path):
            # Create an empty alias hash file
            with open(path, "w", encoding="utf-8") as f:
                json.dump({}, f)
            self.alias_hash = {}
        else:
            with open(path, "r", encoding="utf-8") as f:
                try:
                    self.alias_hash = json.load(f)
                except json.JSONDecodeError:
                    # Corrupted file – reset to empty dict
                    self.alias_hash = {}
                    with open(path, "w", encoding="utf-8") as wf:
                        json.dump(self.alias_hash, wf)

        return self.alias_hash
