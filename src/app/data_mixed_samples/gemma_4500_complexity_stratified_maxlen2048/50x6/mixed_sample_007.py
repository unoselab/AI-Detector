# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2047_lm, name=_WriteRow) ===
def _WriteRow(self, output_writer, values):
    """Writes a row of values aligned to the column width.

    Args:
      output_writer (OutputWriter): output writer.
      values (list[object]): values.
    """
    formatted_row = []
    for i, value in enumerate(values):
        width = self._column_widths[i] if i < len(self._column_widths) else 0
        formatted_row.append(f"{str(value):<{width}}")
    output_writer.write(" ".join(formatted_row) + "\n")

# === BLOCK 2 (label=human, source_idx=line3829_human, name=print_new_versions) ===
def print_new_versions(strict=False):
    """Prints new requirement versions."""
    new_updates = []
    same_updates = []
    for req in everything_in(all_reqs):
        new_versions = []
        same_versions = []
        for ver_str in all_versions(req):
            if newer(ver_str_to_tuple(ver_str), min_versions[req], strict=True):
                new_versions.append(ver_str)
            elif not strict and newer(ver_str_to_tuple(ver_str), min_versions[req]):
                same_versions.append(ver_str)
        update_str = req + ": " + ver_tuple_to_str(min_versions[req]) + " -> " + ", ".join(
            new_versions + ["(" + v + ")" for v in same_versions],
        )
        if new_versions:
            new_updates.append(update_str)
        elif same_versions:
            same_updates.append(update_str)
    print("\n".join(new_updates + same_updates))

# === BLOCK 3 (label=human, source_idx=line8252_human, name=ensure_image_is_hex) ===
def ensure_image_is_hex(input_path):
    """Return a path to a hex version of a firmware image.

    If the input file is already in hex format then input_path
    is returned and nothing is done.  If it is not in hex format
    then an SCons action is added to convert it to hex and the
    target output file path is returned.

    A cache is kept so that each file is only converted once.

    Args:
        input_path (str): A path to a firmware image.

    Returns:
        str: The path to a hex version of input_path, this may
            be equal to input_path if it is already in hex format.
    """

    family = utilities.get_family('module_settings.json')
    target = family.platform_independent_target()
    build_dir = target.build_dirs()['build']

    if platform.system() == 'Windows':
        env = Environment(tools=['mingw'], ENV=os.environ)
    else:
        env = Environment(tools=['default'], ENV=os.environ)

    input_path = str(input_path)
    image_name = os.path.basename(input_path)

    root, ext = os.path.splitext(image_name)
    if len(ext) == 0:
        raise BuildError("Unknown file format or missing file extension in ensure_image_is_hex", file_name=input_path)

    file_format = ext[1:]

    if file_format == 'hex':
        return input_path

    if file_format == 'elf':
        new_file = os.path.join(build_dir, root + '.hex')

        if new_file not in CONVERTED_HEX_FILES:
            env.Command(new_file, input_path, action=Action("arm-none-eabi-objcopy -O ihex $SOURCE $TARGET",
                                                            "Creating intel hex file from: $SOURCE"))
            CONVERTED_HEX_FILES.add(new_file)

        return new_file

    raise BuildError("Unknown file format extension in ensure_image_is_hex",
                     file_name=input_path, extension=file_format)

# === BLOCK 4 (label=lm, source_idx=line4797_lm, name=upload) ===
def upload():
    """Uploads to PyPI"""
    import subprocess
    import sys

    try:
        subprocess.run([sys.executable, "-m", "build"], check=True)
        subprocess.run([sys.executable, "-m", "twine", "upload", "dist/*"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Upload failed: {e}")
        sys.exit(1)

# === BLOCK 5 (label=lm, source_idx=line3305_lm, name=bloquear_sat) ===
def bloquear_sat(self):
        """Sobrepõe :meth:`~satcfe.base.FuncoesSAT.bloquear_sat`.

        :return: Uma resposta SAT padrão.
        :rtype: satcfe.resposta.padrao.RespostaSAT
        """
        return super().bloquear_sat()

# === BLOCK 6 (label=human, source_idx=line1828_human, name=read_long_description) ===
def read_long_description(readme_file):
    """ Read package long description from README file """
    try:
        import pypandoc
    except (ImportError, OSError) as e:
        print('No pypandoc or pandoc: %s' % (e,))
        if is_py3:
            fh = open(readme_file, encoding='utf-8')
        else:
            fh = open(readme_file)
        long_description = fh.read()
        fh.close()
        return long_description
    else:
        return pypandoc.convert(readme_file, 'rst')
