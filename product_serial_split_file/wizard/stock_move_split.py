# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Akretion (http://www.akretion.com)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import base64

from openerp.osv import orm, fields


class StockMoveSplit(orm.TransientModel):
    _inherit = "stock.move.split"

    _columns = {
        'prodlot_file': fields.binary(
            'Serial Numbers File',
            help="The serial numbers file should be a text file with one line "
            "per serial number (all for the same product)."),
    }

    def split(self, cr, uid, ids, move_ids, context=None):
        new_move = []
        for move_split in self.browse(cr, uid, ids, context=context):
            if move_split.prodlot_file:
                new_move += self.split_from_file(
                    cr, uid, move_split, context=context
                )
        new_move += super(StockMoveSplit, self).split(
            cr, uid, ids, move_ids, context=context
        )
        production_obj = self.pool.get('mrp.production')
        production_ids = production_obj.search(
            cr, uid, [('move_lines', 'in', move_ids)]
        )
        production_obj.write(
            cr, uid, production_ids, {'move_lines': [(4, m) for m in new_move]}
        )
        return new_move

    def split_from_file(self, cr, uid, move_split, context=None):
        move_obj = self.pool['stock.move']

        prodlots = base64.decodestring(move_split.prodlot_file).split('\n')
        prodlot_seq = [prodlot for prodlot in prodlots if prodlot]

        move_ids = context.get('active_ids')
        assert len(move_ids) == 1
        move = move_obj.browse(cr, uid, move_ids, context=context)[0]
        return move.split(prodlot_seq)
