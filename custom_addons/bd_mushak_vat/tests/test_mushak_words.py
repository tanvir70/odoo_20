# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase


class TestMushakWords(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Converter = cls.env['mushak.amount.words']

    def test_english_south_asian_words(self):
        """Test South-Asian grouping: Lakh, Crore, Thousand, Hundred."""
        self.assertEqual(
            self.Converter.to_english(0),
            'Zero Taka Only'
        )
        self.assertEqual(
            self.Converter.to_english(1),
            'One Taka Only'
        )
        self.assertEqual(
            self.Converter.to_english(99),
            'Ninety-Nine Taka Only'
        )
        self.assertEqual(
            self.Converter.to_english(100),
            'One Hundred Taka Only'
        )
        self.assertEqual(
            self.Converter.to_english(172500),
            'One Lakh Seventy-Two Thousand Five Hundred Taka Only'
        )
        self.assertEqual(
            self.Converter.to_english(12345678.50),
            'One Crore Twenty-Three Lakh Forty-Five Thousand Six Hundred Seventy-Eight Taka and Fifty Paisa Only'
        )

    def test_bangla_amount_in_words(self):
        """Test Bengali words with কোটি, লক্ষ, হাজার, শত."""
        self.assertEqual(
            self.Converter.to_bangla(0),
            'শূন্য টাকা মাত্র'
        )
        self.assertEqual(
            self.Converter.to_bangla(1),
            'এক টাকা মাত্র'
        )
        self.assertEqual(
            self.Converter.to_bangla(99),
            'নিরানব্বই টাকা মাত্র'
        )
        self.assertEqual(
            self.Converter.to_bangla(172500),
            'এক লক্ষ বাহাত্তর হাজার পাঁচ শত টাকা মাত্র'
        )
        self.assertEqual(
            self.Converter.to_bangla(12345678.50),
            'এক কোটি তেইশ লক্ষ পঁয়তাল্লিশ হাজার ছয় শত আটাত্তর টাকা পঞ্চাশ পয়সা মাত্র'
        )

    def test_to_bn_digits(self):
        """Test ASCII to Bengali digit conversion."""
        self.assertEqual(self.Converter.to_bn_digits('12,345.50'), '১২,৩৪৫.৫০')
        self.assertEqual(self.Converter.to_bn_digits('01712-345678'), '০১৭১২-৩৪৫৬৭৮')
