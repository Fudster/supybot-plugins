###
# Copyright (c) 2016, Fudster
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import string
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Pirate')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Pirate(callbacks.Plugin):
    """English to Pirate translator"""
    
    

    def pirate(self, irc, msg, args, sentence):
        """<phrase>
        Converts Phrase into Pirate speak"""
        pirate = {
            "sir":      "matey",
            "hotel":    "fleabag inn",
            "student":  "swabbie",
            "boy":      "lad",
            "girl":     "lass",
            "little":   "wee",
            "yes":      "aye",
            "no":       "arr",
            "beer":     "rum",
            "treasure": "booty",
            "my":       "me",
            "your":     "yer",
            "ass":      "arse",
            "hello":    "ahoy",
            "madam":    "proud beauty",
            "old":      "barnacle-covered",
            "bank":     "buried trasure",
            "nearby":   "broadside",
            "where is": "whar be",
            "happy":    "grog-filled",
            "mail":     "market",
            "friend":   "mate",
            "money":    "doubloons",
            "food":     "grub",
        }
        exclude = set(string.punctuation)
        def pun(s):
            return ''.join(ch for ch in s if ch not in exclude)
        sentence2 = pun(sentence)
        phrase = sentence2.split()
        newphrase = []
        for word in phrase:
            if word in pirate.keys():
                newphrase.append(pirate[word])
            else:
                newphrase.append(word)
        irc.reply(" ".join(newphrase), prefixNick=False)

    pirate = wrap(pirate, ['text'])
    
Class = Pirate
