# -*- coding: utf-8 -*-
{
    'name': 'Low Stock Alert & Replenishment Monitor',
    'version': '20.0.1.0.0',
    'summary': 'Automated Warehouse-level Low Stock Detection, Severity Classification & Requisition Bridge',
    'category': 'Inventory/Inventory',
    'author': 'Refyne Venture',
    'license': 'LGPL-3',
    'depends': ['stock', 'mail', 'bd_stock_transfer_approval'],
    'data': [
        'security/ir.access.csv',
        'data/sequence_data.xml',
        'data/low_stock_cron.xml',
        'views/low_stock_alert_views.xml',
        'views/product_views.xml',
        'views/menus.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
