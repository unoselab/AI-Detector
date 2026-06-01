# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6243_lm, name=create) ===
def create(self):
        """
        Creates a Flask Application that can be started.
        """
        app = Flask(__name__)
        app.config.from_object(self.config)
        app.register_blueprint(self.blueprint)
        return app

# === BLOCK 2 (label=lm, source_idx=line3211_lm, name=new_connection) ===
def new_connection (self):
        """Connect to clamd for stream scanning.

        @return: tuple (connected socket, host)
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
        except socket.error as e:
            raise ClamdError("Unable to connect to clamd: %s" % e)
        return (sock, self.host)

# === BLOCK 3 (label=human, source_idx=line2399_human, name=get_records_with_attachments) ===
def get_records_with_attachments(attachment_table, rel_object_field="REL_OBJECTID"):
    """returns a list of ObjectIDs for rows in the attachment table"""
    if arcpyFound == False:
        raise Exception("ArcPy is required to use this function")
    OIDs = []
    with arcpy.da.SearchCursor(attachment_table,
                               [rel_object_field]) as rows:
        for row in rows:
            if not str(row[0]) in OIDs:
                OIDs.append("%s" % str(row[0]))
            del row
    del rows
    return OIDs

# === BLOCK 4 (label=human, source_idx=line392_human, name=sendall) ===
def sendall(self, data, **kws):
        """Send data to the socket. The socket must be connected to a remote
        socket. All the data is guaranteed to be sent."""
        return SendAll(self, data, timeout=self._timeout, **kws)

# === BLOCK 5 (label=human, source_idx=line4565_human, name=_fix_quantities) ===
def _fix_quantities(tree):
    """
    Stupidly simple function to fix any Items/Quantity disparities inside a
    DistributionConfig block before use. Since AWS only accepts JSON-encodable
    data types, this implementation is "good enough" for our purposes.
    """
    if isinstance(tree, dict):
        tree = {k: _fix_quantities(v) for k, v in tree.items()}
        if isinstance(tree.get('Items'), list):
            tree['Quantity'] = len(tree['Items'])
            if not tree['Items']:
                tree.pop('Items')  # Silly, but AWS requires it....
        return tree
    elif isinstance(tree, list):
        return [_fix_quantities(t) for t in tree]
    else:
        return tree

# === BLOCK 6 (label=lm, source_idx=line5964_lm, name=query_orders) ===
def query_orders(self, accounts, status='filled'):
        """查询订单

        Arguments:
            accounts {[type]} -- [description]

        Keyword Arguments:
            status {str} -- 'open' 待成交 'filled' 成交 (default: {'filled'})

        Returns:
            [type] -- [description]
        """
        orders = []
        for account in accounts:
            orders.extend(self.query_order(account, status))
        return orders
