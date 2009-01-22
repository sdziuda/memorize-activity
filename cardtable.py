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

import gtk
import pygtk
import pango
import svgcard
import os
import time
import math
import gc
from gobject import SIGNAL_RUN_FIRST, TYPE_PYOBJECT

import theme

class CardTable(gtk.EventBox):
  
    __gsignals__ = {
        'card-flipped': (SIGNAL_RUN_FIRST, None, [int, TYPE_PYOBJECT]), 
        'card-highlighted': (SIGNAL_RUN_FIRST, None, [int, TYPE_PYOBJECT]), 
        }

    def __init__(self):
        gtk.EventBox.__init__(self)
        self.data = None
        self.cards_data = None
        self._workspace_size = 0

        # set request size to 100x100 to skip first time sizing in _allocate_cb
        self.set_size_request(100, 100)
        self.connect('size-allocate', self._allocate_cb)
        
        # Set table settings
        self.modify_bg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#000000'))
        self.table = gtk.Table()
        self.table.grab_focus()
        self.table.set_flags(gtk.CAN_FOCUS)
        self.table.set_flags(gtk.CAN_DEFAULT)
        self.table.set_row_spacings(theme.CARD_PAD)
        self.table.set_col_spacings(theme.CARD_PAD)
        self.table.set_border_width(theme.CARD_PAD)
        self.table.set_resize_mode(gtk.RESIZE_IMMEDIATE)
        self.set_property('child', self.table)
        self.load_message = gtk.Label('Loading Game')
        self.load_message.modify_fg(gtk.STATE_NORMAL, gtk.gdk.color_parse('#ffffff'))
        self.load_message.modify_font(pango.FontDescription("10"))
        self.load_message.show()
        self.first_load = True
        self.load_mode = False
        self.dict = None
        self.show_all()

    def _allocate_cb(self, widget, allocation):
        size = allocation.height
        if size == 100:
            # skip first time sizing
            return
        if self._workspace_size == 0:
            # do it once
            self.set_size_request(size, size)
            self._workspace_size = size
            self.load_game(None, self.data, self.cards_data)
        
    def load_game(self, widget, data, grid):
        self.data = data
        self.cards_data = grid

        if self._workspace_size == 0:
            # widow is not allocated, thus postpone loading
            return

        self.size = int(math.ceil(math.sqrt(len(grid))))
        if self.size < 4:
            self.size = 4
        self.table.resize(self.size, self.size)
        self.card_size = self.get_card_size(self.size)
        self.cards = {}
        self.cd2id = {}
        self.id2cd = {}
        self.dict = {}
        self.selected_card = [0, 0]
        self.flipped_card = -1
        self.table_positions = {}
        
        # Build the table
        if data['divided']=='1':
            text1 = str(self.data.get('face1', ''))
            text2 = str(self.data.get('face2', ''))
        else:
            text1 = str(self.data.get('face', ''))
            text2 = str(self.data.get('face', ''))
        
        x = 0
        y = 0
        id = 0
        
        for card in self.cards_data:        
            if card.get('img', None):
                jpg = os.path.join(self.data['pathimg'], card['img'])
            else:
                jpg = None
            props = {}
            props['front_text']= {'card_text':card.get('char', '')}
                    
            if card['ab']== 'a':
                props['back_text']= {'card_text':text1}
            elif card['ab']== 'b':
                props['back_text']= {'card_text':text2}
            
            align = self.data.get('align', '1')
            card = svgcard.SvgCard(id, props, jpg, self.card_size, align)
            card.connect('enter-notify-event', self.mouse_event, [x, y])
            card.connect("button-press-event", self.flip_card_mouse, id)
            self.table_positions[(x, y)]=1
            self.cd2id[card] = id
            self.id2cd[id] = card
            self.cards[(x, y)] = card
            self.dict[id] = (x, y)            
            self.table.attach(card, x, x+1, y, y+1)
         
            x += 1
            if x == self.size:
                x = 0
                y +=1
            id += 1
        self.first_load = False
        if self.load_mode:
            self._set_load_mode(False)
        self.show_all()
        gc.collect()
            
    def change_game(self, widget, data, grid):
        if not self.first_load:
            for card in self.cards.values():
                self.table.remove(card)
                del card
        gc.collect()
        self.load_game(None, data, grid)
    
    def get_card_size(self, size_table):
        x = self._workspace_size/size_table - theme.CARD_PAD*2
        return x
        
    def mouse_event(self, widget, event, coord):
        #self.table.grab_focus()
        card = self.cards[coord[0], coord[1]]
        id = self.cd2id.get(card)
        self.emit('card-highlighted', id, True)
        self.selected_card = (coord[0], coord[1])
            
    def key_press_event(self, widget, event):
        #self.table.grab_focus()
        x= self.selected_card[0]
        y= self.selected_card[1]
        
        if event.keyval in (gtk.keysyms.Left, gtk.keysyms.KP_Left):
            if self.table_positions.has_key((x-1, y)):
                card = self.cards[x-1, y]
                id = self.cd2id.get(card)
                self.emit('card-highlighted', id, False)
        
        elif event.keyval in (gtk.keysyms.Right, gtk.keysyms.KP_Right):
            if self.table_positions.has_key((x+1, y)):
                card = self.cards[x+1, y]
                id = self.cd2id.get(card)
                self.emit('card-highlighted', id, False)
        
        elif event.keyval in (gtk.keysyms.Up, gtk.keysyms.KP_Up):
            if self.table_positions.has_key((x, y-1)):
                card = self.cards[x, y-1]
                id = self.cd2id.get(card)
                self.emit('card-highlighted', id, False)
        
        elif event.keyval in (gtk.keysyms.Down, gtk.keysyms.KP_Down):
            if self.table_positions.has_key((x, y+1)):
                card = self.cards[x, y+1]
                id = self.cd2id.get(card)
                self.emit('card-highlighted', id, False)
        
        elif event.keyval in (gtk.keysyms.space, gtk.keysyms.KP_Page_Down):
            card = self.cards[x, y]
            self.card_flipped(card)
    
    def flip_card_mouse(self, widget, event, id):
        position = self.dict[id]
        card = self.cards[position]
        self.card_flipped(card)
        
    def card_flipped(self, card):
        if not card.is_flipped():
            id  = self.cd2id[card]
            self.emit('card-flipped', id, False)
            
    def set_border(self, widget, id, stroke_color, fill_color):
        self.id2cd[id].set_border(stroke_color, fill_color)

    def flop_card(self, widget, id):
        self.id2cd.get(id).flop()

    def flip_card(self, widget, id):
        self.id2cd.get(id).flip()
        
    def highlight_card(self, widget, id, status):
        if self.dict != None:
            self.selected_card = self.dict.get(id)
            self.id2cd.get(id).set_highlight(status)
        
    def reset(self, widget):        
        for id in self.id2cd.keys():
           self.id2cd[id].reset()
           
    def _set_load_mode(self,mode):
        if mode:
            self.remove(self.table)
            self.set_property('child', self.load_message)
        else:
            self.remove(self.load_message)
            self.set_property('child', self.table)
        self.load_mode = mode
        self.queue_draw()
        while gtk.events_pending():
            gtk.main_iteration() 
        
    def load_msg(self, widget, msg):
        if not self.load_mode:
            self._set_load_mode(True)
        self.load_message.set_text(msg)
        self.queue_draw() 
