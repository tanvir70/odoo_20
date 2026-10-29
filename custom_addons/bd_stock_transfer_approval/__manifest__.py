# -*- coding: utf-8 -*-
{
    'name': 'Stock Transfer Approval',
    'version': '20.0.1.0.0',
    'summary': 'Multi-Warehouse Internal Stock Transfer Requisition & Approval Workflow',
    'category': 'Inventory/Inventory',
    'author': 'Refyne Venture',
    'license': 'LGPL-3',
    'depends': ['stock', 'mail'],
    'data': [
        'security/security_groups.xml',
        'security/ir.access.csv',
        'data/sequence_data.xml',
        'views/transfer_request_views.xml',
        'views/stock_picking_views.xml',
        'wizards/transfer_reject_wizard_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
