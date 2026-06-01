# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1052_human, name=get) ===
def get(self, name, failobj=None):
        """Get a header value.

        Like __getitem__() but return failobj instead of None when the field
        is missing.
        """
        name = name.lower()
        for k, v in self._headers:
            if k.lower() == name:
                return self.policy.header_fetch_parse(k, v)
        return failobj

# === BLOCK 2 (label=lm, source_idx=line8645_lm, name=_read_line) ===
def _read_line(self, f):
        """
        Reads one non empty line (if it's a comment, it skips it).
        """
        while True:
            line = f.readline()
            if not line:
                return None
            if line[0] == '#':
                continue
            return line.strip()

# === BLOCK 3 (label=lm, source_idx=line1737_lm, name=handle) ===
def handle(self, *args, **options):
        """
        Making it happen.
        """
        # Get the user
        user = User.objects.get(username=options['username'])

        # Get the profile
        profile = Profile.objects.get(user=user)

        # Get the user's groups
        groups = Group.objects.filter(user=user)

        # Get the user's groups' permissions
        permissions = Permission.objects.filter(group__in=groups)

        # Get the user's groups' permissions' content types
        content_types = ContentType.objects.filter(
            permission__in=permissions
        )

        # Get the user's groups' permissions' content types' objects
        objects = ObjectPermission.objects.filter(
            content_type__in=content_types
        )

        # Get the user's groups' permissions' content types' objects' users
        users = User.objects.filter(
            objectpermission__in=objects
        )

        # Get the user's groups' permissions' content types' objects' users' profiles
        profiles = Profile.objects.filter(
            user__in=users
        )

        # Get the user's groups' permissions' content types' objects' users' profiles' sites
        sites = Site.objects.filter(
            profile__in=profiles
        )

        # Get the user's groups' permissions' content types' objects' users' profiles' sites' pages
        pages = Page.objects.filter(
            site__in=sites
        )

        # Get the user's groups' permissions' content types' objects' users' profiles' sites' pages' blocks
        blocks = Block.objects.filter(
            page__in=pages
        )

        # Get the user's groups' permissions' content types' objects' users' profiles' sites' pages' blocks' content
        content = Content.objects.filter(
            block__in=blocks
        )

        # Get the user's groups' permissions' content types' objects' users' profiles' sites' pages' blocks' content's
        # images
        images = Image.objects.filter(
            content__in=content
        )

        # Get the user's groups' permissions'

# === BLOCK 4 (label=lm, source_idx=line774_lm, name=register_tc_plugins) ===
def register_tc_plugins(self, plugin_name, plugin_class):
        """
        Loads a plugin as a dictionary and attaches needed parts to correct areas for testing
        parts.

        :param plugin_name: Name of the plugins
        :param plugin_class: PluginBase
        :return: Nothing
        """
        self.plugin_dict[plugin_name] = plugin_class
        self.plugin_dict[plugin_name].tc_config = self.tc_config
        self.plugin_dict[plugin_name].tc_config_dict = self.tc_config_dict
        self.plugin_dict[plugin_name].tc_config_dict_list = self.tc_config_dict_list
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists = self.tc_config_dict_list_of_lists
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists_of_lists = self.tc_config_dict_list_of_lists_of_lists
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists_of_lists_of_lists = self.tc_config_dict_list_of_lists_of_lists_of_lists
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists_of_lists_of_lists_of_lists = self.tc_config_dict_list_of_lists_of_lists_of_lists_of_lists
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists_of_lists_of_lists_of_lists_of_lists = self.tc_config_dict_list_of_lists_of_lists_of_lists_of_lists_of_lists
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists_of_lists_of_lists_of_lists_of_lists_of_lists = self.tc_config_dict_list_of_lists_of_lists_of_lists_of_lists_of_lists_of_lists
        self.plugin_dict[plugin_name].tc_config_dict_list_of_lists_of_lists_of_lists_of_lists_of_lists_of_lists_of_lists = self.tc_config_dict_list_of_lists_of_lists_of_lists_of_lists_of_lists_of

# === BLOCK 5 (label=human, source_idx=line324_human, name=update_auto_scroll_mode) ===
def update_auto_scroll_mode(self):
        """ Register or un-register signals for follow mode """
        if self._enables['CONSOLE_FOLLOW_LOGGING']:
            if self._auto_scroll_handler_id is None:
                self._auto_scroll_handler_id = self.text_view.connect("size-allocate", self._auto_scroll)
        else:
            if self._auto_scroll_handler_id is not None:
                self.text_view.disconnect(self._auto_scroll_handler_id)
                self._auto_scroll_handler_id = None

# === BLOCK 6 (label=human, source_idx=line7215_human, name=commit) ===
def commit(self) -> ResponseCommit:
        """Return the current encode state value to tendermint"""
        hash = struct.pack('>Q', self.txCount)
        return ResponseCommit(data=hash)
