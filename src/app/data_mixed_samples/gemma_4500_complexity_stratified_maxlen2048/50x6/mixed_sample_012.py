# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5154_human, name=make_tstore_conn) ===
def make_tstore_conn(params, **kwargs):
    """ Returns a triplestore connection

        args:
            attr_name: The name the connection will be assigned in the
                config manager
            params: The paramaters of the connection

        kwargs:
            log_level: logging level to use
    """
    log.setLevel(params.get('log_level', __LOG_LEVEL__))
    log.debug("\n%s", params)
    params.update(kwargs)
    try:
        vendor = RdfwConnections['triplestore'][params.get('vendor')]
    except KeyError:
        vendor = RdfwConnections['triplestore']['blazegraph']
    conn = vendor(**params)
    return conn

# === BLOCK 2 (label=human, source_idx=line4601_human, name=port_profile_qos_profile_qos_flowcontrol_pfc_pfc_cos) ===
def port_profile_qos_profile_qos_flowcontrol_pfc_pfc_cos(self, **kwargs):
        """Auto Generated Code
        """
        config = ET.Element("config")
        port_profile = ET.SubElement(config, "port-profile", xmlns="urn:brocade.com:mgmt:brocade-port-profile")
        name_key = ET.SubElement(port_profile, "name")
        name_key.text = kwargs.pop('name')
        qos_profile = ET.SubElement(port_profile, "qos-profile")
        qos = ET.SubElement(qos_profile, "qos")
        flowcontrol = ET.SubElement(qos, "flowcontrol")
        pfc = ET.SubElement(flowcontrol, "pfc")
        pfc_cos = ET.SubElement(pfc, "pfc-cos")
        pfc_cos.text = kwargs.pop('pfc_cos')

        callback = kwargs.pop('callback', self._callback)
        return callback(config)

# === BLOCK 3 (label=lm, source_idx=line6038_lm, name=on_service_modify) ===
def on_service_modify(self, svc_ref, old_properties):
        """
        Called when a service has been modified in the framework

        :param svc_ref: A service reference
        :param old_properties: Previous properties values
        :return: A tuple (added, (service, reference)) if the dependency has
                 been changed, else None
        """
        new_properties = svc_ref.get_properties()
        if new_properties != old_properties:
            return (True, (svc_ref, svc_ref))
        return None

# === BLOCK 4 (label=lm, source_idx=line2371_lm, name=absent) ===
def absent(name, ip):  # pylint: disable=C0103
    """
    Ensure that the named host is absent

    name
        The host to remove

    ip
        The ip addr(s) of the host to remove
    """
    import subprocess
    for address in (ip if isinstance(ip, list) else [ip]):
        try:
            subprocess.run(['sudo', 'sed', '-i', f'/^{name}.*${address}/d', '/etc/hosts'], check=True)
        except subprocess.CalledProcessError:
            pass

# === BLOCK 5 (label=human, source_idx=line6672_human, name=_handle_sigusr2) ===
def _handle_sigusr2(self, signum: int, frame: Any) -> None:
        """Drop current task."""
        logger.warning("Catched SIGUSR2")
        if self.current_task:
            logger.warning("Dropping current task...")
            raise Discard

# === BLOCK 6 (label=lm, source_idx=line3268_lm, name=find_conflicts_between_sub_selection_sets) ===
def find_conflicts_between_sub_selection_sets(
    context: ValidationContext,
    cached_fields_and_fragment_names: Dict,
    compared_fragment_pairs: "PairSet",
    are_mutually_exclusive: bool,
    parent_type1: Optional[GraphQLNamedType],
    selection_set1: SelectionSetNode,
    parent_type2: Optional[GraphQLNamedType],
    selection_set2: SelectionSetNode,
) -> List[Conflict]:
    """Find conflicts between sub selection sets.

    Find all conflicts found between two selection sets, including those found via
    spreading in fragments. Called when determining if conflicts exist between the
    sub-fields of two overlapping fields.
    """
    conflicts = []
    for selection1 in selection_set1.selections:
        for selection2 in selection_set2.selections:
            if are_mutually_exclusive:
                if selection1 == selection2:
                    continue

            conflict = find_conflict(
                context,
                cached_fields_and_fragment_names,
                compared_fragment_pairs,
                parent_type1,
                selection1,
                parent_type2,
                selection2,
            )
            if conflict:
                conflicts.append(conflict)
    return conflicts
