# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2266_human, name=add_manager) ===
def add_manager(self, manager):
        """
        Add a single manager to the scope.

        :param manager: single username to be added to the scope list of managers
        :type manager: basestring
        :raises APIError: when unable to update the scope manager
        """
        select_action = 'add_manager'

        self._update_scope_project_team(select_action=select_action, user=manager, user_type='manager')

# === BLOCK 2 (label=lm, source_idx=line2845_lm, name=message_handler) ===
def message_handler(self, target):
        """Decorator to register a mpv script message handler.

        WARNING: Only one handler can be registered at a time for any given target.

        To unregister the message handler, call its ``unregister_mpv_messages`` function::

            player = mpv.MPV()
            @player.message_handler('foo')
            def my_handler(some, args):
                print(args)

            my_handler.unregister_mpv_messages()
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)
            return wrapper
        return decorator

# === BLOCK 3 (label=lm, source_idx=line1577_lm, name=generate_csv) ===
def generate_csv(src, out):
    """\
    Walks through `src` and generates the CSV file `out`
    """
    with open(out, 'w') as csvfile:
        writer = csv.writer(csvfile)
        for root, dirs, files in os.walk(src):
            for file in files:
                with open(os.path.join(root, file), 'r') as f:
                    for line in f:
                        writer.writerow([line])

# === BLOCK 4 (label=human, source_idx=line400_human, name=get_rmetric) ===
def get_rmetric( self, mode_inv = 'svd', return_svd = False ):
        """
        Compute the Reimannian Metric
        """
        if self.H is None:
            self.H, self.G, self.Hvv, self.Hsval = riemann_metric(self.Y, self.L, self.mdimG, invert_h = True, mode_inv = mode_inv)
        if self.G is None:
            self.G, self.Hvv, self.Hsvals,  self.Gsvals = compute_G_from_H( self.H, mode_inv = self.mode_inv )
        if mode_inv is 'svd' and return_svd:
            return self.G, self.Hvv, self.Hsvals, self.Gsvals
        else:
            return self.G

# === BLOCK 5 (label=human, source_idx=line2015_human, name=invite) ===
def invite(self, email, roles=None):
        """
        Send invitation to email with a list of roles
        :param email:
        :param roles: None or "ALL" or list of role_names
        :return:
        """
        if roles is None:
            role_ids = [self.roles['Guest'].roleId]
        elif roles == "ALL":
            role_ids = list([i.id for i in self.roles])
        else:
            if "Guest" not in roles:
                roles.append('Guest')
            role_ids = list([i.id for i in self.roles if i.name in roles])

        self._router.invite_user(data=json.dumps({
            "organizationId": self.organizationId,
            "email": email,
            "roles": role_ids}))

# === BLOCK 6 (label=lm, source_idx=line2138_lm, name=egcd) ===
def egcd(b, n):
    """
    Given two integers (b, n), returns (gcd(b, n), a, m) such that
    a*b + n*m = gcd(b, n).

    Adapted from several sources:
      https://brilliant.org/wiki/extended-euclidean-algorithm/
      https://rosettacode.org/wiki/Modular_inverse
      https://en.wikibooks.org/wiki/Algorithm_Implementation/Mathematics/Extended_Euclidean_algorithm
      https://en.wikipedia.org/wiki/Euclidean_algorithm

    >>> egcd(1, 1)
    (1, 0, 1)
    >>> egcd(12, 8)
    (4, 1, -1)
    >>> egcd(23894798501898, 23948178468116)
    (2, 2437250447493, -2431817869532)
    >>> egcd(pow(2, 50), pow(3, 50))
    (1, -260414429242905345185687, 408415383037561)

    """
    x0, x1, y0, y1 = 1, 0, 0, 1
    while n!= 0:
        q, b, n = b // n, n, b % n
        x0, x1 = x1, x0 - q * x1
        y0, y1 = y1, y0 - q * y1
    return b, x0, y0
