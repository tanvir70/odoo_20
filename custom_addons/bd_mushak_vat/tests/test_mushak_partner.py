# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestMushakPartner(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']

    def test_bin_normalization_and_storage(self):
        """Entering BIN with dashes and spaces should store normalized 13 digits."""
        partner = self.Partner.create({
            'name': 'Test Supplier Ltd',
            'mushak_bin': '0034-5678-90123',
        })
        self.assertEqual(partner.mushak_bin, '0034567890123')

        # Test on write
        partner.write({'mushak_bin': '1122 3344 5566 7'})
        self.assertEqual(partner.mushak_bin, '1122334455667')

    def test_bin_invalid_lengths_raise_error(self):
        """Entering less or more than 13 digits raises ValidationError."""
        # 12 digits
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Invalid 12 Digit Partner',
                'mushak_bin': '123456789012',
            })

        # 14 digits
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Invalid 14 Digit Partner',
                'mushak_bin': '12345678901234',
            })

        # Non-digits only (resulting in empty string is allowed if optional)
        partner = self.Partner.create({
            'name': 'Optional Empty BIN',
            'mushak_bin': False,
        })
        self.assertFalse(partner.mushak_bin)

    def test_commercial_fields_propagation(self):
        """Child contacts inherit commercial partner's BIN and VDS flag."""
        parent = self.Partner.create({
            'name': 'Commercial Parent Bank',
            'is_company': True,
            'mushak_bin': '0011223344556',
            'mushak_is_vds_entity': True,
            'mushak_vds_entity_type': 'bank',
        })

        child = self.Partner.create({
            'name': 'Gulshan Branch',
            'parent_id': parent.id,
            'type': 'contact',
        })

        self.assertEqual(child.mushak_bin, '0011223344556')
        self.assertTrue(child.mushak_is_vds_entity)

    def test_vds_entity_type_mandatory_when_flag_enabled(self):
        """Enabling VDS entity flag without specifying entity type raises ValidationError."""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'Withholding Entity without Type',
                'mushak_is_vds_entity': True,
                'mushak_vds_entity_type': False,
            })

    def test_bin_duplicate_warning(self):
        """Sharing the same BIN across partners computes a non-blocking warning string."""
        partner1 = self.Partner.create({
            'name': 'Head Office',
            'mushak_bin': '9988776655443',
        })
        partner2 = self.Partner.create({
            'name': 'Chittagong Depot',
            'mushak_bin': '9988776655443',
        })
        partner2._compute_mushak_bin_duplicate_warning()
        self.assertTrue(partner2.mushak_bin_duplicate_warning)
        self.assertIn('9988776655443', partner2.mushak_bin_duplicate_warning)
