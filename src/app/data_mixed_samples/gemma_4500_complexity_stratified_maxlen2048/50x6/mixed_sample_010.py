# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4115_lm, name=setFontItalic) ===
def setFontItalic(self, state):
        """
        Toggles whehter or not the text is currently italic.

        :param      state | <bool>
        """
        self.italic = state

# === BLOCK 2 (label=lm, source_idx=line5156_lm, name=files_delete) ===
def files_delete(self, *, id: str, **kwargs) -> SlackResponse:
        """Deletes a file.

        Args:
            id (str): The file id. e.g. 'F1234467890'
        """
        return self.api_call("files.delete", id=id, **kwargs)

# === BLOCK 3 (label=lm, source_idx=line3742_lm, name=sort_dicoms) ===
def sort_dicoms(dicoms):
    """
    Sort the dicoms based om the image possition patient

    :param dicoms: list of dicoms
    """
    dicoms.sort(key=lambda x: float(x.ImagePositionPatient[2]))

# === BLOCK 4 (label=human, source_idx=line8761_human, name=main) ===
def main(command_class=None, args=None):
    """Run the command line interface with the given :class:`Command`.

    If no command class is specified the user will be able to select a specific
    command through the first command line argument. If the ``args`` are
    provided, these should be a list of strings that will be used instead of
    ``sys.argv[1:]``. This is mostly useful for testing.
    """

    # Set up logging for the command line interface
    if 'PSAMM_DEBUG' in os.environ:
        level = getattr(logging, os.environ['PSAMM_DEBUG'].upper(), None)
        if level is not None:
            logging.basicConfig(level=level)
    else:
        logging.basicConfig(level=logging.INFO)
        base_logger = logging.getLogger('psamm')
        if len(base_logger.handlers) == 0:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(u'%(levelname)s: %(message)s'))
            base_logger.addHandler(handler)
            base_logger.propagate = False

    title = 'Metabolic modeling tools'
    if command_class is not None:
        title, _, _ = command_class.__doc__.partition('\n\n')

    parser = argparse.ArgumentParser(description=title)
    parser.add_argument('--model', metavar='file', default='.',
                        help='Model definition')
    parser.add_argument(
        '-V', '--version', action='version',
        version='%(prog)s ' + package_version)

    if command_class is not None:
        # Command explicitly given, only allow that command
        command_class.init_parser(parser)
        parser.set_defaults(command=command_class)
    else:
        # Discover all available commands
        commands = {}
        for entry in pkg_resources.iter_entry_points('psamm.commands'):
            canonical = entry.name.lower()
            if canonical not in commands:
                command_class = entry.load()
                commands[canonical] = command_class
            else:
                logger.warning('Command {} was found more than once!'.format(
                    canonical))

        # Create parsers for subcommands
        subparsers = parser.add_subparsers(title='Commands', metavar='command')
        for name, command_class in sorted(iteritems(commands)):
            title, _, _ = command_class.__doc__.partition('\n\n')
            subparser = subparsers.add_parser(
                name, help=title.rstrip('.'),
                formatter_class=argparse.RawDescriptionHelpFormatter,
                description=_trim(command_class.__doc__))
            subparser.set_defaults(command=command_class)
            command_class.init_parser(subparser)

    parsed_args = parser.parse_args(args)

    # Load model definition
    model = native.ModelReader.reader_from_path(
        parsed_args.model).create_model()

    # Instantiate command with model and run
    command = parsed_args.command(model, parsed_args)
    try:
        command.run()
    except CommandError as e:
        parser.error(text_type(e))

# === BLOCK 5 (label=human, source_idx=line1296_human, name=get_subsites) ===
def get_subsites(self):
        """ Returns a list of subsites defined for this site

        :rtype: list[Site]
        """
        url = self.build_url(
            self._endpoints.get('get_subsites').format(id=self.object_id))

        response = self.con.get(url)
        if not response:
            return []

        data = response.json()

        # Everything received from cloud must be passed as self._cloud_data_key
        return [self.__class__(parent=self, **{self._cloud_data_key: site}) for
                site in data.get('value', [])]

# === BLOCK 6 (label=human, source_idx=line916_human, name=_close) ===
def _close(self):
        """Close the tough connection.

        You can always close a tough connection with this method
        and it will not complain if you close it more than once.

        """
        if not self._closed:
            try:
                self._con.close()
            except Exception:
                pass
            self._transaction = False
            self._closed = True
