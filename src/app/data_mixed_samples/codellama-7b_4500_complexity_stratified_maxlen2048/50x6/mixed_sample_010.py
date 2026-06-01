# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4114_lm, name=tempo_account_get_customer_by_id) ===
def tempo_account_get_customer_by_id(self, customer_id=1):
        """
        Get Account Attribute whose key or name contain a specific substring. Attribute can be a Category or Customer.
        :param customer_id: id of Customer record
        :return: Customer info
        """
        url = self.url + 'accounts/customers/' + str(customer_id)
        response = self.client.get(url)
        return response

# === BLOCK 2 (label=lm, source_idx=line4911_lm, name=validate_busy) ===
def validate_busy(func, *args, **kwargs):
    """
    A decorator that raises an exception if the specified target is busy.

    Expects the target ID to be either the 'target_id' param in kwargs,
    or the first positional parameter.

    Raises a TargetBusyException if the target does not exist.
    """
    target_id = kwargs.get('target_id', args[0])
    if target_id is None:
        raise ValueError('target_id must be specified')

    target = Target.get(target_id)
    if target is None:
        raise TargetBusyException('Target %s does not exist' % target_id)

    if target.busy:
        raise TargetBusyException('Target %s is busy' % target_id)

    return func(*args, **kwargs)

# === BLOCK 3 (label=lm, source_idx=line3749_lm, name=_insert_or_replace_entity) ===
def _insert_or_replace_entity(entity):
    """
    Constructs an insert or replace entity request.
    """
    return {
        'InsertOrReplaceEntity': {
            'Entity': entity
        }
    }

# === BLOCK 4 (label=human, source_idx=line8909_human, name=BuildNanny) ===
def BuildNanny(self):
    """Use VS2010 to build the windows Nanny service."""
    # When running under cygwin, the following environment variables are not set
    # (since they contain invalid chars). Visual Studio requires these or it
    # will fail.
    os.environ["ProgramFiles(x86)"] = r"C:\Program Files (x86)"
    self.nanny_dir = os.path.join(self.build_dir, "grr", "client",
                                  "grr_response_client", "nanny")
    nanny_src_dir = config.CONFIG.Get(
        "ClientBuilder.nanny_source_dir", context=self.context)
    logging.info("Copying Nanny build files from %s to %s", nanny_src_dir,
                 self.nanny_dir)

    shutil.copytree(
        config.CONFIG.Get(
            "ClientBuilder.nanny_source_dir", context=self.context),
        self.nanny_dir)

    build_type = config.CONFIG.Get(
        "ClientBuilder.build_type", context=self.context)

    vs_arch = config.CONFIG.Get(
        "ClientBuilder.vs_arch", default=None, context=self.context)

    # We have to set up the Visual Studio environment first and then call
    # msbuild.
    env_script = config.CONFIG.Get(
        "ClientBuilder.vs_env_script", default=None, context=self.context)

    if vs_arch is None or env_script is None or not os.path.exists(env_script):
      # Visual Studio is not installed. We just use pre-built binaries in that
      # case.
      logging.warning(
          "Visual Studio does not appear to be installed, "
          "Falling back to prebuilt GRRNanny binaries."
          "If you want to build it you must have VS 2012 installed.")

      binaries_dir = config.CONFIG.Get(
          "ClientBuilder.nanny_prebuilt_binaries", context=self.context)

      shutil.copy(
          os.path.join(binaries_dir, "GRRNanny_%s.exe" % vs_arch),
          os.path.join(self.output_dir, "GRRservice.exe"))

    else:
      # Lets build the nanny with the VS env script.
      subprocess.check_call(
          "cmd /c \"\"%s\" && msbuild /p:Configuration=%s;Platform=%s\"" %
          (env_script, build_type, vs_arch),
          cwd=self.nanny_dir)

      # The templates always contain the same filenames - the repack step might
      # rename them later.
      shutil.copy(
          os.path.join(self.nanny_dir, vs_arch, build_type, "GRRNanny.exe"),
          os.path.join(self.output_dir, "GRRservice.exe"))

# === BLOCK 5 (label=human, source_idx=line1327_human, name=replace_command) ===
def replace_command(command, broken, matched):
    """Helper for *_no_command rules."""
    new_cmds = get_close_matches(broken, matched, cutoff=0.1)
    return [replace_argument(command.script, broken, new_cmd.strip())
            for new_cmd in new_cmds]

# === BLOCK 6 (label=human, source_idx=line981_human, name=parse_bookmark_data) ===
def parse_bookmark_data (data):
    """Return iterator for bookmarks of the form (url, name, line number).
    Bookmarks are not sorted.
    """
    name = None
    lineno = 0
    for line in data.splitlines():
        lineno += 1
        line = line.strip()
        if line.startswith("NAME="):
            name = line[5:]
        elif line.startswith("URL="):
            url = line[4:]
            if url and name is not None:
                yield (url, name, lineno)
        else:
            name = None
