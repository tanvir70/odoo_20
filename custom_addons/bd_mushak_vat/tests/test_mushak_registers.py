# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests.common import TransactionCase


class TestMushakRegisters(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_bd = cls.env.company
        cls.company_bd.partner_id.write({
            'mushak_bin': '1234567890123',
            'mushak_is_vds_entity': True,
            'mushak_vds_entity_type': 'limited_company',
        })
        cls.customer = cls.env['res.partner'].create({
            'name': 'Beximco Pharma Ltd',
            'mushak_bin': '9876543210123',
        })
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Meghna Imports Ltd',
            'mushak_bin': '4567891230123',
            'mushak_supplier_type': 'importer',
        })

    def test_mushak_register_views_and_export(self):
        """Test SQL views and XLSX export wizard."""
        # 1. Test 6.1 export
        wiz61 = self.env['mushak.register.export'].create({
            'register_type': '6.1',
            'date_from': date(2026, 7, 1),
            'date_to': date(2026, 12, 31),
            'company_id': self.company_bd.id,
        })
        act61 = wiz61.action_export_xlsx()
        self.assertEqual(act61.get('type'), 'ir.actions.act_url')
        self.assertTrue('download=true' in act61.get('url', ''))

        # 2. Test 6.2 export
        wiz62 = self.env['mushak.register.export'].create({
            'register_type': '6.2',
            'date_from': date(2026, 7, 1),
            'date_to': date(2026, 12, 31),
            'company_id': self.company_bd.id,
        })
        act62 = wiz62.action_export_xlsx()
        self.assertEqual(act62.get('type'), 'ir.actions.act_url')
        self.assertTrue('download=true' in act62.get('url', ''))
