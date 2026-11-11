# -*- coding: utf-8 -*-
import decimal
from odoo import api, models

BN_DIGITS_MAP = {
    '0': '০', '1': '১', '2': '২', '3': '৩', '4': '৪',
    '5': '৫', '6': '৬', '7': '৭', '8': '৮', '9': '৯',
}

BN_WORDS_0_TO_99 = {
    0: 'শূন্য', 1: 'এক', 2: 'দুই', 3: 'তিন', 4: 'চার', 5: 'পাঁচ',
    6: 'ছয়', 7: 'সাত', 8: 'আট', 9: 'নয়', 10: 'দশ',
    11: 'এগারো', 12: 'বারো', 13: 'তেরো', 14: 'চৌদ্দ', 15: 'পনেরো',
    16: 'ষোলো', 17: 'সতেরো', 18: 'আঠারো', 19: 'উনিশ', 20: 'বিশ',
    21: 'একুশ', 22: 'বাইশ', 23: 'তেইশ', 24: 'চব্বিশ', 25: 'পঁচিশ',
    26: 'ছাব্বিশ', 27: 'সাতাশ', 28: 'আঠাশ', 29: 'উনত্রিশ', 30: 'ত্রিশ',
    31: 'একত্রিশ', 32: 'বত্রিশ', 33: 'তেত্রিশ', 34: 'চৌত্রিশ', 35: 'পঁয়ত্রিশ',
    36: 'ছত্রিশ', 37: 'সাঁইত্রিশ', 38: 'আটত্রিশ', 39: 'উনচল্লিশ', 40: 'চল্লিশ',
    41: 'একচল্লিশ', 42: 'বিয়াল্লিশ', 43: 'তেতাল্লিশ', 44: 'চুয়াল্লিশ', 45: 'পঁয়তাল্লিশ',
    46: 'ছেচল্লিশ', 47: 'সাতচল্লিশ', 48: 'আটচল্লিশ', 49: 'উনপঞ্চাশ', 50: 'পঞ্চাশ',
    51: 'একান্ন', 52: 'বায়ান্ন', 53: 'তিপ্পান্ন', 54: 'চুয়ান্ন', 55: 'পঞ্চান্ন',
    56: 'ছাপ্পান্ন', 57: 'সাতান্ন', 58: 'আটান্ন', 59: 'উনষাট', 60: 'ষাট',
    61: 'একষট্টি', 62: 'বাষট্টি', 63: 'তেষট্টি', 64: 'চৌষট্টি', 65: 'পঁয়ষট্টি',
    66: 'ছেষট্টি', 67: 'সাতষট্টি', 68: 'আটষট্টি', 69: 'উনসত্তর', 70: 'সত্তর',
    71: 'একাত্তর', 72: 'বাহাত্তর', 73: 'তিয়াত্তর', 74: 'চুয়াত্তর', 75: 'পঁচাত্তর',
    76: 'ছিয়াত্তর', 77: 'সাতাত্তর', 78: 'আটাত্তর', 79: 'উনাশি', 80: 'আশি',
    81: 'একাশি', 82: 'বিরাশি', 83: 'তিরাশি', 84: 'চুরাশি', 85: 'পঁচাশি',
    86: 'ছিয়াশি', 87: 'সাতাশি', 88: 'অষ্টআশি', 89: 'ঊননব্বই', 90: 'নব্বই',
    91: 'একানব্বই', 92: 'বানব্বই', 93: 'তিরানব্বই', 94: 'চুরানব্বই', 95: 'পঁচানব্বই',
    96: 'ছিয়ানব্বই', 97: 'সাতানব্বই', 98: 'আটানব্বই', 99: 'নিরানব্বই',
}

EN_ONES = [
    '', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine',
    'Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen',
    'Seventeen', 'Eighteen', 'Nineteen'
]
EN_TENS = [
    '', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety'
]


