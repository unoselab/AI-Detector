# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1782_human, name=_inject_language) ===
def _inject_language(self, src, strings):
    """Injects languages into (potentially) template strings."""
    if src not in self.sources:
      raise ValueError("Invalid source for '{0}': {1}".format(self.name, src))
    def _format_string(s):
      if "{0}" in s and "{1}" and "{src}" in s:
        return s.format(*sorted([src, self.target]), src=src)
      elif "{0}" in s and "{1}" in s:
        return s.format(*sorted([src, self.target]))
      elif "{src}" in s:
        return s.format(src=src)
      else:
        return s
    return [_format_string(s) for s in strings]

# === BLOCK 2 (label=lm, source_idx=line4110_lm, name=insights) ===
def insights(self):
        """
        Access the Insights Twilio Domain

        :returns: Insights Twilio Domain
        :rtype: twilio.rest.insights.Insights
        """
        return self._client.insights

# === BLOCK 3 (label=human, source_idx=line3445_human, name=respond) ===
def respond(self, output):
        """Generates server response."""
        response = {'exit_code': output.code,
                    'command_output': output.log}

        self.send_response(200)

        self.send_header('Content-type', 'application/json')
        self.end_headers()

        self.wfile.write(bytes(json.dumps(response), "utf8"))

# === BLOCK 4 (label=lm, source_idx=line6135_lm, name=get_bool_attr) ===
def get_bool_attr(self, name):
    """ Returns the value of a boolean HTML attribute like `checked` or `disabled`
    """
    return self.attrs.get(name, False)

# === BLOCK 5 (label=lm, source_idx=line8051_lm, name=remove) ===
def remove(app_id):
    """
    Remove a bundle ID or command as being allowed to use assistive access.

    app_id
        The bundle ID or command to remove from assistive access list.

    CLI Example:

    .. code-block:: bash

        salt '*' assistive.remove /usr/bin/osascript
        salt '*' assistive.remove com.smileonmymac.textexpander
    """
    import subprocess
    try:
        subprocess.run(['sudo', 'profiles', 'remove', '-app', app_id], check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError:
        return False

# === BLOCK 6 (label=human, source_idx=line6348_human, name=open_recruitment) ===
def open_recruitment(self, n=1):
        """Start recruiting right away."""
        logger.info("Opening Bot recruitment for {} participants".format(n))
        factory = self._get_bot_factory()
        bot_class_name = factory("", "", "").__class__.__name__
        return {
            "items": self.recruit(n),
            "message": "Bot recruitment started using {}".format(bot_class_name),
        }
