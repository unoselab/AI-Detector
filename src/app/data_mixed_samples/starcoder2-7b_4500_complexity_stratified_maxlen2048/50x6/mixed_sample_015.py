# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2447_lm, name=get_phi_comps_from_recfile) ===
def get_phi_comps_from_recfile(recfile):
    """read the phi components from a record file by iteration

    Parameters
    ----------
    recfile : str
        pest record file name

    Returns
    -------
    iters : dict
        nested dictionary of iteration number, {group,contribution}

    """
    iters = {}
    with open(recfile, 'r') as f:
        for line in f:
            if line.startswith('  phi'):
                iters[int(line.split()[1])] = {}
                iters[int(line.split()[1])]['group'] = line.split()[2]
                iters[int(line.split()[1])]['contribution'] = float(line.split()[3])
    return iters

# === BLOCK 2 (label=human, source_idx=line1974_human, name=handle) ===
def handle(self, *args, **options):
        """Handle the command"""
        # get the command arguments
        self.verbosity = int(options.get('verbosity', 1))
        force = options['force']
        imports = self.get_imports(options['import'])

        # Import the CurrencyHandler and get an instance
        handler = self.get_handler(options)

        self.log(logging.INFO, "Getting currency data from %s", handler.endpoint)
        timestamp = datetime.now().isoformat()

        # find available codes
        if imports:
            allcodes = set(handler.get_allcurrencycodes())
            reqcodes = set(imports)
            available = reqcodes & allcodes
            unavailable = reqcodes - allcodes
        else:
            self.log(logging.WARNING, "Importing all. Some currencies may be out-of-date (MTL) or spurious (XPD)")
            available = handler.get_allcurrencycodes()
            unavailable = None

        for code in available:
            obj, created = Currency._default_manager.get_or_create(code=code)
            name = handler.get_currencyname(code)
            description = "%r (%s)" % (name, code)
            if created or force:
                kwargs = {}
                if created:
                    kwargs['is_active'] = False
                    msg = "Creating %s"
                    obj.info.update( {'Created': timestamp} )
                else:
                    msg = "Updating %s"
                obj.info.update( {'Modified': timestamp} )

                if name:
                    kwargs['name'] = name

                symbol = handler.get_currencysymbol(code)
                if symbol:
                    kwargs['symbol'] = symbol

                try:
                    obj.info.update(handler.get_info(code))
                except AttributeError:
                    pass

                kwargs['info'] = obj.info

                self.log(logging.INFO, msg, description)
                Currency._default_manager.filter(pk=obj.pk).update(**kwargs)
            else:
                msg = "Skipping %s"
                self.log(logging.INFO, msg, description)

        if unavailable:
            raise ImproperlyConfigured("Currencies %s not found in %s source" % (unavailable, handler.name))

# === BLOCK 3 (label=lm, source_idx=line4773_lm, name=client_ident) ===
def client_ident(self):
        """
        Return the client identifier as included in many command replies.
        """
        return self.client_ident

# === BLOCK 4 (label=human, source_idx=line3390_human, name=handleError) ===
def handleError(self, test, err, capt=None):
        """
        After a test error, we want to record testcase run information.
        "Error" also encompasses any states other than Pass or Fail, so we
        check for those first.
        """
        if err[0] == errors.BlockedTest:
            self.__insert_test_result(constants.State.BLOCKED, test, err)
            self.error_handled = True
            raise SkipTest(err[1])
            return True

        elif err[0] == errors.DeprecatedTest:
            self.__insert_test_result(constants.State.DEPRECATED, test, err)
            self.error_handled = True
            raise SkipTest(err[1])
            return True

        elif err[0] == errors.SkipTest:
            self.__insert_test_result(constants.State.SKIP, test, err)
            self.error_handled = True
            raise SkipTest(err[1])
            return True

# === BLOCK 5 (label=human, source_idx=line4486_human, name=save) ===
def save(self, name, content, *args, **kwargs):
        """
        Save the image.

        The image will be resized down using a ``ThumbnailField`` if
        ``resize_source`` (a dictionary of thumbnail options) is provided by
        the field.
        """
        options = getattr(self.field, 'resize_source', None)
        if options:
            if 'quality' not in options:
                options['quality'] = self.thumbnail_quality
            content = Thumbnailer(content, name).generate_thumbnail(options)
            # If the generated extension differs from the original, use it
            # instead.
            orig_name, ext = os.path.splitext(name)
            generated_ext = os.path.splitext(content.name)[1]
            if generated_ext.lower() != ext.lower():
                name = orig_name + generated_ext
        super(ThumbnailerImageFieldFile, self).save(name, content, *args,
                                                    **kwargs)

# === BLOCK 6 (label=lm, source_idx=line1015_lm, name=_invoke_submit) ===
def _invoke_submit(self, iterobj, is_dict, is_itmcoll, mres, global_kw):
        """
        Internal function to invoke the actual submit_single function
        :param iterobj: The raw object returned as the next item of the iterator
        :param is_dict: True if iterator is a dictionary
        :param is_itmcoll: True if the iterator contains Item objects
        :param mres: The multi result object
        :param global_kw: The global settings
        :return: The return value of :meth:`submit_single`
        """
        if is_dict:
            # If the iterator is a dictionary, we need to convert it to a list of
            # dictionaries.
            iterobj = [iterobj]
        elif is_itmcoll:
            # If the iterator is an ItemCollection, we need to convert it to a list
            # of dictionaries.
            iterobj = iterobj.items()
        return self.submit_single(iterobj, mres, global_kw)
