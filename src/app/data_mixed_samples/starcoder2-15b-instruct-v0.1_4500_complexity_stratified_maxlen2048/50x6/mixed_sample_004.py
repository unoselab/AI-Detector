# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2171_lm, name=print_meter_record) ===
def print_meter_record(file_path, rows=5):
    """ Output readings for specified number of rows to console """
    with open(file_path, 'r') as file:
        for _ in range(rows):
            print(file.readline())

# === BLOCK 2 (label=lm, source_idx=line2501_lm, name=dinf_downslope_direction) ===
def dinf_downslope_direction(a):
        """Get the downslope directions of an dinf direction value
        Args:
            a: Dinf value

        Returns:
            downslope directions
        """
        downslope_directions = []
        if a & 1:
            downslope_directions.append((0, 1))
        if a & 2:
            downslope_directions.append((1, 1))
        if a & 4:
            downslope_directions.append((1, 0))
        if a & 8:
            downslope_directions.append((1, -1))
        if a & 16:
            downslope_directions.append((0, -1))
        if a & 32:
            downslope_directions.append((-1, -1))
        if a & 64:
            downslope_directions.append((-1, 0))
        if a & 128:
            downslope_directions.append((-1, 1))

        return downslope_directions

# === BLOCK 3 (label=human, source_idx=line3284_human, name=displayable) ===
def displayable(obj):
    """
    Predicate that returns whether the object is displayable or not
    (i.e whether the object obeys the nesting hierarchy
    """
    if isinstance(obj, Overlay) and any(isinstance(o, (HoloMap, GridSpace))
                                        for o in obj):
        return False
    if isinstance(obj, HoloMap):
        return not (obj.type in [Layout, GridSpace, NdLayout, DynamicMap])
    if isinstance(obj, (GridSpace, Layout, NdLayout)):
        for el in obj.values():
            if not displayable(el):
                return False
        return True
    return True

# === BLOCK 4 (label=lm, source_idx=line1878_lm, name=_add_observation) ===
def _add_observation(self, x_to_add, y_to_add):
        """Add observation to window, updating means/variance efficiently."""
        n = len(self.x)
        self.x_mean_old = self.x_mean
        self.y_mean_old = self.y_mean
        self.x_mean = (self.x_mean * n + x_to_add) / (n + 1)
        self.y_mean = (self.y_mean * n + y_to_add) / (n + 1)
        self.x_var = (n * self.x_var + (x_to_add - self.x_mean_old) ** 2) / (n + 1)
        self.y_var = (n * self.y_var + (y_to_add - self.y_mean_old) ** 2) / (n + 1)
        self.x.append(x_to_add)
        self.y.append(y_to_add)

# === BLOCK 5 (label=human, source_idx=line4734_human, name=pre_social_login) ===
def pre_social_login(self, request, sociallogin):
        """Update user based on token information."""

        user = sociallogin.user
        # If the user hasn't been saved yet, it will be updated
        # later on in the sign-up flow.
        if not user.pk:
            return

        data = sociallogin.account.extra_data
        oidc = sociallogin.account.provider == 'helsinki_oidc'
        update_user(user, data, oidc)

# === BLOCK 6 (label=human, source_idx=line2884_human, name=create_default_config) ===
def create_default_config(schema):
    """Create a configuration dictionary from a schema dictionary.
    The schema defines the valid configuration keys and their default
    values.  Each element of ``schema`` should be a tuple/list
    containing (default value,docstring,type) or a dict containing a
    nested schema."""

    o = {}
    for key, item in schema.items():

        if isinstance(item, dict):
            o[key] = create_default_config(item)
        elif isinstance(item, tuple):

            value, comment, item_type = item

            if isinstance(item_type, tuple):
                item_type = item_type[0]

            if value is None and (item_type == list or item_type == dict):
                value = item_type()

            if key in o:
                raise KeyError('Duplicate key in schema.')

            o[key] = value
        else:
            raise TypeError('Unrecognized type for schema dict element: %s %s' %
                            (key, type(item)))

    return o
