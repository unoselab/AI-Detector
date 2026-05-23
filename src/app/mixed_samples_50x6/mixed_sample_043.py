# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1057_lm, name=one_vertical_total_stress) ===
def one_vertical_total_stress(self, z_c):
        """
        Determine the vertical total stress at a single depth z_c.

        :param z_c: depth from surface
        """
        return self.one_vertical_effective_stress(z_c) - self.one_vertical_pore_pressure(z_c)

# === BLOCK 2 (label=human, source_idx=line2634_human, name=location) ===
def location(name, uri, default):
    """Create new location."""
    from .models import Location
    location = Location(name=name, uri=uri, default=default)
    db.session.add(location)
    db.session.commit()
    click.secho(str(location), fg='green')

# === BLOCK 3 (label=lm, source_idx=line1392_lm, name=get_vmpolicy_macaddr_output_instance_id) ===
def get_vmpolicy_macaddr_output_instance_id(self, **kwargs):
        """Auto Generated Code
        """
        return self.instance_id

# === BLOCK 4 (label=human, source_idx=line1068_human, name=to_struct_file) ===
def to_struct_file(self, f):
        """ write a PEST-style structure file

        Parameters
        ----------
        f : (str or file handle)
            file to write the GeoStruct information to

        """
        if isinstance(f, str):
            f = open(f,'w')
        f.write("STRUCTURE {0}\n".format(self.name))
        f.write("  NUGGET {0}\n".format(self.nugget))
        f.write("  NUMVARIOGRAM {0}\n".format(len(self.variograms)))
        for v in self.variograms:
            f.write("  VARIOGRAM {0} {1}\n".format(v.name,v.contribution))
        f.write("  TRANSFORM {0}\n".format(self.transform))
        f.write("END STRUCTURE\n\n")
        for v in self.variograms:
            v.to_struct_file(f)

# === BLOCK 5 (label=human, source_idx=line1371_human, name=startAlertListener) ===
def startAlertListener(self, callback=None):
        """ Creates a websocket connection to the Plex Server to optionally recieve
            notifications. These often include messages from Plex about media scans
            as well as updates to currently running Transcode Sessions.

            NOTE: You need websocket-client installed in order to use this feature.
            >> pip install websocket-client

            Parameters:
                callback (func): Callback function to call on recieved messages.

            raises:
                :class:`plexapi.exception.Unsupported`: Websocket-client not installed.
        """
        notifier = AlertListener(self, callback)
        notifier.start()
        return notifier

# === BLOCK 6 (label=lm, source_idx=line2047_lm, name=lower_ext) ===
def lower_ext(abspath):
    """Convert file extension to lowercase.
    """
    filename = os.path.basename(abspath)
    name, ext = os.path.splitext(filename)
    return os.path.join(os.path.dirname(abspath), name + ext.lower())
