# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4069_human, name=Process) ===
def Process(self, parser_mediator, plist_name, top_level, **kwargs):
    """Check if it is a valid Apple account plist file name.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      plist_name (str): name of the plist.
      top_level (dict[str, object]): plist top-level key.
    """
    if not plist_name.startswith(self.PLIST_PATH):
      raise errors.WrongPlistPlugin(self.NAME, plist_name)
    super(AppleAccountPlugin, self).Process(
        parser_mediator, plist_name=self.PLIST_PATH, top_level=top_level)

# === BLOCK 2 (label=human, source_idx=line4240_human, name=login) ===
def login(self):
        """Logon to the server."""

        if self.args.snmp_force:
            # Force SNMP instead of Glances server
            self.client_mode = 'snmp'
        else:
            # First of all, trying to connect to a Glances server
            if not self._login_glances():
                return False

        # Try SNMP mode
        if self.client_mode == 'snmp':
            if not self._login_snmp():
                return False

        # Load limits from the configuration file
        # Each client can choose its owns limits
        logger.debug("Load limits from the client configuration file")
        self.stats.load_limits(self.config)

        # Init screen
        if self.quiet:
            # In quiet mode, nothing is displayed
            logger.info("Quiet mode is ON: Nothing will be displayed")
        else:
            self.screen = GlancesCursesClient(config=self.config, args=self.args)

        # Return True: OK
        return True

# === BLOCK 3 (label=human, source_idx=line317_human, name=from_json) ===
def from_json(cls, data, result=None):
        """
        Create new Relation element from JSON data

        :param data: Element data from JSON
        :type data: Dict
        :param result: The result this element belongs to
        :type result: overpy.Result
        :return: New instance of Relation
        :rtype: overpy.Relation
        :raises overpy.exception.ElementDataWrongType: If type value of the passed JSON data does not match.
        """
        if data.get("type") != cls._type_value:
            raise exception.ElementDataWrongType(
                type_expected=cls._type_value,
                type_provided=data.get("type")
            )

        tags = data.get("tags", {})

        rel_id = data.get("id")
        (center_lat, center_lon) = cls.get_center_from_json(data=data)

        members = []

        supported_members = [RelationNode, RelationWay, RelationRelation]
        for member in data.get("members", []):
            type_value = member.get("type")
            for member_cls in supported_members:
                if member_cls._type_value == type_value:
                    members.append(
                        member_cls.from_json(
                            member,
                            result=result
                        )
                    )

        attributes = {}
        ignore = ["id", "members", "tags", "type"]
        for n, v in data.items():
            if n in ignore:
                continue
            attributes[n] = v

        return cls(
            rel_id=rel_id,
            attributes=attributes,
            center_lat=center_lat,
            center_lon=center_lon,
            members=members,
            tags=tags,
            result=result
        )

# === BLOCK 4 (label=lm, source_idx=line772_lm, name=_create_body) ===
def _create_body(self, name, description=None, volume=None, force=False):
        """
        Used to create the dict required to create a new snapshot
        """
        body = {'snapshot': {'name': name}}
        if description is not None:
            body['snapshot']['description'] = description
        if volume is not None:
            body['snapshot']['volume_id'] = volume
        if force:
            body['snapshot']['force'] = True
        return body

# === BLOCK 5 (label=lm, source_idx=line4612_lm, name=search_indices) ===
def search_indices(values, source):
    """
    Given a set of values returns the indices of each of those values
    in the source array.
    """
    idx_map = {v: i for i, v in enumerate(source)}
    return [idx_map.get(v, -1) for v in values]

# === BLOCK 6 (label=lm, source_idx=line5550_lm, name=_index) ===
def _index(self, value):
        """Rearrange a tensor according to the convolution mode

        Input is assumed to be in (channels, bins, time) format.
        """
