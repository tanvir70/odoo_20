# -*- coding: utf-8 -*-
from datetime import date
from odoo.tests.common import TransactionCase


class TestMushakVds(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_bd = cls.env.company
        cls.company_bd.write({
            'mushak_bin': '1234567890123',
            'mushak_is_vds_entity': True,
        })
        cls.bank_partner = cls.env['res.partner'].create({
            'name': 'Sonali Bank PLC',
            'mushak_bin': '1122334455667',
            'mushak_is_vds_entity': True,
            'mushak_vds_entity_type': 'bank',
        })
        cls.supplier = cls.env['res.partner'].create({
            'name': 'Bashundhara Construction Ltd',
            'mushak_bin': '5544332211009',
            'mushak_supplier_type': 'service_provider',
        })
        cls.rule_s004 = cls.env['mushak.vds.rule'].create({
            'code': 'S004.00',
            'name': 'Construction Contractor Test',
            'applies_to': 'service',
            'vds_rate': 10.0,
            'date_from': date(2025, 7, 1),
        })

    def test_vds_rule_matching(self):
        """Test rule matching by service code and date."""
        matched = self.env['mushak.vds.rule'].match_rule(
            service_code_id=self.rule_s004.id,
            payment_date=date(2026, 8, 1),
            company_id=self.company_bd.id,
        )
        self.assertEqual(matched.id, self.rule_s004.id)

    def test_vds_rule_expired_not_matched(self):
        """A rule with date_to in past is not matched."""
        expired_rule = self.env['mushak.vds.rule'].create({
            'code': 'S999.00',
            'name': 'Old Expired Rule',
            'applies_to': 'service',
            'vds_rate': 7.5,
            'date_from': date(2024, 7, 1),
            'date_to': date(2025, 6, 30),
        })
        matched = self.env['mushak.vds.rule'].match_rule(
            service_code_id=expired_rule.id,
            payment_date=date(2025, 7, 1),
            company_id=self.company_bd.id,
        )
        self.assertFalse(matched)

    def test_mushak_66_certificate_workflow(self):
        """Creating and issuing Mushak 6.6 certificate generates sequence and token."""
        cert = self.env['mushak.vds.certificate'].create({
            'direction': 'issued',
            'partner_id': self.supplier.id,
            'date': date(2026, 8, 10),
            'line_ids': [(0, 0, {
                'challan_number': '2026-000100',
                'value_excl_vat': 100000.0,
                'vat_amount': 15000.0,
                'vds_rate': 10.0,
                'vds_amount': 10000.0,
            })],
        })
        self.assertEqual(cert.amount_total, 10000.0)
        self.assertEqual(cert.state, 'draft')

        cert.action_issue()
        self.assertEqual(cert.state, 'issued')
        self.assertTrue(cert.name)
        self.assertTrue(cert.name.startswith('2026-'))
        self.assertTrue(cert.mushak_access_token)
