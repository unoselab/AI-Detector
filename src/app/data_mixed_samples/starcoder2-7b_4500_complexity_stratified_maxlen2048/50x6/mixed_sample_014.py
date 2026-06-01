# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6842_lm, name=start) ===
def start(name, call=None):
    """
    Start a node.

    CLI Example:

    .. code-block:: bash

        salt-cloud -a start mymachine
    """
    if call == "function":
        return _start(name)
    else:
        return _start(name, call)

# === BLOCK 2 (label=human, source_idx=line3047_human, name=discover_slave) ===
async def discover_slave(self, service, timeout, **kwargs):
        """Perform Slave discovery for specified service."""
        # TODO: use kwargs to change how slaves are picked up
        #   (eg: round-robin, priority, random, etc)
        idle_timeout = timeout
        pools = self._pools[:]
        for sentinel in pools:
            try:
                with async_timeout(timeout, loop=self._loop):
                    address = await self._get_slave_address(
                        sentinel, service)  # add **kwargs
                pool = self._slaves[service]
                with async_timeout(timeout, loop=self._loop), \
                        contextlib.ExitStack() as stack:
                    conn = await pool._create_new_connection(address)
                    stack.callback(conn.close)
                    await self._verify_service_role(conn, 'slave')
                    stack.pop_all()
                return conn
            except asyncio.CancelledError:
                raise
            except asyncio.TimeoutError:
                continue
            except DiscoverError:
                await asyncio.sleep(idle_timeout, loop=self._loop)
                continue
            except RedisError as err:
                raise SlaveReplyError("Service {} error".format(service), err)
            except Exception:
                await asyncio.sleep(idle_timeout, loop=self._loop)
                continue
        raise SlaveNotFoundError("No slave found for {}".format(service))

# === BLOCK 3 (label=lm, source_idx=line1117_lm, name=_discretize_check) ===
def _discretize_check(self, table, att, col):
        """
        Replaces the value with an appropriate interval symbol, if available.
        """
        if att in self.discretized_atts:
            if self.discretized_atts[att] == 'equal_width':
                table[col] = table[col].apply(lambda x: self._get_interval_symbol(x, self.discretized_atts[att], self.discretized_atts[att+'_bins']))
            elif self.discretized_atts[att] == 'equal_freq':
                table[col] = table[col].apply(lambda x: self._get_interval_symbol(x, self.discretized_atts[att], self.discretized_atts[att+'_bins']))
            elif self.discretized_atts[att] == 'custom':
                table[col] = table[col].apply(lambda x: self._get_interval_symbol(x, self.discretized_atts[att], self.discretized_atts[att+'_bins']))
            else:
                raise ValueError('Discretization method not supported.')

# === BLOCK 4 (label=human, source_idx=line5361_human, name=_read_cellular_components) ===
def _read_cellular_components():
    """Read cellular components from a resource file."""
    # Here we load a patch file in addition to the current cellular components
    # file to make sure we don't error with InvalidLocationError with some
    # deprecated cellular location names
    this_dir = os.path.dirname(os.path.abspath(__file__))
    cc_file = os.path.join(this_dir, os.pardir, 'resources',
                           'cellular_components.tsv')
    cc_patch_file = os.path.join(this_dir, os.pardir, 'resources',
                                 'cellular_components_patch.tsv')
    cellular_components = {}
    cellular_components_reverse = {}
    with open(cc_file, 'rt') as fh:
        lines = list(fh.readlines())
    # We add the patch to the end of the lines list
    with open(cc_patch_file, 'rt') as fh:
        lines += list(fh.readlines())
    for lin in lines[1:]:
        terms = lin.strip().split('\t')
        cellular_components[terms[1]] = terms[0]
        # If the GO -> name mapping doesn't exist yet, we add a mapping
        # but if it already exists (i.e. the try doesn't error) then
        # we don't add the GO -> name mapping. This ensures that names from
        # the patch file aren't mapped to in the reverse list.
        try:
            cellular_components_reverse[terms[0]]
        except KeyError:
            cellular_components_reverse[terms[0]] = terms[1]
    return cellular_components, cellular_components_reverse

# === BLOCK 5 (label=lm, source_idx=line6525_lm, name=d_from_format) ===
def d_from_format(self, attr):
        """ Find out the local name of an attribute

        :param attr: An Attribute dictionary
        :return: The local attribute name or "" if no mapping could be made
        """
        return self.attr_map.get(attr.get("name"), "")

# === BLOCK 6 (label=human, source_idx=line5195_human, name=lock) ===
def lock(self, key, timeout=0, sleep=0):
        """Emulate lock."""
        return MockRedisLock(self, key, timeout, sleep)
