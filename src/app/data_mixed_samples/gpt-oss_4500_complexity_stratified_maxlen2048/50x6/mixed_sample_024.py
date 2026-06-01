# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6599_lm, name=get_service_id_list) ===
def get_service_id_list() -> List[tuple]:
    """Return list of Services."""
    return []

# === BLOCK 2 (label=human, source_idx=line855_human, name=expand_expression) ===
def expand_expression(self, pattern, hosts, services, hostgroups, servicegroups, running=False):
        # pylint: disable=too-many-locals
        """Expand a host or service expression into a dependency node tree
        using (host|service)group membership, regex, or labels as item selector.

        :param pattern: pattern to parse
        :type pattern: str
        :param hosts: hosts list, used to find a specific host
        :type hosts: alignak.objects.host.Host
        :param services: services list, used to find a specific service
        :type services: alignak.objects.service.Service
        :param running: rules are evaluated at run time and parsing. True means runtime
        :type running: bool
        :return: root node of parsed tree
        :rtype: alignak.dependencynode.DependencyNode
        """
        error = None
        node = DependencyNode()
        node.operand = '&'
        elts = [e.strip() for e in pattern.split(',')]
        # If host_name is empty, use the host_name the business rule is bound to
        if not elts[0]:
            elts[0] = self.bound_item.host_name
        filters = []
        # Looks for hosts/services using appropriate filters
        try:
            all_items = {
                "hosts": hosts,
                "hostgroups": hostgroups,
                "servicegroups": servicegroups
            }
            if len(elts) > 1:
                # We got a service expression
                host_expr, service_expr = elts
                filters.extend(self.get_srv_host_filters(host_expr))
                filters.extend(self.get_srv_service_filters(service_expr))
                items = services.find_by_filter(filters, all_items)
            else:
                # We got a host expression
                host_expr = elts[0]
                filters.extend(self.get_host_filters(host_expr))
                items = hosts.find_by_filter(filters, all_items)
        except re.error as regerr:
            error = "Business rule uses invalid regex %s: %s" % (pattern, regerr)
        else:
            if not items:
                error = "Business rule got an empty result for pattern %s" % pattern

        # Checks if we got result
        if error:
            if running is False:
                node.configuration_errors.append(error)
            else:
                # As business rules are re-evaluated at run time on
                # each scheduling loop, if the rule becomes invalid
                # because of a badly written macro modulation, it
                # should be notified upper for the error to be
                # displayed in the check output.
                raise Exception(error)
            return node

        # Creates dependency node subtree
        # here we have Alignak SchedulingItem object (Host/Service)
        for item in items:
            # Creates a host/service node
            son = DependencyNode()
            son.operand = item.__class__.my_type
            son.sons.append(item.uuid)  # Only store the uuid, not the full object.
            # Appends it to wrapping node
            node.sons.append(son)

        node.switch_zeros_of_values()
        return node

# === BLOCK 3 (label=human, source_idx=line1463_human, name=__getRefererUrl) ===
def __getRefererUrl(self, url=None):
        """
        gets the referer url for the token handler
        """
        if url is None:
            url = "http://www.arcgis.com/sharing/rest/portals/self"
        params = {
            "f" : "json",
            "token" : self.token
        }
        val = self._get(url=url, param_dict=params,
                           proxy_url=self._proxy_url,
                           proxy_port=self._proxy_port)
        self._referer_url = "arcgis.com"#"http://%s.%s" % (val['urlKey'], val['customBaseUrl'])
        self._token = None
        return self._referer_url

# === BLOCK 4 (label=lm, source_idx=line6777_lm, name=publish) ===
async def publish(self, endpoint: str, payload: str):
        """
        Publish to an endpoint.
        :param str endpoint: Key by which the endpoint is recognised.
                         Subscribers will use this key to listen to events
        :param str payload: Payload to publish with the event
        :return: A boolean indicating if the publish was successful
        """
        import asyncio
        subs = getattr(self, "_subscribers", {}).get(endpoint, [])
        if not subs:
            return False
        results = await asyncio.gather(
            *(sub(payload) for sub in subs), return_exceptions=True
        )
        return all(not isinstance(r, Exception) for r in results)

# === BLOCK 5 (label=lm, source_idx=line6550_lm, name=_read_opt_ra) ===
def _read_opt_ra(self, code, *, desc):
        """Read HOPOPT Router Alert option.

        Structure of HOPOPT Router Alert option [RFC 2711]:
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
            |0 0 0|0 0 1 0 1|0 0 0 0 0 0 1 0|        Value (2 octets)       |
            +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

            Octets      Bits        Name                    Description
              0           0     hopopt.ra.type          Option Type
              0           0     hopopt.ra.type.value    Option Number
              0           0     hopopt.ra.type.action   Action (00)
              0           2     hopopt.ra.type.change   Change Flag (0)
              1           8     hopopt.opt.length       Length of Option Data
              2          16     hopopt.ra.value         Value

        """

# === BLOCK 6 (label=human, source_idx=line4956_human, name=get_setting) ===
def get_setting(key, *default):
    """Return specific search setting from Django conf."""
    if default:
        return get_settings().get(key, default[0])
    else:
        return get_settings()[key]
