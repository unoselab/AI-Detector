# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6783_human, name=keyword) ===
def keyword(self) -> Tuple[Optional[str], str]:
        """Parse a YANG statement keyword.

        Raises:
            EndOfInput: If past the end of input.
            UnexpectedInput: If no syntactically correct keyword is found.
        """
        i1 = self.yang_identifier()
        if self.peek() == ":":
            self.offset += 1
            i2 = self.yang_identifier()
            return (i1, i2)
        return (None, i1)

# === BLOCK 2 (label=human, source_idx=line4974_human, name=load_containers) ===
def load_containers(self, service, configs, use_cache):
        """
        :param service_name:
        :return None:
        """
        if not isinstance(service, Service):
            raise TypeError("service must be and instance of service.  {0} was passed.".format(service))

        if not self.healthy():
            logger.error("unable to connect to container ship.")
            raise Exception('lost comms with our container ship')

        self._load_service_containers(service, configs, use_cache)

# === BLOCK 3 (label=lm, source_idx=line4105_lm, name=load_image_imread) ===
def load_image_imread(file, shape=None, max_range=1.0):
    """
    Load image from file like object.

    :param file: Image contents
    :type file: file like object.
    :param shape: shape of output array
        e.g. (3, 128, 192) : n_color, height, width.
    :type shape: tuple of int
    :param float max_range: the value of return array ranges from 0 to `max_range`.

    :return: numpy array

    """
    import numpy as np
    from PIL import Image
    import io

    image = Image.open(io.BytesIO(file) if isinstance(file, bytes) else file)
    image = image.convert('RGB')
    image = np.array(image).astype(np.float32)

    if shape is not None:
        image = np.array(image.resize((shape[2], shape[1]), Image.BILINEAR))

    image = image.transpose((2, 0, 1))
    image = (image / 255.0) * max_range

    return image

# === BLOCK 4 (label=lm, source_idx=line4140_lm, name=get_property) ===
def get_property(self, remote_path, option):
        """Gets metadata property of remote resource on WebDAV server.
        More information you can find by link http://webdav.org/specs/rfc4918.html#METHOD_PROPFIND

        :param remote_path: the path to remote resource.
        :param option: the property attribute as dictionary with following keys:
                       `namespace`: (optional) the namespace for XML property which will be set,
                       `name`: the name of property which will be set.
        :return: the value of property or None if property is not found.
        """
        import requests
        from lxml import etree

        url = f"{self.base_url}/{remote_path}"
        namespace = option.get('namespace', 'DAV:')
        prop_name = option['name']

        xml_body = f"""<?xml version="1.0" encoding="utf-8" ?>
        <propfind xmlns="DAV:">
          <prop>
            <{prop_name} xmlns="{namespace}" />
          </prop>
        </propfind>"""

        headers = {'Depth': '0', 'Content-Type': 'text/xml; charset=utf-8'}
        response = requests.request('PROPFIND', url, data=xml_body, headers=headers, auth=self.auth)

        if response.status_code != 207:
            return None

        root = etree.fromstring(response.content)
        ns = {'dav': 'DAV:', 'custom': namespace}

        # Search for the property value within the response XML
        xpath_query = f"//dav:prop/*[local-name()='{prop_name}']"
        element = root.xpath(xpath_query)

        if element:
            return element[0].text
        return None

# === BLOCK 5 (label=human, source_idx=line5444_human, name=cache) ===
def cache(cls, id):
        """return the number of query cache for the last 24H"""
        sampler = {'unit': 'days', 'value': 1, 'function': 'sum'}
        query = 'webacc.requests.cache.all'
        metrics = Metric.query(id, 60 * 60 * 24, query, 'paas', sampler)

        cache = {'hit': 0, 'miss': 0, 'not': 0, 'pass': 0}
        for metric in metrics:
            what = metric['cache'].pop()
            for point in metric['points']:
                value = point.get('value', 0)
                cache[what] += value
        return cache

# === BLOCK 6 (label=lm, source_idx=line1335_lm, name=step) ===
def step( self, peer_table=None, zonefile_queue=None, path=None ):
        """
        Run one step of this algorithm.
        Push the zonefile to all the peers that need it.
        Return the number of peers we sent to
        """
        if peer_table is None or zonefile_queue is None:
            return 0

        sent_count = 0
        while not zonefile_queue.empty():
            zonefile = zonefile_queue.get()
            for peer in peer_table:
                if peer.needs_update(zonefile):
                    peer.send_zonefile(zonefile, path)
                    sent_count += 1
        return sent_count
