# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4338_human, name=submit_form_action) ===
def submit_form_action(step, url):
    """
    Submit the form having given action URL.
    """
    form = world.browser.find_element_by_xpath(str('//form[@action="%s"]' %
                                                   url))
    form.submit()

# === BLOCK 2 (label=human, source_idx=line8490_human, name=x509_rsa_load) ===
def x509_rsa_load(txt):
    """ So I get the same output format as loads produces
    :param txt:
    :return:
    """
    pub_key = import_rsa_key(txt)
    if isinstance(pub_key, rsa.RSAPublicKey):
        return [("rsa", pub_key)]

# === BLOCK 3 (label=lm, source_idx=line8700_lm, name=_build_projection_expression) ===
def _build_projection_expression(clean_table_keys):
    """Given cleaned up keys, this will return a projection expression for
    the dynamodb lookup.

    Args:
        clean_table_keys (dict): keys without the data types attached

    Returns:
        str: A projection expression for the dynamodb lookup.
    """
    return ", ".join(clean_table_keys.keys())

# === BLOCK 4 (label=lm, source_idx=line2826_lm, name=on_send) ===
def on_send(self, frame):
        """
        Add the heartbeat header to the frame when connecting, and bump
        next outbound heartbeat timestamp.

        :param Frame frame: the Frame object
        """
        frame.header.add_heartbeat()
        self.next_outbound_heartbeat = self.heartbeat_interval + self.current_time()

# === BLOCK 5 (label=lm, source_idx=line668_lm, name=stream_upload) ===
def stream_upload(self, data, callback):
        """Generator for streaming request body data.

        :param data: A file-like object to be streamed.
        :param callback: Custom callback for monitoring progress.
        """
        chunk_size = 8192
        while True:
            chunk = data.read(chunk_size)
            if not chunk:
                break
            if callback:
                callback(len(chunk))
            yield chunk

# === BLOCK 6 (label=human, source_idx=line1455_human, name=write_out_page) ===
def write_out_page(self, output, page):
        """
        Banana banana
        """
        subpages = OrderedDict({})
        all_pages = self.project.tree.get_pages()
        subpage_names = self.get_subpages_sorted(all_pages, page)
        for pagename in subpage_names:
            proj = self.project.subprojects.get(pagename)

            if not proj:
                cpage = all_pages[pagename]
                sub_formatter = self.project.extensions[
                    cpage.extension_name].formatter
            else:
                cpage = proj.tree.root
                sub_formatter = proj.extensions[cpage.extension_name].formatter

            subpage_link, _ = cpage.link.get_link(self.app.link_resolver)
            prefix = sub_formatter.get_output_folder(cpage)
            if prefix:
                subpage_link = '%s/%s' % (prefix, subpage_link)
            subpages[subpage_link] = cpage

        html_subpages = self.formatter.format_subpages(page, subpages)

        js_dir = os.path.join(output, 'html', 'assets', 'js')
        if not os.path.exists(js_dir):
            os.makedirs(js_dir)
        sm_path = os.path.join(js_dir, 'sitemap.js')
        self.write_out_sitemap(sm_path)

        self.formatter.write_out(page, html_subpages, output)
