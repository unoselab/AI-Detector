# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8990_lm, name=appendChild) ===
def appendChild(self, child: 'WdomElement') -> Node:
        """Append child node at the last of child nodes.

        If this instance is connected to the node on browser, the child node is
        also added to it.
        """
        self.children.append(child)
        if self.node is not None:
            self.node.appendChild(child.node)
        return child

# === BLOCK 2 (label=human, source_idx=line1804_human, name=_get_contents) ===
def _get_contents(self):
        """Create strings from lazy strings."""
        return [
            str(value) if is_lazy_string(value) else value
            for value in super(LazyNpmBundle, self)._get_contents()
        ]

# === BLOCK 3 (label=human, source_idx=line6002_human, name=tarbell_list_templates) ===
def tarbell_list_templates(command, args):
    """
    List available Tarbell blueprints.
    """
    with ensure_settings(command, args) as settings:
        puts("\nAvailable project templates\n")
        _list_templates(settings)
        puts("")

# === BLOCK 4 (label=lm, source_idx=line1696_lm, name=to_creator) ===
def to_creator(self, subject, desc):
        """ Return a python-zimbra dict for CreateTaskRequest

        Example :
        <CreateTaskRequest>
            <m su="Task subject">
                <inv>
                    <comp name="Task subject">
                        <fr>Task comment</fr>
                        <desc>Task comment</desc>
                    </comp>
                </inv>
                <mp>
                    <content/>
                </mp>
            </m>
        </CreateTaskRequest>
        """
        return {
            "CreateTaskRequest": {
                "m": {
                    "su": subject,
                    "inv": {
                        "comp": {
                            "name": subject,
                            "fr": desc,
                            "desc": desc
                        }
                    }
                }
            }
        }

# === BLOCK 5 (label=lm, source_idx=line6557_lm, name=parse) ===
def parse(self, parser):
        """Main method to render data into the template."""
        self.data = parser.parse_data()
        self.template = parser.parse_template()
        self.rendered = self.template.render(self.data)
        return self.rendered

# === BLOCK 6 (label=human, source_idx=line8645_human, name=_read_line) ===
def _read_line(self, f):
        """
        Reads one non empty line (if it's a comment, it skips it).
        """
        l = f.readline().strip()
        while l == "" or l[0] == "#": # comment or an empty line
            l = f.readline().strip()
        return l
