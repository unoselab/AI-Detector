# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3323_lm, name=walk_dir_with_filter) ===
def walk_dir_with_filter(pth, prefix=None, suffix=None):
    """
        默认情况下,会遍历目录下所有文件,写入数组返回.

    - ``prefix`` 会过滤以 其开头的所有文件
    - ``suffix`` 结尾

    :param pth:
    :type pth:
    :param prefix:
    :type prefix:
    :param suffix:
    :type suffix:
    :return:
    :rtype:
    """
    files = []
    for root, _, filenames in os.walk(pth):
        for filename in filenames:
            if (prefix is None or filename.startswith(prefix)) and (suffix is None or filename.endswith(suffix)):
                files.append(os.path.join(root, filename))
    return files

# === BLOCK 2 (label=human, source_idx=line4012_human, name=_F) ===
def _F(self, X):
        """
        analytic solution of the projection integral

        :param x: R/Rs
        :type x: float >0
        """
        if isinstance(X, int) or isinstance(X, float):
            if X < 1 and X > 0:
                a = 1/(X**2-1)*(1-2/np.sqrt(1-X**2)*np.arctanh(np.sqrt((1-X)/(1+X))))
            elif X == 1:
                a = 1./3
            elif X > 1:
                a = 1/(X**2-1)*(1-2/np.sqrt(X**2-1)*np.arctan(np.sqrt((X-1)/(1+X))))
            else:  # X == 0:
                c = 0.0000001
                a = 1/(-1)*(1-2/np.sqrt(1)*np.arctanh(np.sqrt((1-c)/(1+c))))

        else:
            a = np.empty_like(X)
            x = X[(X < 1) & (X > 0)]
            a[(X < 1) & (X > 0)] = 1/(x**2-1)*(1-2/np.sqrt(1-x**2)*np.arctanh(np.sqrt((1-x)/(1+x))))

            a[X == 1] = 1./3.

            x = X[X > 1]
            a[X > 1] = 1/(x**2-1)*(1-2/np.sqrt(x**2-1)*np.arctan(np.sqrt((x-1)/(1+x))))
            # a[X>y] = 0

            c = 0.0000001
            a[X == 0] = 1/(-1)*(1-2/np.sqrt(1)*np.arctanh(np.sqrt((1-c)/(1+c))))
        return a

# === BLOCK 3 (label=lm, source_idx=line1400_lm, name=_extend_blocks) ===
def _extend_blocks(extend_node, blocks, context):
    """
    Extends the dictionary `blocks` with *new* blocks in the parent node (recursive)

    :param extend_node: The ``{% extends .. %}`` node object.
    :type extend_node: ExtendsNode
    :param blocks: dict of all block names found in the template.
    :type blocks: dict
    """
    parent_template = extend_node.get_parent(context)
    parent_blocks = parent_template.find_all_blocks()
    for name, parent_block in parent_blocks.items():
        if name not in blocks:
            blocks[name] = parent_block.copy()
        else:
            blocks[name].extend(parent_block)
    for child in parent_template.children:
        if isinstance(child, ExtendsNode):
            _extend_blocks(child, blocks, context)

# === BLOCK 4 (label=lm, source_idx=line3665_lm, name=_build_request_url) ===
def _build_request_url(self, secure, api_method):
        """Build a URL for a API method request
        """
        protocol = 'https' if secure else 'http'
        host = self.secure_host if secure else self.host
        return f'{protocol}://{host}/{api_method}'

# === BLOCK 5 (label=human, source_idx=line1884_human, name=_param_to_matrix) ===
def _param_to_matrix(self):
        """
        Convert parameters defined in `self._params` to `cvxopt.matrix`

        :return None
        """
        for item in self._params:
            self.__dict__[item] = matrix(self.__dict__[item], tc='d')

# === BLOCK 6 (label=human, source_idx=line1374_human, name=compatible_firmware_version) ===
def compatible_firmware_version(self):
        """Returns the DLL's compatible J-Link firmware version.

        Args:
          self (JLink): the ``JLink`` instance

        Returns:
          The firmware version of the J-Link that the DLL is compatible
          with.

        Raises:
          JLinkException: on error.
        """
        identifier = self.firmware_version.split('compiled')[0]
        buf_size = self.MAX_BUF_SIZE
        buf = (ctypes.c_char * buf_size)()
        res = self._dll.JLINKARM_GetEmbeddedFWString(identifier.encode(), buf, buf_size)
        if res < 0:
            raise errors.JLinkException(res)

        return ctypes.string_at(buf).decode()
