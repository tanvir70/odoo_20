# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    mushak_bin = fields.Char(
        related='partner_id.mushak_bin',
        string='Company BIN',
        readonly=False,
        store=True,
        help='13-digit Business Identification Number of this company.',
    )
    mushak_is_vds_entity = fields.Boolean(
        related='partner_id.mushak_is_vds_entity',
        string='Company is Withholding Entity',
        readonly=False,
        store=True,
        help='Check if this company withholds VAT on its vendor payments.',
    )
    mushak_vat_circle = fields.Char(
        string='VAT Circle / Division',
        help='Tax circle, division, or commissionerate to which the company reports.',
    )
    mushak_signatory_id = fields.Many2one(
        comodel_name='res.users',
        string='Default Mushak Signatory',
        help='Authorized person whose name and designation appear on statutory Mushak declarations.',
    )
    mushak_show_bangla_digits = fields.Boolean(
        string='Print Bangla Numerals on Documents',
        default=False,
        help='Enable to print amounts and numbers in Bengali digits (০-৯) on printed Mushak forms.',
    )
    mushak_journal_ids = fields.Many2many(
        comodel_name='account.journal',
        relation='res_company_mushak_journal_rel',
        column1='company_id',
        column2='journal_id',
        string='Mushak-Enabled Sales Journals',
        domain="[('type', '=', 'sale')]",
        help='Sales journals whose customer invoices generate statutory Mushak 6.3 challans.',
    )
    mushak_vds_payable_account_id = fields.Many2one(
        comodel_name='account.account',
        string='VDS Payable Account',
        check_company=True,
        help='Current liability account for VAT withheld by this company from vendor payments.',
    )
    mushak_vds_receivable_account_id = fields.Many2one(
        comodel_name='account.account',
        string='VDS Receivable Account',
        check_company=True,
        help='Current asset account for VAT withheld by customers from invoices pending Mushak 6.6.',
    )
    mushak_vds_include_sd = fields.Boolean(
        string='Include SD in VDS Base',
        default=True,
        help='When enabled, Supplementary Duty is included in the base amount upon which VDS is calculated.',
    )
