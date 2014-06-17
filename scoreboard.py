#    Copyright (C) 2006, 2007, 2008 One Laptop Per Child
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#

import logging

from gi.repository import Gtk
from gi.repository import Gdk

from playerscoreboard import PlayerScoreboard

_logger = logging.getLogger('memorize-activity')


class Scoreboard(Gtk.EventBox):
    def __init__(self):
        Gtk.EventBox.__init__(self)

        self.players = {}
        self.current_buddy = None

        self.vbox = Gtk.VBox(False)

        fill_box = Gtk.EventBox()
        fill_box.modify_bg(Gtk.StateType.NORMAL, Gdk.color_parse('#4c4d4f'))
        fill_box.show()
        self.vbox.pack_end(fill_box, True, True, 0)

        scroll = Gtk.ScrolledWindow()
        scroll.props.shadow_type = Gtk.ShadowType.NONE
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.add_with_viewport(self.vbox)
        scroll.set_border_width(0)
        scroll.get_child().set_property('shadow-type', Gtk.ShadowType.NONE)
        self.add(scroll)
        self.show_all()

    def change_game(self, widget, data, grid):
        for buddy in self.players.keys():
            self.players[buddy].change_game(len(grid))

    def add_buddy(self, widget, buddy, score):
        ### FIXME: this breaks when the body is empty
        nick = buddy.props.nick
        stroke_color, fill_color = buddy.props.color.split(',')
        player = PlayerScoreboard(nick, fill_color, stroke_color, score)
        player.show()
        self.players[buddy] = player
        # remove widgets and add sorted
        for child in self.vbox.get_children():
            self.vbox.remove(child)
        for buddy in sorted(self.players.keys(), key=lambda buddy: buddy.props.nick):
            p = self.players[buddy]
            self.vbox.pack_start(p, False, False, 0)

        if score == -1:
            player.set_wait_mode(True)
        self.show_all()

    def rem_buddy(self, widget, buddy):
        self.vbox.remove(self.players[buddy])
        del self.players[buddy]  # fix for self.players[id]

    def set_selected(self, widget, buddy):
        if self.current_buddy is not None:
            old = self.players[self.current_buddy]
            old.set_selected(False)
        self.current_buddy = buddy
        player = self.players[buddy]
        player.set_selected(True)

    def set_buddy_message(self, widget, buddy, msg):
        self.players[buddy].set_message(msg)

    def increase_score(self, widget, buddy):
        self.players[buddy].increase_score()

    def reset(self, widget):
        for buddy in self.players.keys():
            self.players[buddy].reset()

    def set_wait_mode(self, widget, buddy, status):
        self.players[buddy].set_wait_mode(status)
