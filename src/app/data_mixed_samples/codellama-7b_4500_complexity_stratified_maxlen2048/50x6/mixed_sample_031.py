# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8093_lm, name=update_project) ===
def update_project(self, project_id, name=None, description=None,
                       reference_language=None):
        """
        Updates project settings (name, description, reference language)
        If optional parameters are not sent, their respective fields are not updated.
        """
        params = {}
        if name is not None:
            params['name'] = name
        if description is not None:
            params['description'] = description
        if reference_language is not None:
            params['reference_language'] = reference_language

        return self.request('projects/%s' % project_id, method='PUT', data=params)

# === BLOCK 2 (label=human, source_idx=line774_human, name=register_tc_plugins) ===
def register_tc_plugins(self, plugin_name, plugin_class):
        """
        Loads a plugin as a dictionary and attaches needed parts to correct areas for testing
        parts.

        :param plugin_name: Name of the plugins
        :param plugin_class: PluginBase
        :return: Nothing
        """
        if plugin_name in self.registered_plugins:
            raise PluginException("Plugin {} already registered! Duplicate "
                                  "plugins?".format(plugin_name))
        self.logger.debug("Registering plugin %s", plugin_name)
        plugin_class.init(bench=self.bench)
        if plugin_class.get_bench_api() is not None:
            register_func = self.plugin_types[PluginTypes.BENCH]
            register_func(plugin_name, plugin_class)
        if plugin_class.get_parsers() is not None:
            register_func = self.plugin_types[PluginTypes.PARSER]
            register_func(plugin_name, plugin_class)
        if plugin_class.get_external_services() is not None:
            register_func = self.plugin_types[PluginTypes.EXTSERVICE]
            register_func(plugin_name, plugin_class)

        self.registered_plugins.append(plugin_name)

# === BLOCK 3 (label=human, source_idx=line7865_human, name=_validate_schema) ===
def _validate_schema(self):
        """
        Validates provider schema for syntax issues. Raises :class:`~notifiers.exceptions.SchemaError` if relevant

        :raises: :class:`~notifiers.exceptions.SchemaError`
        """
        try:
            log.debug("validating provider schema")
            self.validator.check_schema(self.schema)
        except jsonschema.SchemaError as e:
            raise SchemaError(
                schema_error=e.message, provider=self.name, data=self.schema
            )

# === BLOCK 4 (label=human, source_idx=line1387_human, name=data_find_all) ===
def data_find_all(data, path, dyn_cls=False):
    """Find and return all element-as-tuples in tuple ``data`` using simplified
    XPath ``path``.
    """
    path_parts = path.split("/")
    try:
        sub_elms = tuple(
            el
            for el in data
            if isinstance(el, (tuple, list)) and el[0] == path_parts[0]
        )
    except IndexError:
        return None
    if len(path_parts) > 1:
        ret = []
        for sub_elm in sub_elms:
            for x in data_find_all(sub_elm, "/".join(path_parts[1:])):
                ret.append(x)
        ret = tuple(ret)
    else:
        ret = sub_elms
    if ret and dyn_cls:
        cls = generate_element_class(ret[0])
        return tuple(cls(data=tuple_) for tuple_ in ret)
    return ret

# === BLOCK 5 (label=lm, source_idx=line1944_lm, name=get_cases) ===
def get_cases(self, skip_ws=False):
        """Returns a list of 2-tuples (condition, value).

        If an ELSE exists condition is None.
        """
        cases = []
        while True:
            if skip_ws:
                self.skip_ws()
            if self.current_char == '}':
                break
            if self.current_char == '|':
                self.next_char()
                if self.current_char == '|':
                    self.next_char()
                    if self.current_char == '}':
                        break
                    else:
                        raise SyntaxError('Expected "}"')
                else:
                    raise SyntaxError('Expected "|"')
            condition = self.get_condition()
            if self.current_char == '|':
                self.next_char()
                if self.current_char == '|':
                    self.next_char()
                    if self.current_char == '}':
                        break
                    else:
                        raise SyntaxError('Expected "}"')
                else:
                    raise SyntaxError('Expected "|"')
            if self.current_char == '=':
                self.next_char()
                value = self.get_value()
                cases.append((condition, value))
            else:
                raise SyntaxError('Expected "="')
        return cases

# === BLOCK 6 (label=lm, source_idx=line5900_lm, name=from_string) ===
def from_string(s):
        """Deserializes a token from a string like one returned by
        `to_string()`."""
        return cls(s)
