# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line56_lm, name=static) ===
def static(self, *args, **kwargs):
        """Define the routes to static files the API should expose"""

# === BLOCK 2 (label=human, source_idx=line2298_human, name=monitored_resource_descriptor_path) ===
def monitored_resource_descriptor_path(cls, project, monitored_resource_descriptor):
        """Return a fully-qualified monitored_resource_descriptor string."""
        return google.api_core.path_template.expand(
            "projects/{project}/monitoredResourceDescriptors/{monitored_resource_descriptor}",
            project=project,
            monitored_resource_descriptor=monitored_resource_descriptor,
        )

# === BLOCK 3 (label=human, source_idx=line853_human, name=res_to_url) ===
def res_to_url(resource, action):
    """Convert resource.action to (url, HTTP_METHOD)"""
    i = action.find("_")
    if i < 0:
        url = "/" + resource
        httpmethod = action
    else:
        url = "/%s/%s" % (resource, action[i + 1:])
        httpmethod = action[:i]
    return url, httpmethod.upper()

# === BLOCK 4 (label=lm, source_idx=line453_lm, name=is_all_field_none) ===
def is_all_field_none(self):
        """
        :rtype: bool
        """
        return all(value is None for value in vars(self).values())

# === BLOCK 5 (label=lm, source_idx=line6300_lm, name=_lookup_unconflicted_symbol) ===
def _lookup_unconflicted_symbol(self, symbol):
        """
        Attempt to find a unique asset whose symbol is the given string.

        If multiple assets have held the given symbol, return a 0.

        If no asset has held the given symbol, return a  NaN.
        """

# === BLOCK 6 (label=human, source_idx=line5720_human, name=chain_callback) ===
def chain_callback(self, iocb):
        """Callback when this iocb completes."""
        if _debug: IOChainMixIn._debug("chain_callback %r", iocb)

        # if we're not chained, there's no notification to do
        if not self.ioChain:
            return

        # refer to the chained iocb
        iocb = self.ioChain

        try:
            if _debug: IOChainMixIn._debug("    - decoding")

            # let the derived class transform the data
            self.decode()

            if _debug: IOChainMixIn._debug("    - decode complete")
        except:
            # extract the error and abort
            err = sys.exc_info()[1]
            if _debug: IOChainMixIn._exception("    - decoding exception: %r", err)

            iocb.ioState = ABORTED
            iocb.ioError = err

        # break the references
        self.ioChain = None
        iocb.ioController = None

        # notify the client
        iocb.trigger()
