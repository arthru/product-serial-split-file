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

from openerp.osv import orm, fields, osv
from openerp.tools.translate import _


class StockMoveSplit(orm.TransientModel):
    _inherit = "stock.move.split"

    _columns = {
        'prodlot_file': fields.binary(
            'Serial Numbers File',
            help="The serial numbers file should be a text file with one line "
            "per serial number (all for the same product)."),
    }

    def __parent_split(self, cr, uid, ids, move_ids, context=None):
        if context is None:
            context = {}
        assert (context.get('active_model') == 'stock.move',
                'Incorrect use of the stock move split wizard')
        inventory_id = context.get('inventory_id', False)
        inventory_obj = self.pool.get('stock.inventory')
        move_obj = self.pool.get('stock.move')
        new_move = []
        for data in self.browse(cr, uid, ids, context=context):
            for move in move_obj.browse(cr, uid, move_ids, context=context):
                move_qty = move.product_qty
                quantity_rest = move.product_qty
                uos_qty_rest = move.product_uos_qty
                new_move = []
                lines = [l for l in data.line_exist_ids if l]
                lines += [l for l in data.line_ids if l]
                total_move_qty = 0.0
                for line in lines:
                    quantity = line.quantity
                    total_move_qty += quantity
                    if total_move_qty > move_qty:
                        raise osv.except_osv(
                            _('Processing Error!'),
                            _('Serial number quantity %d of %s is larger than '
                              'available quantity (%d)!') % (
                                total_move_qty, move.product_id.name, move_qty
                            )
                        )
                    if quantity <= 0 or move_qty == 0:
                        continue
                    quantity_rest -= quantity
                    uos_qty = quantity / move_qty * move.product_uos_qty
                    uos_qty_rest = (
                        quantity_rest / move_qty * move.product_uos_qty
                    )
                    if quantity_rest < 0:
                        quantity_rest = quantity
                        self.pool.get('stock.move').log(
                            cr, uid, move.id,
                            _('Unable to assign all lots to this move!')
                        )
                        return False
                    default_val = {
                        'product_qty': quantity,
                        'product_uos_qty': uos_qty,
                        'state': move.state
                    }
                    if quantity_rest > 0:
                        current_move = move_obj.copy(
                            cr, uid, move.id, default_val, context=context
                        )
                        if inventory_id and current_move:
                            inventory_obj.write(
                                cr, uid, inventory_id,
                                {'move_ids': [(4, current_move)]},
                                context=context
                            )
                        new_move.append(current_move)

                    if quantity_rest == 0:
                        current_move = move.id
                    prodlot_id = False
                    if line.prodlot_id:
                        prodlot_id = line.prodlot_id.id
                    else:
                        prodlot_id = move_obj.find_or_create_prodlot(
                            cr, uid, line.name, move, context=context
                        )

                    move_obj.write(
                        cr, uid, [current_move],
                        {'prodlot_id': prodlot_id, 'state': move.state}
                    )

                    update_val = {}
                    if quantity_rest > 0:
                        update_val['product_qty'] = quantity_rest
                        update_val['product_uos_qty'] = uos_qty_rest
                        update_val['state'] = move.state
                        move_obj.write(cr, uid, [move.id], update_val)

        return new_move

    def split(self, cr, uid, ids, move_ids, context=None):
        new_move = []
        for move_split in self.browse(cr, uid, ids, context=context):
            if move_split.prodlot_file:
                new_move += self.split_from_file(
                    cr, uid, move_split, context=context
                )
        new_move += self.__parent_split(
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
