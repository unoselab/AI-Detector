# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2487_human, name=load_and_set_file_content) ===
def load_and_set_file_content(self, file_system_path):
        """ Implements the abstract method of the ExternalEditor class.
        """
        semantic_data = load_data_file(os.path.join(file_system_path, storage.SEMANTIC_DATA_FILE))
        self.model.state.semantic_data = semantic_data

# === BLOCK 2 (label=human, source_idx=line818_human, name=strip_quotes) ===
def strip_quotes(self, content):
        """
        Unquote given rule.

        Args:
            content (str): An import rule.

        Raises:
            InvalidImportRule: Raise exception if the rule is badly quoted
            (not started or not ended quotes).

        Returns:
            string: The given rule unquoted.
        """
        error_msg = "Following rule is badly quoted: {}"
        if (content.startswith('"') and content.endswith('"')) or \
           (content.startswith("'") and content.endswith("'")):
            return content[1:-1]
        # Quote starting but not ended
        elif (content.startswith('"') and not content.endswith('"')) or \
             (content.startswith("'") and not content.endswith("'")):
            raise InvalidImportRule(error_msg.format(content))
        # Quote ending but not started
        elif (not content.startswith('"') and content.endswith('"')) or \
             (not content.startswith("'") and content.endswith("'")):
            raise InvalidImportRule(error_msg.format(content))

        return content

# === BLOCK 3 (label=lm, source_idx=line1177_lm, name=get_withdrawals) ===
def get_withdrawals(self, account_id, **params):
        """https://developers.coinbase.com/api/v2#list-withdrawals"""
        return self._request('GET', f'/accounts/{account_id}/withdrawals', params=params)

# === BLOCK 4 (label=lm, source_idx=line869_lm, name=get_fields) ===
def get_fields(self):
        """Get all fields"""
        return self._fields

# === BLOCK 5 (label=lm, source_idx=line304_lm, name=_reset_internal) ===
def _reset_internal(self):
        """
        Sets initial pose of arm and grippers.
        """
        self.arm.set_joint_positions(self.initial_arm_joint_positions)
        self.left_gripper.set_joint_positions(self.initial_gripper_joint_positions)
        self.right_gripper.set_joint_positions(self.initial_gripper_joint_positions)

# === BLOCK 6 (label=human, source_idx=line1249_human, name=read_busiest_date) ===
def read_busiest_date(path: str) -> Tuple[datetime.date, FrozenSet[str]]:
    """Find the earliest date with the most trips"""
    feed = load_raw_feed(path)
    return _busiest_date(feed)