class MushakAmountWords(models.AbstractModel):
    _name = 'mushak.amount.words'
    _description = 'South Asian / Bangladeshi Amount in Words Converter'

    @api.model
    def to_bn_digits(self, text):
        """Map ASCII 0-9 digits to Bengali ০-৯ digits."""
        if not text:
            return ''
        text_str = str(text)
        return ''.join(BN_DIGITS_MAP.get(ch, ch) for ch in text_str)

    @api.model
    def _en_under_thousand(self, n):
        words = []
        if n >= 100:
            words.append(EN_ONES[n // 100] + ' Hundred')
            n %= 100
        if n >= 20:
            tens = EN_TENS[n // 10]
            unit = EN_ONES[n % 10]
            words.append(f"{tens}-{unit}" if unit else tens)
        elif n > 0:
            words.append(EN_ONES[n])
        return ' '.join(words)

    @api.model
    def to_english(self, amount):
        """Convert decimal number to English South-Asian words (Crore, Lakh, Thousand, Hundred)."""
        if amount is None:
            return ''
        try:
            d = decimal.Decimal(str(amount))
        except (ValueError, decimal.InvalidOperation):
            return ''

        taka = int(abs(d))
        paisa = int(round((abs(d) - taka) * 100))

        if taka == 0:
            taka_words = 'Zero Taka'
        else:
            crore = taka // 10000000
            remainder = taka % 10000000
            lakh = remainder // 100000
            remainder %= 100000
            thousand = remainder // 1000
            remainder %= 1000
            hundred_and_units = remainder

            parts = []
            if crore > 0:
                parts.append(self.to_english(crore).replace(' Taka Only', '').replace(' Taka', '') + ' Crore')
            if lakh > 0:
                parts.append(self._en_under_thousand(lakh) + ' Lakh')
            if thousand > 0:
                parts.append(self._en_under_thousand(thousand) + ' Thousand')
            if hundred_and_units > 0:
                parts.append(self._en_under_thousand(hundred_and_units))

            taka_words = ' '.join(parts) + ' Taka'

        paisa_words = ''
        if paisa > 0:
            paisa_words = ' and ' + self._en_under_thousand(paisa) + ' Paisa'

        return (taka_words + paisa_words + ' Only').strip()

    @api.model
    def _bn_under_thousand(self, n):
        words = []
        hundreds = n // 100
        rem = n % 100
        if hundreds > 0:
            words.append(BN_WORDS_0_TO_99[hundreds] + ' শত')
        if rem > 0:
            words.append(BN_WORDS_0_TO_99[rem])
        return ' '.join(words)

    @api.model
    def to_bangla(self, amount):
        """Convert decimal number to Bengali words with কোটি, লক্ষ, হাজার, শত."""
        if amount is None:
            return ''
        try:
            d = decimal.Decimal(str(amount))
        except (ValueError, decimal.InvalidOperation):
            return ''

        taka = int(abs(d))
        paisa = int(round((abs(d) - taka) * 100))

        if taka == 0:
            taka_words = 'শূন্য টাকা'
        else:
            crore = taka // 10000000
            remainder = taka % 10000000
            lakh = remainder // 100000
            remainder %= 100000
            thousand = remainder // 1000
            remainder %= 1000
            hundred_and_units = remainder

            parts = []
            if crore > 0:
                parts.append(self.to_bangla(crore).replace(' টাকা মাত্র', '').replace(' টাকা', '') + ' কোটি')
            if lakh > 0:
                parts.append(BN_WORDS_0_TO_99[lakh] + ' লক্ষ')
            if thousand > 0:
                parts.append(BN_WORDS_0_TO_99[thousand] + ' হাজার')
            if hundred_and_units > 0:
                parts.append(self._bn_under_thousand(hundred_and_units))

            taka_words = ' '.join(parts) + ' টাকা'

        paisa_words = ''
        if paisa > 0:
            paisa_words = ' ' + BN_WORDS_0_TO_99[paisa] + ' পয়সা'

        return (taka_words + paisa_words + ' মাত্র').strip()
