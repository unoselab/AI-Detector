# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line908_lm, name=generate_veq) ===
def generate_veq(R=1.3, dR=0.1, Prot=6, dProt=0.1,nsamples=1e4,plot=False,
                 R_samples=None,Prot_samples=None):
    """ Returns the mean and std equatorial velocity given R,dR,Prot,dProt

    Assumes all distributions are normal.  This will be used mainly for
    testing purposes; I can use MC-generated v_eq distributions when we go for real.
    """
    if R_samples is None:
        R_samples = np.random.normal(R, dR, int(nsamples))
    if Prot_samples is None:
        Prot_samples = np.random.normal(Prot, dProt, int(nsamples))
    veq_samples = 2 * np.pi * R_samples / Prot_samples
    mean_veq = np.mean(veq_samples)
    std_veq = np.std(veq_samples)
    if plot:
        import matplotlib.pyplot as plt
        plt.hist(veq_samples, bins=50)
        plt.xlabel('Equatorial velocity')
        plt.ylabel('Frequency')
        plt.show()
    return mean_veq, std_veq

# === BLOCK 2 (label=human, source_idx=line1582_human, name=generate) ===
def generate(self, state_size=None, start=(), dataset='', backward=False):
        """Generate a sequence.

        Parameters
        ----------
        state_size : `int`, optional
            State size (default: parser.state_sizes[0]).
        start : `str` or `iterable` of `str`, optional
            Initial state (default: ()).
        dataset : `str`, optional
            Dataset key prefix.
        backward : `bool`, optional
            Link direction.

        Returns
        -------
        `generator` of `str`
            State generator.
        """
        if state_size is None:
            try:
                state_size = next(iter(self.parser.state_sizes))
            except StopIteration:
                return
        #elif (self.parser is not None
        #      and state_size not in self.parser.state_sizes):
        #    raise ValueError('invalid state size: {0}: not in {1}'
        #                     .format(state_size, self.parser.state_sizes))
        dataset += state_size_dataset(state_size)
        return self.storage.generate(start, state_size, dataset, backward)

# === BLOCK 3 (label=human, source_idx=line3863_human, name=action_webimport) ===
def action_webimport(hrlinetop=False):
    """ select from the available online directories for import """
    DIR_OPTIONS = {1: "http://lov.okfn.org", 2: "http://prefix.cc/popular/"}
    selection = None
    while True:
        if hrlinetop:
            printDebug("----------")
        text = "Please select which online directory to scan: (enter=quit)\n"
        for x in DIR_OPTIONS:
            text += "%d) %s\n" % (x, DIR_OPTIONS[x])
        var = input(text + "> ")
        if var == "q" or var == "":
            return None
        else:
            try:
                selection = int(var)
                test = DIR_OPTIONS[selection]  #throw exception if number wrong
                break
            except:
                printDebug("Invalid selection. Please try again.", "important")
                continue

    printDebug("----------")
    text = "Search for a specific keyword? (enter=show all)\n"
    var = input(text + "> ")
    keyword = var

    try:
        if selection == 1:
            _import_LOV(keyword=keyword)
        elif selection == 2:
            _import_PREFIXCC(keyword=keyword)
    except:
        printDebug("Sorry, the online repository seems to be unreachable.")

    return True

# === BLOCK 4 (label=lm, source_idx=line1549_lm, name=add_scm_info) ===
def add_scm_info(self):
    """Adds SCM-related info."""
    self.scm_info = {}
    self.scm_info["branch"] = "main"
    self.scm_info["revision"] = "1234567"
    self.scm_info["url"] = "https://github.com/my-org/my-repo"

# === BLOCK 5 (label=lm, source_idx=line4186_lm, name=ask_user) ===
def ask_user(prompt: str, default: str = None) -> Optional[str]:
    """
    Prompts the user, with a default. Returns user input from ``stdin``.
    """
    if default is not None:
        prompt += f" [default: {default}]"
    user_input = input(prompt + ": ")
    if user_input == "":
        return default
    return user_input

# === BLOCK 6 (label=human, source_idx=line705_human, name=last_ehlo_response) ===
def last_ehlo_response(self, response: SMTPResponse) -> None:
        """
        When setting the last EHLO response, parse the message for supported
        extensions and auth methods.
        """
        extensions, auth_methods = parse_esmtp_extensions(response.message)
        self._last_ehlo_response = response
        self.esmtp_extensions = extensions
        self.server_auth_methods = auth_methods
        self.supports_esmtp = True
