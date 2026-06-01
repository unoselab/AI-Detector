# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4188_human, name=expireat) ===
def expireat(self, key, timestamp):
        """Set expire timestamp on a key.

        if timeout is float it will be multiplied by 1000
        coerced to int and passed to `pexpireat` method.

        Otherwise raises TypeError if timestamp argument is not int.
        """
        if isinstance(timestamp, float):
            return self.pexpireat(key, int(timestamp * 1000))
        if not isinstance(timestamp, int):
            raise TypeError("timestamp argument must be int, not {!r}"
                            .format(timestamp))
        fut = self.execute(b'EXPIREAT', key, timestamp)
        return wait_convert(fut, bool)

# === BLOCK 2 (label=lm, source_idx=line2102_lm, name=_check_backend) ===
def _check_backend():
    """
    Check :py:class:`djconfig.middleware.DjConfigMiddleware`\
    is registered into ``settings.MIDDLEWARE_CLASSES``
    """
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured

    middleware = getattr(settings, "MIDDLEWARE", None)
    if middleware is None:
        middleware = getattr(settings, "MIDDLEWARE_CLASSES", [])
    if "djconfig.middleware.DjConfigMiddleware" not in middleware:
        raise ImproperlyConfigured(
            "DjConfigMiddleware must be added to settings.MIDDLEWARE or MIDDLEWARE_CLASSES."
        )

# === BLOCK 3 (label=lm, source_idx=line2117_lm, name=vsetup) ===
async def vsetup(self, author):
        """Creates the voice client

        Args:
            author (discord.Member): The user that the voice ui will seek
        """
        if not getattr(author, "voice", None) or not author.voice.channel:
            raise ValueError("Author is not connected to a voice channel.")
        channel = author.voice.channel
        # Reuse existing connection if possible
        vc = getattr(self, "voice_client", None)
        if vc and vc.is_connected():
            if vc.channel != channel:
                await vc.move_to(channel)
        else:
            vc = await channel.connect()
            setattr(self, "voice_client", vc)
        return vc

# === BLOCK 4 (label=human, source_idx=line4618_human, name=get_all_as_list) ===
def get_all_as_list(self, dir='_todo_dir'):
        """
        Returns a list of the the full path to all items currently in the todo directory. The items will be listed in ascending order based on filesystem time.
        This will re-scan the directory on each execution.

        Do not use this to process items, this method should only be used for troubleshooting or something axillary. To process items use get_todo_items() iterator.
        """
        dir = getattr(self,dir)
        list = [x for x in os.listdir(dir) if x.endswith('.json') or x.endswith('.json.gz')]
        full = [os.path.join(dir,x) for x in list]
        full.sort(key=lambda x: os.path.getmtime(x))
        return full

# === BLOCK 5 (label=lm, source_idx=line3126_lm, name=_merge_args) ===
def _merge_args(qCmd, parsed_args, _extra_values, value_specs):
    """Merge arguments from _extra_values into parsed_args.

    If an argument value are provided in both and it is a list,
    the values in _extra_values will be merged into parsed_args.

    @param parsed_args: the parsed args from known options
    @param _extra_values: the other parsed arguments in unknown parts
    @param values_specs: the unparsed unknown parts
    """

# === BLOCK 6 (label=human, source_idx=line5753_human, name=change_hosts) ===
def change_hosts(self, mode, host_family, host, onerror = None):
        """mode is either X.HostInsert or X.HostDelete. host_family is
        one of X.FamilyInternet, X.FamilyDECnet or X.FamilyChaos.

        host is a list of bytes. For the Internet family, it should be the
        four bytes of an IPv4 address."""
        request.ChangeHosts(display = self.display,
                            onerror = onerror,
                            mode = mode,
                            host_family = host_family,
                            host = host)
