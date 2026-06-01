# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2793_lm, name=blue) ===
def blue(self, memo=None):
        """
        Constructs a Blueprint out of the current object.

        :param memo:
            A dictionary to cache Blueprints.
        :type memo: dict[T,schedula.utils.blue.Blueprint]

        :return:
            A Blueprint of the current object.
        :rtype: schedula.utils.blue.Blueprint
        """
        if memo is None:
            memo = {}

        if self in memo:
            return memo[self]

        if isinstance(self, (int, float, str, bool)):
            return Blueprint(self)

        if isinstance(self, (list, tuple)):
            return Blueprint(
                [self.blue(memo) for self in self]
            )

        if isinstance(self, dict):
            return Blueprint(
                {
                    key: self.blue(memo)
                    for key in self
                }
            )

        if isinstance(self, set):
            return Blueprint(
                {
                    self.blue(memo)
                    for self in self
                }
            )

        if isinstance(self, (type, type(None))):
            return Blueprint(self)

        if isinstance(self, object):
            return Blueprint(
                {
                    key: self.blue(memo)
                    for key in dir(self)
                    if not key.startswith('_')
                }
            )

        raise TypeError(
            'Cannot blue an object of type {0}'.format(
                type(self)
            )
        )

# === BLOCK 2 (label=human, source_idx=line4997_human, name=extract) ===
def extract(what, calc_id, webapi=True):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    By default uses the WebAPI, otherwise the extraction is done locally.
    """
    with performance.Monitor('extract', measuremem=True) as mon:
        if webapi:
            obj = WebExtractor(calc_id).get(what)
        else:
            obj = Extractor(calc_id).get(what)
        fname = '%s_%d.hdf5' % (what.replace('/', '-').replace('?', '-'),
                                calc_id)
        obj.save(fname)
        print('Saved', fname)
    if mon.duration > 1:
        print(mon)

# === BLOCK 3 (label=human, source_idx=line4440_human, name=moduleInfo) ===
def moduleInfo( module ):
        """
        Generates HTML information to display for the about info for a module.

        :param      module  | <module>
        """
        data = module.__dict__

        html = []
        html.append( '<h2>%s</h2>' % data.get('__name__', 'Unknown') )
        html.append( '<hr/>' )
        ver = data.get('__version__', '0')
        html.append( '<small>version: %s</small>' % ver)
        html.append( '<br/>' )
        html.append( nativestring(data.get('__doc__', '')) )
        html.append( '<br/><br/><b>Authors</b><ul/>' )

        for author in data.get('__authors__', []):
            html.append( '<li>%s</li>' % author )

        html.append( '</ul>' )
        html.append( '<br/><br/><b>Depends on:</b>' )
        for depends in data.get('__depends__', []):
            html.append( '<li>%s</li>' % depends )

        html.append( '</ul>' )
        html.append( '' )
        html.append( '<br/><br/><b>Credits</b></ul>' )

        for credit in data.get('__credits__', []):
            html.append('<li>%s: %s</li>' % credit)

        html.append( '</ul>' )

        opts = (data.get('__maintainer__', ''), data.get('__email__', ''))
        html.append('<br/><br/><small>maintained by: %s email: %s</small>' % opts)

        opts = (data.get('__copyright__', ''), data.get('__license__', ''))
        html.append('<br/><small>%s | license: %s</small>' % opts)

        return '\n'.join(html)

# === BLOCK 4 (label=lm, source_idx=line761_lm, name=parameterized_send) ===
def parameterized_send(self, request, parameter_list):
        """Send batched requests for a list of parameters

        Args:
            request (str): Request to send, like "%s.*?\n"
            parameter_list (list): parameters to format with, like
                ["TTLIN", "TTLOUT"]

        Returns:
            dict: {parameter: response_queue}
        """
        responses = {}
        for parameter in parameter_list:
            responses[parameter] = self.send(request.format(parameter))
        return responses

# === BLOCK 5 (label=lm, source_idx=line3572_lm, name=ls_) ===
def ls_(active=None, cache=True, path=None):
    """
    Return a list of the containers available on the minion

    path
        path to the container parent directory
        default: /var/lib/lxc (system)

        .. versionadded:: 2015.8.0

    active
        If ``True``, return only active (i.e. running) containers

        .. versionadded:: 2015.5.0

    CLI Example:

    .. code-block:: bash

        salt '*' lxc.ls
        salt '*' lxc.ls active=True
    """
    ret = []
    if path is None:
        path = _get_path()
    if not os.path.isdir(path):
        return ret
    for container in os.listdir(path):
        if not os.path.isdir(os.path.join(path, container)):
            continue
        if active is not None:
            if active:
                if not os.path.isfile(os.path.join(path, container, 'lxc.state')):
                    continue
            else:
                if os.path.isfile(os.path.join(path, container, 'lxc.state')):
                    continue
        if cache:
            ret.append(container)
        else:
            if os.path.isfile(os.path.join(path, container, 'lxc.state')):
                ret.append(container)
    return ret

# === BLOCK 6 (label=human, source_idx=line6586_human, name=transform_current_line) ===
def transform_current_line(self, transform_callback):
        """
        Apply the given transformation function to the current line.

        :param transform_callback: callable that takes a string and return a new string.
        """
        document = self.document
        a = document.cursor_position + document.get_start_of_line_position()
        b = document.cursor_position + document.get_end_of_line_position()
        self.text = (
            document.text[:a] +
            transform_callback(document.text[a:b]) +
            document.text[b:])
