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

        #Box values
        self.boxes = defaultdict(lambda: defaultdict(str))
        #Which cases are opened
        self.checkList = defaultdict(lambda: defaultdict(str))
        #Choosen case
        self.yourCase = defaultdict(lambda: defaultdict(str))
        #Choosen Case Value
        self.YourCaseValue = defaultdict(lambda: defaultdict(str))

    def _unopened_cases(self, irc, channel):
        numbers = [1, 2, 3, 4 ,5, 6, 7, 8, 9, 10, 11, 12, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26]
        return ", ".join((str(item) for item in numbers if item not in self.checkList[irc.network][channel]))

    def _stopGame(self, irc, msg, channel=None, forced=None):
        channel = channel or msg.args[0]
        del self.player[irc.network][channel]

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

        irc.reply('Welcome to the game of Deal Or No Deal!', prefixNick=True)
        self.player[irc.network][channel] = msg.nick
        self.checkList[irc.network][channel] = {}
        irc.reply(_("Available cases: %s") % self._unopened_cases(irc, channel))

    @wrap(['channel'])
    def status(self, irc, msg, args, channel):
        """[<channel>]

        Shows the current status of the game in <channel>, if one is running.
        <channel> is only required if the message isn't sent in the channel
        itself.
        """

        if self.player[irc.network][channel]:
            irc.reply(_("There is currently an active game in %s started by %s.") %
                      (channel, self.player[irc.network][channel]))
        else:
            irc.reply(_("No game is currently running in %s.") % channel)

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

        if not self.player[irc.network][channel]:
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
