# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3087_human, name=build_conda_packages) ===
def build_conda_packages(self):
        """
        Run the Linux build and use converter to build OSX
        """
        ## check if update is necessary
        #if self.nversion == self.pversion:
        #    raise SystemExit("Exited: new version == existing version")

        ## tmp dir
        bldir = "./tmp-bld"
        if not os.path.exists(bldir):
            os.makedirs(bldir)

        ## iterate over builds
        for pybuild in ["2.7", "3"]:

            ## build and upload Linux to anaconda.org
            build = api.build(
                "conda-recipe/{}".format(self.package),
                 python=pybuild)

            ## upload Linux build
            if not self.deploy:
                cmd = ["anaconda", "upload", build[0], "--label", "test", "--force"]
            else:
                cmd = ["anaconda", "upload", build[0]]
            err = subprocess.Popen(cmd).communicate()

            ## build OSX copies 
            api.convert(build[0], output_dir=bldir, platforms=["osx-64"])
            osxdir = os.path.join(bldir, "osx-64", os.path.basename(build[0]))
            if not self.deploy:
                cmd = ["anaconda", "upload", osxdir, "--label", "test", "--force"]
            else:
                cmd = ["anaconda", "upload", osxdir]
            err = subprocess.Popen(cmd).communicate()

        ## cleanup tmpdir
        shutil.rmtree(bldir)

# === BLOCK 2 (label=lm, source_idx=line1886_lm, name=_get_countdown_for_next_slice) ===
def _get_countdown_for_next_slice(self, spec):
    """Get countdown for next slice's task.

    When user sets processing rate, we set countdown to delay task execution.

    Args:
      spec: model.MapreduceSpec

    Returns:
      countdown in int.
    """
    if spec.rate:
      return 1.0 / spec.rate
    else:
      return None

# === BLOCK 3 (label=human, source_idx=line5039_human, name=add_include) ===
def add_include(self, name, included_scope, module):
        """Register an imported module into this scope.

        Raises ``ThriftCompilerError`` if the name has already been used.
        """
        # The compiler already ensures this. If we still get here with a
        # conflict, that's a bug.
        assert name not in self.included_scopes

        self.included_scopes[name] = included_scope
        self.add_surface(name, module)

# === BLOCK 4 (label=human, source_idx=line4414_human, name=stepback) ===
def stepback(self, append=False):
        """
        Stepbacks/reverses the buffer.
        Optional arguments:
        * append=False - If True, appends the data onto the buffer;
                        else, it just steps the index back.
        """
        if append:
            data = self._buffer[self._index - 1]
            self._buffer.append(data)
        else:
            self._index -= 1

# === BLOCK 5 (label=lm, source_idx=line2765_lm, name=_parse_udf_vol_descs) ===
def _parse_udf_vol_descs(self, extent, length, descs):
        # type: (int, int, PyCdlib._UDFDescriptors) -> None
        """
        An internal method to parse a set of UDF Volume Descriptors.

        Parameters:
         extent - The extent at which to start parsing.
         length - The number of bytes to read from the incoming ISO.
         descs - The _UDFDescriptors object to store parsed objects into.
        Returns:
         Nothing.
        """
        # type: (...) -> None
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-instance-attributes
        # pylint: disable=too-many-public-methods
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-function-args
        # pylint: disable=too-many-function-locals
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-instance-attributes
        # pylint: disable=too-many-public-methods
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint: disable=too-many-boolean-expressions
        # pylint: disable=too-many-lines
        # pylint

# === BLOCK 6 (label=lm, source_idx=line1938_lm, name=isfile_notempty) ===
def isfile_notempty(inputfile: str) -> bool:
        """Check if the input filename with path is a file and is not empty."""
        if not os.path.isfile(inputfile):
            raise FileNotFoundError(f"File {inputfile} does not exist.")
        if os.stat(inputfile).st_size == 0:
            raise FileNotFoundError(f"File {inputfile} is empty.")
        return True
