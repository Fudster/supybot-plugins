###
# Copyright (c) 2017, Fudster
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

from collections import defaultdict
import random

from supybot import callbacks, commands, i18n, ircdb, ircmsgs, ircutils
from supybot.commands import getopts, wrap

_ = i18n.PluginInternationalization('DOND')


class DOND(callbacks.Plugin):
    """
    This plugin implements the Deal or No Deal game.
    """

    threaded = True

    def __init__(self, irc):
        self.__parent = super(DOND, self)
        self.__parent.__init__(irc)

        #Track If game is running on Network/Channel, If who is playing.
        self.player =  defaultdict(lambda: defaultdict(str))

        self.boxes = defaultdict(lambda: defaultdict(str))
        #Which cases are opened
        self.checkList = defaultdict(lambda: defaultdict(str))
        self.yourCase = defaultdict(lambda: defaultdict(str))
        self.yourCaseValue = defaultdict(lambda: defaultdict(str))
        self.bankOffer = defaultdict(lambda: defaultdict(str))
        self.round = defaultdict(lambda: defaultdict(str))
        #Number of cases opened this round.
        self.casesOpened = defaultdict(lambda: defaultdict(str))

    def _casesRequired(self, irc, channel):
        round = {1: 6,
                 2: 5,
                 3: 4,
                 4: 3,
                 5: 2,
                 6: 1,
                 }
        r = self.round[irc.network][channel]
        return round[r]

    def _nextRound(self, irc, channel): 
        del self.bankOffer[irc.network][channel]
        self.round[irc.network][channel] += 1
        self.casesOpened[irc.network][channel] = 0
        irc.reply(_('Round %s') % self.round[irc.network][channel])
        return

    def _unopened(self, irc, channel, case=None):
        numbers = list(range(1, 27))
        unopened = [str(item) for item in map(str, numbers) if item not in self.checkList[irc.network][channel]]
        if case:
            if case in unopened:
                return True
            else:
                return False
        return ", ".join(unopened)

    def _stopGame(self, irc, msg, channel=None, forced=None, silent=None):
        channel = channel or msg.args[0]
        del self.player[irc.network][channel]
        del self.boxes[irc.network][channel]
        del self.checkList [irc.network][channel]
        del self.yourCase[irc.network][channel]
        del self.yourCaseValue[irc.network][channel]
        del self.bankOffer[irc.network][channel]
        del self.round[irc.network][channel]
        del self.casesOpened[irc.network][channel]

        if silent is True:
            return

        if forced is None:
            irc.reply(_('Game stopped.'))
        else:
            irc.queueMsg(ircmsgs.privmsg(
                channel, _('Game forcibly stopped by %s.') % forced))

            if msg.args[0] != channel:
                # If foribly stopped in a private message, also reply there.
                irc.replySuccess()

    def doNick(self, irc, msg):
        oldNick = msg.nick
        newNick = msg.args[0]

        for channel in self.player:
            if self.player[irc.network][channel] == oldNick:
                self.player[irc.network][channel] = newNick

    def doPart(self, irc, msg):
        channel = msg.args[0]

        if self.player[irc.network][channel] == msg.nick:
            self._stopGame(irc, msg)

    def doQuit(self, irc, msg):
        for channel in self.player:
            if self.player[irc.network][channel] == msg.nick:
                self._stopGame(irc, msg)

    @wrap(['inChannel'])
    def start(self, irc, msg, args, channel):
        """takes no arguments

        Starts a game of Deal or No Deal."""

        if channel != msg.args[0]:
            # The command is being called from a private message.
            irc.error(_('This command may only be used in a channel.'))
            return

        if self.player[irc.network][channel]:
            irc.error(_('A game is already in progress in this channel.'))
            return

        self.player[irc.network][channel] = msg.nick
        self.checkList[irc.network][channel] = set()
        self.boxes[irc.network][channel] = [0.01, 1, 5, 10, 25, 50, 75, 100, 200, 300, 400, 500, 750, 1000, 5000, 10000, 25000, 50000, 75000, 100000, 200000, 300000, 400000, 500000, 750000, 1000000]
        self.round[irc.network][channel] = 1
        self.casesOpened[irc.network][channel] = 0

        irc.reply('Welcome to the game of Deal Or No Deal!', prefixNick=True)
        irc.reply(_('Available cases: %s') % self._unopened(irc, channel))
        irc.reply('Pick your case with: dond pick')

    @wrap(['inChannel'])
    def cases(self, irc, msg, args, channel):
        """takes no arguments

        Lists the current unopened cases."""

        if self.player[irc.network][channel]:
                irc.reply(_('Available cases: %s') % self._unopened(irc, channel))
                return
        else:
            return

    @wrap(['inChannel', 'text'])
    def pick(self, irc, msg, args, channel, text):
        """<Case>

        Allows a player to pick a case."""

        if channel != msg.args[0]:
            # The command is being called from a private message.
            irc.error(_('This command may only be used in a channel.'))
            return

        if self.player[irc.network][channel] == msg.nick:
            parts = text.split()
            if not self.yourCase[irc.network][channel]:
                if self._unopened(irc, channel, parts[0]):

                    self.checkList[irc.network][channel].add(str(parts[0]))
                    case = random.choice(self.boxes[irc.network][channel])
                    self.boxes[irc.network][channel].remove(int(case))
                    self.yourCase[irc.network][channel] = parts[0]
                    self.yourCaseValue[irc.network][channel] = case
                    irc.reply(_('Case %s picked. You can now open cases using dond open <numbers>. You need to open %s cases.') % (parts[0], self._casesRequired(irc, channel)))
                    return
                else:
                    irc.reply(_('%s is not a vaild case number') % parts[0])
                    return
    
    @wrap(['channel'])
    def test(self, irc, msg, args, channel):
        """takes no arguments

        Lists the current unopened cases."""

        irc.reply(_('Player: %s, boxes %s, Checklist: %s, yourCase: %s, yourCaseValue: %s, bankOffer: %s, round: %s, cases: %s') % (self.player[irc.network][channel], self.boxes[irc.network][channel], self.checkList [irc.network][channel], self.yourCase[irc.network][channel], self.yourCaseValue[irc.network][channel], self.bankOffer[irc.network][channel], self.round[irc.network][channel], self.casesOpened[irc.network][channel]))
        return
 
    @wrap(['inChannel', 'text'])
    def open(self, irc, msg, args, channel, text):
        """<Case>

        Allows a player to pick a case."""

        if channel != msg.args[0]:
            # The command is being called from a private message.
            irc.error(_('This command may only be used in a channel.'))
            return
        if not self.yourCase[irc.network][channel]:
            irc.error('Pick a case first using dond pick')
            return

        if self.player[irc.network][channel] == msg.nick:
            parts = text.split()
            numbers = set()
            for i in parts:
                if self.casesOpened[irc.network][channel] >= self._casesRequired(irc, channel):
                    break
                if self._unopened(irc, channel, i):
                    self.casesOpened[irc.network][channel] += 1
                    self.checkList[irc.network][channel].add(i)
                    case = random.choice(self.boxes[irc.network][channel])
                    self.boxes[irc.network][channel].remove(case)
                    numbers.add('$' + str('{:,}'.format(case)))
            numbers = str(', '.join(numbers))
            if len(numbers) >= 1:
                irc.reply(_('You have opened: %s') % numbers)
            return

            if self.casesOpened[irc.network][channel] >= self._casesRequired(irc, channel) and self.bankOffer[irc.network][channel]:
                irc.reply('The banker is waiting....' )
                return

    @wrap(['channel', 'text'])
    def banker(self, irc, msg, args, channel, text):
        """[<Accept/Decline>]

        Allows the player to Accept or Decline the Banker offer,
        If arguments are given shows the currnet Banker offer.
        """

        if channel != msg.args[0]:
            # The command is being called from a private message.
            irc.error(_('This command may only be used in a channel.'))
            return

        if self.player[irc.network][channel] == msg.nick:
            parts = text.split()
            if parts[0].lower() == 'answer' and not self.bankOffer[irc.network][channel]:
                plist = [0.80, 0.85, 0.85, 0.90, 0.95]
                percent = random.choice(plist)
                boxes = self.boxes[irc.network][channel]
                self.bankOffer[irc.network][channel] = '$' + str('{:,}'.format(int(sum(boxes)/float(len(boxes) * percent))))
                irc.reply(_("The Banker's offer is %s") % self.bankOffer[irc.network][channel])
                return

            if parts[0].lower() == 'accept' or parts[0].lower() == 'a':
                #TODO (stats logic)
                irc.reply(_('You have won %s') % self.bankOffer)
                self._stopGame(irc, msg, silent=True)
                return

            if parts[0].lower() == 'decline' or parts[0].lower() == "d":
                self._nextRound(irc, channel)
                return

            irc.reply(_("The Banker's offer is %s" % self.bankOffer[irc.network][channel]))
            irc.reply('To accept: dond accept', prefixNick=False) #Hard coded Prefix ;( 
            irc.reply('To decline: dond decline', prefixNick=False)
            return

    @wrap(['channel'])
    def status(self, irc, msg, args, channel):
        """[<channel>]

        Shows the current status of the game in <channel>, if one is running.
        <channel> is only required if the message isn't sent in the channel
        itself.
        """

        if self.player[irc.network][channel]:
            irc.reply(_('There is currently an active game in %s started by %s.') %
                      (channel, self.player[irc.network][channel]))
        else:
            irc.reply(_('No game is currently running in %s.') % channel)

    @wrap([getopts({'force': ''}), 'inChannel'])
    def stop(self, irc, msg, args, force, channel):
        """[--force] [<channel>]

        Stops the game currently in progress in this channel. You may only stop
        the game if you are playing. Admins may forcibly stop a game using the
        --force flag; this also works from a private message. <channel> is only
        required if the message isn't sent in the channel itself.
        """

        cap = ircdb.makeChannelCapability(channel, 'op')

        isOp = (irc.state.channels[channel].isOp(msg.nick) or
                ircdb.checkCapability(msg.prefix, cap))

        if self.player[irc.network][channel] is None:
            irc.error(_('No game is currently running in %s.' % channel))
            return

        if force:
            if isOp:
                self._stopGame(irc, msg, channel=channel, forced=msg.nick)
            else:
                irc.errorNoCapability(msg.prefix, 'admin')

            return

        if channel != msg.args[0]:
            # The command is being called from a private message.
            irc.error(_('This command may only be used in a channel.'))
            return

        if self.player[irc.network][channel] == msg.nick:
            self._stopGame(irc, msg)
        else:
            irc.error(_('Only %s may stop the game. Admins may use the '
                        '--force flag to forcibly stop the game.') %
                      self.player[irc.network][channel])
            return


Class = DOND


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
