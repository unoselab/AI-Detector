# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4040_human, name=message) ===
def message(self, message_ids):
        """
        This will return information about the referenced message. If the id
        is given as a comma-delimited list, one record will be returned for
        each id. In this way you can query a set of messages in a single
        request. Note that you can only give up to 25 ids per request--more
        than that will return an error.
        """
        if isinstance(message_ids, list):
            message_ids = ','.join([int(id) for id in message_ids])
        path = '/msg/get/%s' % message_ids
        return self._request(path)

# === BLOCK 2 (label=lm, source_idx=line1792_lm, name=_format_envvars) ===
def _format_envvars(ctx):
    """Format all envvars for a `click.Command`."""
    result = []
    for param in ctx.command.params:
        if param.envvar:
            result.append(f"{param.envvar}={param.default}")
    return "\n".join(result)

# === BLOCK 3 (label=lm, source_idx=line2590_lm, name=get_power_state) ===
def get_power_state(self, userid):
        """Get power status of a z/VM instance."""
        instance = self.instances.get(userid)
        if instance:
            return instance.power_state
        else:
            return None

# === BLOCK 4 (label=lm, source_idx=line2399_lm, name=get_form) ===
def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        return super().get_form(request, obj, **kwargs)

# === BLOCK 5 (label=human, source_idx=line3728_human, name=_initialize) ===
def _initialize(self, boto_session, sagemaker_client, sagemaker_runtime_client):
        """Initialize this Local SageMaker Session."""

        self.boto_session = boto_session or boto3.Session()
        self._region_name = self.boto_session.region_name

        if self._region_name is None:
            raise ValueError('Must setup local AWS configuration with a region supported by SageMaker.')

        self.sagemaker_client = LocalSagemakerClient(self)
        self.sagemaker_runtime_client = LocalSagemakerRuntimeClient(self.config)
        self.local_mode = True

# === BLOCK 6 (label=human, source_idx=line3650_human, name=get_file_port) ===
def get_file_port(self):
        """Returns ports list can be used by File

        File ports includes ethernet ports and link aggregation ports.
        """
        eths = self.get_ethernet_port(bond=False)
        las = self.get_link_aggregation()
        return eths + las
