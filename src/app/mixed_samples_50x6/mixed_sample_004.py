# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1671_lm, name=add_to_favorites) ===
def add_to_favorites(current):
    """
    Favorite a message

    .. code-block:: python

        #  request:
            {
            'view':'_zops_add_to_favorites,
            'key': key,
            }

        #  response:
            {
            'status': 'Created',
            'code': 201
            'favorite_key': key
            }

    """
    key = current.data.get('key')
    if not key:
        return {'status': 'Bad Request', 'code': 400}
    favorite = Favorite(key=key)
    favorite.save()
    return {'status': 'Created', 'code': 201, 'favorite_key': key}

# === BLOCK 2 (label=human, source_idx=line942_human, name=get_label) ===
def get_label(self, prop, value):
        """
        Format label
        If value is missing, label will be colored red
        """
        if value is None:
            return '{}: <FONT color="red">{}</FONT>'.format(prop, "not set")
        else:
            return "{}:{}".format(prop, value)

# === BLOCK 3 (label=lm, source_idx=line797_lm, name=load) ===
def load(self, config_path=None):
        """ Load and parse the configuration file using pyyaml

        :param config_path: An optional file path, file handle, or byte string
            for the configuration file.

        """
        def load(self, config_path=None):
            if config_path is None:
                config_path = self.DEFAULT_CONFIG_PATH
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config

# === BLOCK 4 (label=human, source_idx=line1671_human, name=add_to_favorites) ===
def add_to_favorites(current):
    """
    Favorite a message

    .. code-block:: python

        #  request:
            {
            'view':'_zops_add_to_favorites,
            'key': key,
            }

        #  response:
            {
            'status': 'Created',
            'code': 201
            'favorite_key': key
            }

    """
    msg = Message.objects.get(current.input['key'])
    current.output = {'status': 'Created', 'code': 201}
    fav, new = Favorite.objects.get_or_create(user_id=current.user_id, message=msg)
    current.output['favorite_key'] = fav.key

# === BLOCK 5 (label=human, source_idx=line304_human, name=_reset_internal) ===
def _reset_internal(self):
        """
        Sets initial pose of arm and grippers.
        """
        super()._reset_internal()
        self.sim.data.qpos[self._ref_joint_pos_indexes] = self.mujoco_robot.init_qpos

        if self.has_gripper:
            self.sim.data.qpos[
                self._ref_joint_gripper_actuator_indexes
            ] = self.gripper.init_qpos

# === BLOCK 6 (label=lm, source_idx=line28_lm, name=meter) ===
def meter(self, key, **dims):
        """Adds meter with dimensions to the registry"""
        self._metrics[key] = dims
