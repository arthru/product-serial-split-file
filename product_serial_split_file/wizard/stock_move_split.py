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
from openerp.tools.translate import _


class StockMoveSplit(orm.TransientModel):
    _inherit = "stock.move.split"

    _columns = {
        'prodlot_file': fields.binary(
            'Serial Numbers File',
            help="The serial numbers file should be a text file with one line "
            "per serial number (all for the same product)."),
    }

    def split_lot(self, cr, uid, ids, context=None):
        for move_split in self.browse(cr, uid, ids, context=context):
            if move_split.prodlot_file:
                self.split_from_file(cr, uid, move_split, context=context)
        return super(StockMoveSplit, self).split_lot(
            cr, uid, ids, context=context
        )

    def split_from_file(self, cr, uid, move_split, context=None):
        move_obj = self.pool['stock.move']
        prodlot_obj = self.pool['stock.production.lot']

        prodlots = base64.decodestring(move_split.prodlot_file).split('\n')
        prodlot_seq = [prodlot for prodlot in prodlots if prodlot]

        move_ids = context.get('active_ids')
        assert len(move_ids) == 1
        move = move_obj.browse(cr, uid, move_ids, context=context)[0]
        if move.prodlot_id:
            raise orm.except_orm(_('This move already has a serial number'))
        for prodlot in prodlot_seq:
            if move_split.use_exist:
                prodlot_id = self.find_prodlot(
                    cr, uid, prodlot, move, context=context
                )
            else:
                prodlot_vals = {
                    'product_id': move.product_id.id,
                    'name': prodlot,
                    'company_id': move.company_id.id,
                }
                prodlot_id = prodlot_obj.create(
                    cr, uid, prodlot_vals, context=context
                )
            if move.product_qty == 1.0:
                move.write({'prodlot_id': prodlot_id})
                return
            move_obj.copy(
                cr, uid, move.id,
                {'product_qty': 1, 'prodlot_id': prodlot_id},
                context=context
            )
            move.write(
                {'product_qty': move.product_qty - 1}
            )
            move = move_obj.browse(cr, uid, move_ids, context=context)[0]

    def find_prodlot(self, cr, uid, prodlot, move, context=None):
        prodlot_obj = self.pool['stock.production.lot']
        lot_ids = prodlot_obj.search(
            cr, uid, [('name', '=', prodlot)], limit=1, context=context
        )
        if not lot_ids:
            raise orm.except_orm(
                _('Invalid Serial Number'),
                _('Serial Number %s not found.') % prodlot)

        ctx = context.copy()
        ctx['location_id'] = move.location_id.id
        prodlot = self.pool.get('stock.production.lot').browse(
            cr, uid, lot_ids[0], ctx
        )

        if prodlot.product_id != move.product_id:
            raise orm.except_orm(
                _('Invalid Serial Number'),
                _('Serial Number %s exists but not for product %s.')
                % (prodlot, move.product_id.name)
            )

        return lot_ids[0]
