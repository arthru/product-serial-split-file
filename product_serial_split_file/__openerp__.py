# -*- encoding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Akretion (http://www.akretion.com/)
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

{
    "name": "Product Serial Split with File",
    "summary": "Upload a file to split lot",
    "version": "1.0",
    "author": "Akretion",
    "website": "http://www.akretion.com",
    "depends": [
        "mrp",
        "stock",
    ],
    "category": "Generic Modules/Inventory Control",
    "license": "AGPL-3",
    "description": """
This permits to split a move with serial numbers from a file.
""",
    "demo": [],
    "data": [
        "wizard/stock_move_view.xml",
    ],
    "active": False,
    "installable": True
}
