# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line984_lm, name=parse_xml) ===
def parse_xml(self, xml):
        """
            :param key_xml: lxml.etree.Element representing a single VocabularyCodeSet
        """
        self.name = xml.findtext('Name')
        self.description = xml.findtext('Description')
        self.codes = []
        for code_xml in xml.findall('VocabularyCode'):
            code = VocabularyCode()
            code.parse_xml(code_xml)
            self.codes.append(code)

# === BLOCK 2 (label=human, source_idx=line216_human, name=delegate) ===
def delegate(attribute_name, method_names):
    """
    Decorator factory to delegate methods to an attribute.

    Decorate a class to map every method in `method_names` to the attribute `attribute_name`.

    """
    call_attribute_method = partial(_call_delegated_method, attribute_name)

    def decorate(class_):
        for method in method_names:
            setattr(class_, method, partialmethod(call_attribute_method, method))

        return class_
    return decorate

# === BLOCK 3 (label=lm, source_idx=line1848_lm, name=unprovision_vdp_overlay_networks) ===
def unprovision_vdp_overlay_networks(self, net_uuid, lvid, vdp_vlan, oui):
        """Unprovisions a overlay type network configured using VDP.

        :param net_uuid: the uuid of the network associated with this vlan.
        :lvid: Local VLAN ID
        :vdp_vlan: VDP VLAN ID
        :oui: OUI Parameters
        """
        if not net_uuid:
            raise ValueError("net_uuid is required")
        if not lvid:
            raise ValueError("lvid is required")
        if not vdp_vlan:
            raise ValueError("vdp_vlan is required")
        if not oui:
            raise ValueError("oui is required")
        if not isinstance(net_uuid, str):
            raise TypeError("net_uuid must be a string")
        if not isinstance(lvid, int):
            raise TypeError("lvid must be an integer")
        if not isinstance(vdp_vlan, int):
            raise TypeError("vdp_vlan must be an integer")
        if not isinstance(oui, str):
            raise TypeError("oui must be a string")
        if not self.validate_net_uuid(net_uuid):
            raise ValueError("Invalid net_uuid")
        if not self.validate_lvid(lvid):
            raise ValueError("Invalid lvid")
        if not self.validate_vdp_vlan(vdp_vlan):
            raise ValueError("Invalid vdp_vlan")
        if not self.validate_oui(oui):
            raise ValueError("Invalid oui")
        self.unprovision_vdp_overlay_networks(net_uuid, lvid, vdp_vlan, oui)

# === BLOCK 4 (label=lm, source_idx=line754_lm, name=_parse_description) ===
def _parse_description(self, node):
        # type: (ElementTree.Element) -> EndpointDescription
        """
        Parse an endpoint description node

        :param node: The endpoint description node
        :return: The parsed EndpointDescription bean
        :raise KeyError: Attribute missing
        :raise ValueError: Invalid description
        """
        attributes = {
            "name": node.get("name"),
            "address": node.get("address"),
            "port": int(node.get("port")),
            "protocol": node.get("protocol"),
            "priority": int(node.get("priority")),
            "weight": int(node.get("weight")),
        }
        required_attributes = ["name", "address", "port", "protocol", "priority", "weight"]
        missing_attributes = [attr for attr in required_attributes if attributes[attr] is None]
        if missing_attributes:
            raise KeyError("Missing attributes: {}".format(", ".join(missing_attributes)))
        if attributes["protocol"] not in ["http", "https"]:
            raise ValueError("Invalid protocol: {}".format(attributes["protocol"]))
        return EndpointDescription(**attributes)

# === BLOCK 5 (label=human, source_idx=line1046_human, name=timex_starts) ===
def timex_starts(self):
        """The list of start positions of ``timexes`` layer elements."""
        if not self.is_tagged(TIMEXES):
            self.tag_timexes()
        return self.starts(TIMEXES)

# === BLOCK 6 (label=human, source_idx=line883_human, name=decode_keys) ===
def decode_keys(store, encoding='utf-8'):
    """
    If a dictionary has keys that are bytes decode them to a str.

    Parameters
    ---------
    store : dict
      Dictionary with data

    Returns
    ---------
    result : dict
      Values are untouched but keys that were bytes
      are converted to ASCII strings.

    Example
    -----------
    In [1]: d
    Out[1]: {1020: 'nah', b'hi': 'stuff'}

    In [2]: trimesh.util.decode_keys(d)
    Out[2]: {1020: 'nah', 'hi': 'stuff'}
    """
    keys = store.keys()
    for key in keys:
        if hasattr(key, 'decode'):
            decoded = key.decode(encoding)
            if key != decoded:
                store[key.decode(encoding)] = store[key]
                store.pop(key)
    return store
