# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3735_human, name=get_provider) ===
def get_provider(self, module_member: str) -> Optional['ProviderResource']:
        """
        Fetches the provider for the given module member, if this resource has been provided a specific
        provider for the given module member.

        Returns None if no provider was provided.

        :param str module_member: The requested module member.
        :return: The :class:`ProviderResource` associated with the given module member, or None if one does not exist.
        :rtype: Optional[ProviderResource]
        """
        components = module_member.split(":")
        if len(components) != 3:
            return None

        [pkg, _, _] = components
        return self._providers.get(pkg)

# === BLOCK 2 (label=lm, source_idx=line5574_lm, name=unshare_database) ===
def unshare_database(self, username):
        """
        Removes all sharing with the named user for the current remote database.
        This will remove the entry for the user from the security document.
        To modify permissions, use the
        :func:`~cloudant.database.CloudantDatabase.share_database` method
        instead.

        :param str username: Cloudant user to unshare the database from.

        :returns: Unshare database status in JSON format
        """
        url = f"{self._url}/_security"
        response = self._request("DELETE", url, params={"users": username})
        return response.json() if response.content else response

# === BLOCK 3 (label=lm, source_idx=line3357_lm, name=get_midi_data) ===
def get_midi_data(self):
        """Collect and return the raw, binary MIDI data from the tracks."""
        midi_data = bytearray()
        for track in self.tracks:
            midi_data.extend(track.raw_data)
        return bytes(midi_data)

# === BLOCK 4 (label=human, source_idx=line7269_human, name=_to_dict) ===
def _to_dict(self):
        """Return a json dictionary representing this model."""
        _dict = {}
        if hasattr(self, 'concepts') and self.concepts is not None:
            _dict['concepts'] = self.concepts._to_dict()
        if hasattr(self, 'emotion') and self.emotion is not None:
            _dict['emotion'] = self.emotion._to_dict()
        if hasattr(self, 'entities') and self.entities is not None:
            _dict['entities'] = self.entities._to_dict()
        if hasattr(self, 'keywords') and self.keywords is not None:
            _dict['keywords'] = self.keywords._to_dict()
        if hasattr(self, 'metadata') and self.metadata is not None:
            _dict['metadata'] = self.metadata._to_dict()
        if hasattr(self, 'relations') and self.relations is not None:
            _dict['relations'] = self.relations._to_dict()
        if hasattr(self, 'semantic_roles') and self.semantic_roles is not None:
            _dict['semantic_roles'] = self.semantic_roles._to_dict()
        if hasattr(self, 'sentiment') and self.sentiment is not None:
            _dict['sentiment'] = self.sentiment._to_dict()
        if hasattr(self, 'categories') and self.categories is not None:
            _dict['categories'] = self.categories._to_dict()
        if hasattr(self, 'syntax') and self.syntax is not None:
            _dict['syntax'] = self.syntax._to_dict()
        return _dict

# === BLOCK 5 (label=human, source_idx=line635_human, name=resolve) ===
def resolve(self, jref, parser=None):
        """ JSON reference resolver

        :param str jref: a JSON Reference, refer to http://tools.ietf.org/html/draft-pbryan-zyp-json-ref-03 for details.
        :param parser: the parser corresponding to target object.
        :type parser: pyswagger.base.Context
        :return: the referenced object, wrapped by weakref.ProxyType
        :rtype: weakref.ProxyType
        :raises ValueError: if path is not valid
        """

        logger.info('resolving: [{0}]'.format(jref))

        if jref == None or len(jref) == 0:
            raise ValueError('Empty Path is not allowed')

        obj = None
        url, jp = utils.jr_split(jref)

        # check cacahed object against json reference by
        # comparing url first, and find those object prefixed with
        # the JSON pointer.
        o = self.__objs.get(url, None)
        if o:
            if isinstance(o, BaseObj):
                obj = o.resolve(utils.jp_split(jp)[1:])
            elif isinstance(o, dict):
                for k, v in six.iteritems(o):
                    if jp.startswith(k):
                        obj = v.resolve(utils.jp_split(jp[len(k):])[1:])
                        break
            else:
                raise Exception('Unknown Cached Object: {0}'.format(str(type(o))))

        # this object is not found in cache
        if obj == None:
            if url:
                obj, _ = self.load_obj(jref, parser=parser)
                if obj:
                    obj = self.prepare_obj(obj, jref)
            else:
                # a local reference, 'jref' is just a json-pointer
                if not jp.startswith('#'):
                    raise ValueError('Invalid Path, root element should be \'#\', but [{0}]'.format(jref))

                obj = self.root.resolve(utils.jp_split(jp)[1:]) # heading element is #, mapping to self.root

        if obj == None:
            raise ValueError('Unable to resolve path, [{0}]'.format(jref))

        if isinstance(obj, (six.string_types, six.integer_types, list, dict)):
            return obj
        return weakref.proxy(obj)

# === BLOCK 6 (label=lm, source_idx=line6630_lm, name=get_season_player_stats) ===
def get_season_player_stats(self, season_key, player_key):
        """
        Calling Season Player Stats API.

        Arg:
           season_key: key of the season
           player_key: key of the player
        Return:
           json data
        """
        endpoint = f"seasons/{season_key}/players/{player_key}"
        response = self.session.get(endpoint)
        response.raise_for_status()
        return response.json()
