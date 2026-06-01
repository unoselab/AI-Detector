# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line759_lm, name=_process_credentials) ===
def _process_credentials(self, req, resp, origin):
        """Adds the Access-Control-Allow-Credentials to the response
        if the cors settings indicates it should be set.
        """
        resp.headers['Access-Control-Allow-Credentials'] = 'true'

# === BLOCK 2 (label=lm, source_idx=line376_lm, name=where) ===
def where(cond, a, b, use_numexpr=True):
    """ evaluate the where condition cond on a and b

        Parameters
        ----------

        cond : a boolean array
        a :    return if cond is True
        b :    return if cond is False
        use_numexpr : whether to try to use numexpr (default True)
        """
    if use_numexpr:
        try:
            import numexpr as ne
            return ne.evaluate("where(cond, a, b)", local_dict={'cond': cond, 'a': a, 'b': b})
        except (ImportError, Exception):
            pass
    import numpy as np
    return np.where(cond, a, b)

# === BLOCK 3 (label=human, source_idx=line2677_human, name=refine_water_bridges) ===
def refine_water_bridges(self, wbridges, hbonds_ldon, hbonds_pdon):
        """A donor atom already forming a hydrogen bond is not allowed to form a water bridge. Each water molecule
        can only be donor for two water bridges, selecting the constellation with the omega angle closest to 110 deg."""
        donor_atoms_hbonds = [hb.d.idx for hb in hbonds_ldon + hbonds_pdon]
        wb_dict = {}
        wb_dict2 = {}
        omega = 110.0

        # Just one hydrogen bond per donor atom
        for wbridge in [wb for wb in wbridges if wb.d.idx not in donor_atoms_hbonds]:
            if (wbridge.water.idx, wbridge.a.idx) not in wb_dict:
                wb_dict[(wbridge.water.idx, wbridge.a.idx)] = wbridge
            else:
                if abs(omega - wb_dict[(wbridge.water.idx, wbridge.a.idx)].w_angle) < abs(omega - wbridge.w_angle):
                    wb_dict[(wbridge.water.idx, wbridge.a.idx)] = wbridge
        for wb_tuple in wb_dict:
            water, acceptor = wb_tuple
            if water not in wb_dict2:
                wb_dict2[water] = [(abs(omega - wb_dict[wb_tuple].w_angle), wb_dict[wb_tuple]), ]
            elif len(wb_dict2[water]) == 1:
                wb_dict2[water].append((abs(omega - wb_dict[wb_tuple].w_angle), wb_dict[wb_tuple]))
                wb_dict2[water] = sorted(wb_dict2[water])
            else:
                if wb_dict2[water][1][0] < abs(omega - wb_dict[wb_tuple].w_angle):
                    wb_dict2[water] = [wb_dict2[water][0], (wb_dict[wb_tuple].w_angle, wb_dict[wb_tuple])]

        filtered_wb = []
        for fwbridges in wb_dict2.values():
            [filtered_wb.append(fwb[1]) for fwb in fwbridges]
        return filtered_wb

# === BLOCK 4 (label=human, source_idx=line4864_human, name=send) ===
def send(self, sender: PytgbotApiBot):
        """
        Send the message via pytgbot.

        :param sender: The bot instance to send with.
        :type  sender: pytgbot.bot.Bot

        :rtype: PytgbotApiMessage
        """
        return sender.send_video(
            # receiver, self.media, disable_notification=self.disable_notification, reply_to_message_id=reply_id
            video=self.video, chat_id=self.receiver, reply_to_message_id=self.reply_id, duration=self.duration, width=self.width, height=self.height, thumb=self.thumb, caption=self.caption, parse_mode=self.parse_mode, supports_streaming=self.supports_streaming, disable_notification=self.disable_notification, reply_markup=self.reply_markup
        )

# === BLOCK 5 (label=human, source_idx=line5550_human, name=tag) ===
def tag(self, utterance, context_trie=None):
        """
        Tag known entities within the utterance.
        Args:
            utterance(str): a string of natural language text
            context_trie(trie): optional, a trie containing only entities from context
                for this request

        Returns: dictionary, with the following keys
            match(str): the proper entity matched
            key(str): the string that was matched to the entity
            start_token(int): 0-based index of the first token matched
            end_token(int): 0-based index of the last token matched
            entities(list): a list of entity kinds as strings (Ex: Artist, Location)
        """
        tokens = self.tokenizer.tokenize(utterance)
        entities = []
        if len(self.regex_entities) > 0:
            for part, idx in self._iterate_subsequences(tokens):
                local_trie = Trie()
                for regex_entity in self.regex_entities:
                    match = regex_entity.match(part)
                    groups = match.groupdict() if match else {}
                    for key in list(groups):
                        match_str = groups.get(key)
                        local_trie.insert(match_str, (match_str, key))
                sub_tagger = EntityTagger(local_trie, self.tokenizer, max_tokens=self.max_tokens)
                for sub_entity in sub_tagger.tag(part):
                    sub_entity['start_token'] += idx
                    sub_entity['end_token'] += idx
                    for e in sub_entity['entities']:
                        e['confidence'] = 0.5
                    entities.append(sub_entity)
        additional_sort = len(entities) > 0

        context_entities = []
        for i in xrange(len(tokens)):
            part = ' '.join(tokens[i:])

            for new_entity in self.trie.gather(part):
                new_entity['data'] = list(new_entity['data'])
                entities.append({
                    'match': new_entity.get('match'),
                    'key': new_entity.get('key'),
                    'start_token': i,
                    'entities': [new_entity],
                    'end_token': i + len(self.tokenizer.tokenize(new_entity.get('match'))) - 1,
                    'from_context': False
                })

            if context_trie:
                for new_entity in context_trie.gather(part):
                    new_entity['data'] = list(new_entity['data'])
                    new_entity['confidence'] *= 2.0  # context entities get double the weight!
                    context_entities.append({
                        'match': new_entity.get('match'),
                        'key': new_entity.get('key'),
                        'start_token': i,
                        'entities': [new_entity],
                        'end_token': i + len(self.tokenizer.tokenize(new_entity.get('match'))) - 1,
                        'from_context': True
                    })

        additional_sort = additional_sort or len(entities) > 0

        if additional_sort:
            entities = self._sort_and_merge_tags(entities + context_entities)

        return entities

# === BLOCK 6 (label=lm, source_idx=line7240_lm, name=set_application_name) ===
def set_application_name(self, options):
        """
        Set the application_name on PostgreSQL connection

        Use the fallback_application_name to let the user override
        it with PGAPPNAME env variable

        http://www.postgresql.org/docs/9.4/static/libpq-connect.html#LIBPQ-PARAMKEYWORDS  # noqa
        """
        app_name = options.get('application_name') or options.get('fallback_application_name')
        if app_name:
            self.connection_params['application_name'] = app_name
