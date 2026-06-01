# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3986_human, name=createDAM) ===
def createDAM(dam_name, config):
        """ create DAM """
        if 'yahoo' == dam_name:
            from analyzerdam.yahooDAM import YahooDAM
            dam=YahooDAM()
        elif 'google' == dam_name:
            from analyzerdam.google import GoogleDAM
            dam=GoogleDAM()
        elif 'excel' == dam_name:
            from analyzerdam.excelDAM import ExcelDAM
            dam=ExcelDAM()
        elif 'hbase' == dam_name:
            from analyzerdam.hbaseDAM import HBaseDAM
            dam=HBaseDAM()
        elif 'sql' == dam_name:
            from analyzerdam.sqlDAM import SqlDAM
            dam=SqlDAM(config)
        elif 'cex' == dam_name:
            from analyzerdam.cex import CexDAM
            dam=CexDAM(config)
        else:
            raise UfException(Errors.INVALID_DAM_TYPE,
                              "DAM type is invalid %s" % dam_name)

        return dam

# === BLOCK 2 (label=human, source_idx=line4184_human, name=_get_stack_frame) ===
def _get_stack_frame(stacklevel):
    """
    utility functions to get a stackframe, skipping internal frames.
    """
    stacklevel = stacklevel + 1
    if stacklevel <= 1 or _is_internal_frame(sys._getframe(1)):
        # If frame is too small to care or if the warning originated in
        # internal code, then do not try to hide any frames.
        frame = sys._getframe(stacklevel)
    else:
        frame = sys._getframe(1)
        # Look for one frame less since the above line starts us off.
        for x in range(stacklevel-1):
            frame = _next_external_frame(frame)
            if frame is None:
                raise ValueError
    return frame

# === BLOCK 3 (label=human, source_idx=line3211_human, name=new_connection) ===
def new_connection (self):
        """Connect to clamd for stream scanning.

        @return: tuple (connected socket, host)
        """
        if self.get('LocalSocket'):
            host = 'localhost'
            sock = self.create_local_socket()
        elif self.get('TCPSocket'):
            host = self.get('TCPAddr', 'localhost')
            sock = self.create_tcp_socket(host)
        else:
            raise ClamavError(_("one of TCPSocket or LocalSocket must be enabled"))
        return sock, host

# === BLOCK 4 (label=lm, source_idx=line782_lm, name=clear_extensions) ===
def clear_extensions(self, group=None):
        """Clear all previously registered extensions."""
        self.extensions = {}
        self.extension_groups = {}
        self.extension_groups[group] = []

# === BLOCK 5 (label=lm, source_idx=line4565_lm, name=_fix_quantities) ===
def _fix_quantities(tree):
    """
    Stupidly simple function to fix any Items/Quantity disparities inside a
    DistributionConfig block before use. Since AWS only accepts JSON-encodable
    data types, this implementation is "good enough" for our purposes.
    """
    for item in tree.get('Items', []):
        if 'Quantity' in item:
            item['Quantity'] = int(item['Quantity'])
        if 'Quantity' in item.get('Attributes', {}):
            item['Attributes']['Quantity'] = int(item['Attributes']['Quantity'])
    return tree

# === BLOCK 6 (label=lm, source_idx=line56_lm, name=_extract_spi_args) ===
def _extract_spi_args(self, **kwargs):
        """
        Given a set of keyword arguments, splits it into those relevant to SPI
        implementations and all the rest. SPI arguments are augmented with
        defaults and converted into the pin format (from the port/device
        format) if necessary.

        Returns a tuple of ``(spi_args, other_args)``.
        """
        spi_args = {}
        other_args = {}
        for key, value in kwargs.items():
            if key in self._spi_args:
                spi_args[key] = value
            else:
                other_args[key] = value

        # Convert port/device to pin if necessary
        if self._spi_args.get('port', None) is not None:
            spi_args['port'] = self._spi_args['port'].pin
        if self._spi_args.get('device', None) is not None:
            spi_args['device'] = self._spi_args['device'].pin

        return (spi_args, other_args)
