# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1560_human, name=sampled_logs) ===
def sampled_logs(self, logs_limit=-1):
        """Return up to `logs_limit` logs.

        If `logs_limit` is -1, this function will return all logs that belong
        to the result.
        """
        logs_count = len(self.logs)
        if logs_limit == -1 or logs_count <= logs_limit:
            return self.logs
        elif logs_limit == 0:
            return []
        elif logs_limit == 1:
            return [self.logs[-1]]
        else:
            def get_sampled_log(idx):
                # always include the first and last element of `self.logs`
                return self.logs[idx * (logs_count - 1) // (logs_limit - 1)]
            return [get_sampled_log(i) for i in range(logs_limit)]

# === BLOCK 2 (label=human, source_idx=line3801_human, name=to_dataframe) ===
def to_dataframe(self) -> "pandas.DataFrame":
        """Convert to pandas DataFrame.

        This is not a lossless conversion - (under/over)flow info is lost.
        """
        import pandas as pd
        df = pd.DataFrame(
            {
                "left": self.bin_left_edges,
                "right": self.bin_right_edges,
                "frequency": self.frequencies,
                "error": self.errors,
            },
            columns=["left", "right", "frequency", "error"])
        return df

# === BLOCK 3 (label=lm, source_idx=line4505_lm, name=_encode_request) ===
def _encode_request(self, request):
        """Encode a request object"""
        return json.dumps(request).encode("utf-8")

# === BLOCK 4 (label=human, source_idx=line2513_human, name=run_gevent) ===
def run_gevent(self):
        """Created the server that runs the application supplied a subclass"""
        from pywb.utils.geventserver import GeventServer, RequestURIWSGIHandler
        logging.info('Starting Gevent Server on ' + str(self.r.port))
        ge = GeventServer(self.application,
                          port=self.r.port,
                          hostname=self.r.bind,
                          handler_class=RequestURIWSGIHandler,
                          direct=True)

# === BLOCK 5 (label=lm, source_idx=line1720_lm, name=call) ===
def call(corofunc, *args, **kwargs):
    """
    :return:
        a delegator function that returns a coroutine object by calling
        ``corofunc(seed_tuple, *args, **kwargs)``.
    """
    def delegator(*args, **kwargs):
        seed_tuple = (corofunc, args, kwargs)
        return corofunc(seed_tuple, *args, **kwargs)
    return delegator

# === BLOCK 6 (label=lm, source_idx=line1412_lm, name=adev) ===
def adev(self, tau0, tau):
        """ return predicted ADEV of noise-type at given tau

        """
        if tau < tau0:
            return 0
        elif tau0 <= tau <= self.tau_c:
            return self.adev_c * (tau / tau0) ** self.beta
        else:
            return self.adev_c * (self.tau_c / tau0) ** self.beta
