from openerp.osv import orm
from openerp.tools.translate import _


class StockMove(orm.Model):
    _inherit = 'stock.move'

    def split(self, cr, uid, move_ids, prodlot_names, context=None):
        assert len(move_ids) == 1
        move_id = move_ids[0]
        move = self.browse(cr, uid, move_id, context=context)
        if move.prodlot_id:
            raise orm.except_orm(
                _('Serial split error'),
                _('This move already has a serial number')
            )

        production_obj = self.pool.get('mrp.production')
        production_ids = production_obj.search(
            cr, uid, [('move_lines', 'in', move_ids)]
        )

        new_move_ids = []
        for prodlot in prodlot_names:
            prodlot_id = self.find_or_create_prodlot(
                cr, uid, prodlot, move, context=context
            )
            if move.product_qty == 1.0:
                move.write({'prodlot_id': prodlot_id})
                break
            new_move_defaults = {
                'product_qty': 1,
                'prodlot_id': prodlot_id,
                'state': move.state,
                'product_uom': move.product_uom.id,
            }
            new_move_id = self.copy(
                cr, uid, move.id, new_move_defaults, context=context
            )
            if production_ids:
                production_obj.write(
                    cr, uid, production_ids, {'move_lines': [(4, new_move_id)]}
                )

            new_move_ids.append(new_move_id)
            move.write({'product_qty': move.product_qty - 1})
            move = self.browse(cr, uid, move_id, context=context)
        return new_move_ids

    def find_or_create_prodlot(self, cr, uid, prodlot, move, context=None):
        prodlot_obj = self.pool['stock.production.lot']
        prodlot_id = self.find_prodlot(
            cr, uid, prodlot, move, context=context
        )
        if prodlot_id:
            return prodlot_id
        prodlot_vals = {
            'product_id': move.product_id.id,
            'name': prodlot,
        }
        return prodlot_obj.create(
            cr, uid, prodlot_vals, context=context
        )

    def find_prodlot(self, cr, uid, prodlot, move, context=None):
        prodlot_obj = self.pool['stock.production.lot']
        lot_ids = prodlot_obj.search(
            cr, uid,
            [
                ('name', '=', prodlot),
                ('product_id', '=', move.product_id.id)
            ],
            limit=1,
            context=context
        )
        if not lot_ids:
            return None

        ctx = context.copy()
        ctx['location_id'] = move.location_id.id
        prodlot = self.pool.get('stock.production.lot').browse(
            cr, uid, lot_ids[0], ctx
        )
        return lot_ids[0]
