# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line68_lm, name=get_peers_in_established) ===
def get_peers_in_established(self):
        """Returns list of peers in established state."""
        return [peer for peer in self.peers if peer.state == "ESTABLISHED"]

# === BLOCK 2 (label=lm, source_idx=line348_lm, name=do_bc) ===
def do_bc(self, arg):
        """
        [~process] bc <address> - clear a code breakpoint
        [~thread] bc <address> - clear a hardware breakpoint
        [~process] bc <address-address> - clear a memory breakpoint
        [~process] bc <address> <size> - clear a memory breakpoint
        """
        args = arg.split()
        if len(args) == 1:
            if args[0].startswith('0x'):
                return self.clear_code_breakpoint(args[0])
            else:
                return self.clear_hardware_breakpoint(args[0])
        elif len(args) == 2:
            return self.clear_memory_breakpoint(args[0], args[1])

# === BLOCK 3 (label=human, source_idx=line640_human, name=exception_to_github) ===
def exception_to_github(github_obj_to_comment, summary=""):
    """If any exception comes, log them in the given Github obj.
    """
    context = ExceptionContext()
    try:
        yield context
    except Exception:  # pylint: disable=broad-except
        if summary:
            summary = ": ({})".format(summary)
        error_type = "an unknown error"
        try:
            raise
        except CalledProcessError as err:
            error_type = "a Subprocess error"
            content = "Command: {}\n".format(err.cmd)
            content += "Finished with return code {}\n".format(err.returncode)
            if err.output:
                content += "and output:\n```shell\n{}\n```".format(err.output)
            else:
                content += "and no output"
        except Exception:  # pylint: disable=broad-except
            content = "```python\n{}\n```".format(traceback.format_exc())
        response = "<details><summary>Encountered {}{}</summary><p>\n\n".format(
            error_type,
            summary
        )
        response += content
        response += "\n\n</p></details>"
        context.comment = create_comment(github_obj_to_comment, response)

# === BLOCK 4 (label=lm, source_idx=line2803_lm, name=remove_bad_sequence) ===
def remove_bad_sequence(codon_list, bad_seq, bad_seqs):
    """
    Make a silent mutation to the given codon list to remove the first instance 
    of the given bad sequence found in the gene sequence.  If the bad sequence 
    isn't found, nothing happens and the function returns false.  Otherwise the 
    function returns true.  You can use these return values to easily write a 
    loop totally purges the bad sequence from the codon list.  Both the 
    specific bad sequence in question and the list of all bad sequences are 
    expected to be regular expressions.
    """
    codon_str = ''.join(codon_list)
    match = re.search(bad_seq, codon_str)
    if match:
        codon_list[:] = re.sub(bad_seq, '', codon_str, 1)
        return True
    else:
        return False

# === BLOCK 5 (label=human, source_idx=line2506_human, name=get_tesseract_version) ===
def get_tesseract_version():
    """Try to extract version from tesseract otherwise default min version."""
    config = {'libraries': ['tesseract', 'lept']}
    try:
        p = subprocess.Popen(['tesseract', '-v'], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout_version, version = p.communicate()
        version = _read_string(version).strip()
        if version == '':
            version = _read_string(stdout_version).strip()
        version_match = re.search(r'^tesseract ((?:\d+\.)+\d+).*', version, re.M)
        if version_match:
            version = version_match.group(1)
        else:
            _LOGGER.warn('Failed to extract tesseract version number from: {}'.format(version))
            version = _TESSERACT_MIN_VERSION
    except OSError as e:
        _LOGGER.warn('Failed to extract tesseract version from executable: {}'.format(e))
        version = _TESSERACT_MIN_VERSION
    _LOGGER.info("Supporting tesseract v{}".format(version))
    version = version_to_int(version)
    config['cython_compile_time_env'] = {'TESSERACT_VERSION': version}
    _LOGGER.info("Building with configs: {}".format(config))
    return config

# === BLOCK 6 (label=human, source_idx=line621_human, name=get_document_unit) ===
def get_document_unit(self):
        """Get the unit of the SVG surface.

        If the surface passed as an argument is not a SVG surface, the function
        sets the error status to ``STATUS_SURFACE_TYPE_MISMATCH`` and
        returns :ref:`SVG_UNIT_USER`.

        :return: The SVG unit of the SVG surface.

        *New in cairo 1.16.*

        *New in cairocffi 0.9.*

        """
        unit = cairo.cairo_svg_surface_get_document_unit(self._pointer)
        self._check_status()
        return unit
