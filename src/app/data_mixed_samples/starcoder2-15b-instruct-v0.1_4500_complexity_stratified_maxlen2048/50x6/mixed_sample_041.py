# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3897_human, name=print_status) ===
def print_status(self, repo):
        """Print status
        """
        print("  {0}{1}{2}".format(repo, " " * (19 - len(repo)), self.st))

# === BLOCK 2 (label=human, source_idx=line279_human, name=_get_chromecast_from_host) ===
def _get_chromecast_from_host(host, tries=None, retry_wait=None, timeout=None,
                              blocking=True):
    """Creates a Chromecast object from a zeroconf host."""
    # Build device status from the mDNS info, this information is
    # the primary source and the remaining will be fetched
    # later on.
    ip_address, port, uuid, model_name, friendly_name = host
    _LOGGER.debug("_get_chromecast_from_host %s", host)
    cast_type = CAST_TYPES.get(model_name.lower(),
                               CAST_TYPE_CHROMECAST)
    device = DeviceStatus(
        friendly_name=friendly_name, model_name=model_name,
        manufacturer=None, uuid=uuid, cast_type=cast_type,
    )
    return Chromecast(host=ip_address, port=port, device=device, tries=tries,
                      timeout=timeout, retry_wait=retry_wait,
                      blocking=blocking)

# === BLOCK 3 (label=lm, source_idx=line2279_lm, name=no_positional) ===
def no_positional(allow_self=False):
    """A decorator that doesn't allow for positional arguments.

    :param bool allow_self:
        Whether to allow ``self`` as a positional argument.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if allow_self and len(args) > 1:
                raise TypeError(f"{func.__name__}() does not allow for positional arguments")
            elif not allow_self and len(args) > 0:
                raise TypeError(f"{func.__name__}() does not allow for positional arguments")
            return func(*args, **kwargs)
        return wrapper
    return decorator

# === BLOCK 4 (label=lm, source_idx=line1925_lm, name=_get_whole_subtrees) ===
def _get_whole_subtrees(self):
        """Returns an array of nodes in the tree that have balanced subtrees beneath them,
        moving from left to right.
        """
        result = []
        def dfs(node):
            if not node:
                return 0
            left_height = dfs(node.left)
            right_height = dfs(node.right)
            if abs(left_height - right_height) <= 1:
                result.append(node)
            return max(left_height, right_height) + 1
        dfs(self)
        return result

# === BLOCK 5 (label=human, source_idx=line3343_human, name=get_resource_data) ===
def get_resource_data(ref_key, ref_id, scenario_id, type_id=None, expunge_session=True, **kwargs):
    """
        Get all the resource scenarios for a given resource
        in a given scenario. If type_id is specified, only
        return the resource scenarios for the attributes
        within the type.
    """

    user_id = kwargs.get('user_id')

    resource_data_qry = db.DBSession.query(ResourceScenario).filter(
        ResourceScenario.dataset_id   == Dataset.id,
        ResourceAttr.id == ResourceScenario.resource_attr_id,
        ResourceScenario.scenario_id == scenario_id,
        ResourceAttr.ref_key == ref_key,
        or_(
            ResourceAttr.network_id==ref_id,
            ResourceAttr.node_id==ref_id,
            ResourceAttr.link_id==ref_id,
            ResourceAttr.group_id==ref_id
        )).distinct().\
            options(joinedload('resourceattr')).\
            options(joinedload_all('dataset.metadata')).\
            order_by(ResourceAttr.attr_is_var)

    if type_id is not None:
        attr_ids = []
        rs = db.DBSession.query(TypeAttr).filter(TypeAttr.type_id==type_id).all()
        for r in rs:
            attr_ids.append(r.attr_id)

        resource_data_qry = resource_data_qry.filter(ResourceAttr.attr_id.in_(attr_ids))

    resource_data = resource_data_qry.all()

    for rs in resource_data:

        #TODO: Design a mechanism to read the value of the dataset if it's stored externally

        if rs.dataset.hidden == 'Y':
           try:
                rs.dataset.check_read_permission(user_id)
           except:
               rs.dataset.value      = None

    if expunge_session == True:
        db.DBSession.expunge_all()

    return resource_data

# === BLOCK 6 (label=lm, source_idx=line312_lm, name=initialize) ===
def initialize(config):
        """Initialize method.

        :param config: current application config, injected
        :type config: Config
        """
        config.initialize()
