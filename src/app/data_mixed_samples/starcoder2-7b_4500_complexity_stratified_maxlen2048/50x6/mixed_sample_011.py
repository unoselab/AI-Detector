# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4141_human, name=remove_all_nexusnve_bindings) ===
def remove_all_nexusnve_bindings():
    """Removes all nexusnve bindings."""

    LOG.debug("remove_all_nexusport_bindings() called")
    session = bc.get_writer_session()
    session.query(nexus_models_v2.NexusNVEBinding).delete()
    session.flush()

# === BLOCK 2 (label=lm, source_idx=line2124_lm, name=highlight) ===
def highlight(self, rect, color="red", seconds=None):
        """ Simulates a transparent rectangle over the specified ``rect`` on the screen.

        Actually takes a screenshot of the region and displays with a
        rectangle border in a borderless window (due to Tkinter limitations)

        If a Tkinter root window has already been created somewhere else,
        uses that instead of creating a new one.
        """
        if self.root is None:
            self.root = Tk()
            self.root.withdraw()
            self.root.overrideredirect(True)
            self.root.wm_attributes("-transparentcolor", "black")
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-alpha", 0)
            self.root.wm_attributes("-disabled", True)
            self.root.wm_attributes("-toolwindow", True)
            self.root.wm_attributes("-topmost", True)
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")
            self.root.wm_attributes("-type", "splash")

# === BLOCK 3 (label=lm, source_idx=line2208_lm, name=get_ordering) ===
def get_ordering(self, *args, **kwargs):
        """Take whatever the expected ordering is and then first order by QuerySet."""
        ordering = self.ordering
        if ordering is None:
            ordering = []
        ordering.extend(self.get_ordering_from_query_set())
        return ordering

# === BLOCK 4 (label=human, source_idx=line4584_human, name=write_summary) ===
def write_summary(page, args, ifos, skyError=None, ipn=False, ipnError=False):

    """
        Write summary of information to markup.page object page
    """
    from pylal import antenna
    from lal.gpstime import gps_to_utc, LIGOTimeGPS

    gps = args.start_time
    grbdate = gps_to_utc(LIGOTimeGPS(gps))\
                                .strftime("%B %d %Y, %H:%M:%S %ZUTC")
    page.h3()
    page.add('Basic information')
    page.h3.close()

    if ipn:
        ra = []
        dec = []
        td1 = []
        td2 = []
        td3 = []
        timedelay = {}
        search_file = '../../../S5IPN_GRB%s_search_180deg.txt' % args.grb_name
        for line in open(search_file):
            ra.append(line.split()[0])
            dec.append(line.split()[1])
        th1 = [ 'GPS', 'Date', 'Error Box (sq.deg.)', 'IFOs' ]
        td1 = [ gps, grbdate, ipnError, ifos ]
        th2 = [ 'RA', 'DEC' ]
        th3 = ['Timedelays (ms)', '', '' ]
        for ra_i,dec_i in zip(ra,dec):
            td_i = [ ra_i, dec_i ]
            td2.append(td_i)
        ifo_list = [ ifos[i*2:(i*2)+2] for i in range(int(len(ifos)/2)) ]
        for j in td2:
            for p in range(0, len(ifo_list)):
                for q in range(0, len(ifo_list)):
                    pairs = [ifo_list[p], ifo_list[q]]
                    ifo_pairs = "".join(pairs)
                    timedelay[ifo_pairs] = antenna.timeDelay(int(gps),
                            float(j[0]), float(j[1]), 'degree', ifo_list[p],
                            ifo_list[q])
                    timedelay[ifo_pairs]="%.4f" % timedelay[ifo_pairs]
            if ifos == 'H1H2L1':
                td3.append(['H1L1: %f' % float(timedelay['H1L1'])])
            if ifos == 'H1H2L1V1':
                td3.append(['H1L1: %f' % float(timedelay['H1L1']),
                            'H1V1: %f' % float(timedelay['H1V1']),
                            'L1V1: %f' % float(timedelay['L1V1'])])
            if ifos == 'L1V1':
                td3.append(['L1V1: %f' % float(timedelay['L1V1'])])
        page = write_table(page, th1, td1)
        page = write_table(page, th2, td2)
        page = write_table(page, th3, td3)

    else:
        ra = args.ra
        dec = args.dec
        if skyError:
            th = [ 'GPS', 'Date', 'RA', 'DEC', 'Sky Error', 'IFOs' ]
            td = [ gps, grbdate, ra, dec, skyError, ifos ]
        else:
            th = [ 'GPS', 'Date', 'RA', 'DEC', 'IFOs' ]
            td = [ gps, grbdate, ra, dec, ifos ]

        page = write_table(page, th, td)

    return page

# === BLOCK 5 (label=lm, source_idx=line3169_lm, name=find_version) ===
def find_version(file_path):
    """
    Scrape version information from specified file path.

    """
    with open(file_path, 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                delim = '"' if '"' in line else "'"
                return line.split(delim)[1]
        else:
            raise RuntimeError("Unable to find version string.")

# === BLOCK 6 (label=human, source_idx=line5981_human, name=draw_on) ===
def draw_on(self, canvas, stem_color, leaf_color, thickness, ages=None):
        """Draw the tree on a canvas.

        Args:
            canvas (object): The canvas, you want to draw the tree on. Supported canvases: svgwrite.Drawing and PIL.Image (You can also add your custom libraries.)
            stem_color (tupel): Color or gradient for the stem of the tree.
            leaf_color (tupel): Color for the leaf (= the color for last iteration).
            thickness (int): The start thickness of the tree.
        """
        if canvas.__module__ in SUPPORTED_CANVAS:
            drawer = SUPPORTED_CANVAS[canvas.__module__]
            drawer(self, canvas, stem_color, leaf_color, thickness, ages).draw()
