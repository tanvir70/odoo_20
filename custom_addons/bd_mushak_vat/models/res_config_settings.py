# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    mushak_bin = fields.Char(
        related='company_id.mushak_bin',
        readonly=False,
        string='Company BIN',
    )
    mushak_is_vds_entity = fields.Boolean(
        related='company_id.mushak_is_vds_entity',
        readonly=False,
        string='We are a Withholding Entity',
    )
    mushak_vds_entity_type = fields.Selection(
        related='company_id.mushak_vds_entity_type',
        readonly=False,
        string='Withholding Entity Type',
    )
    mushak_vat_circle = fields.Char(
        related='company_id.mushak_vat_circle',
        readonly=False,
        string='VAT Circle / Division',
    )
    mushak_signatory_id = fields.Many2one(
        related='company_id.mushak_signatory_id',
        readonly=False,
        string='Default Mushak Signatory',
    )
    mushak_show_bangla_digits = fields.Boolean(
        related='company_id.mushak_show_bangla_digits',
        readonly=False,
        string='Show Bangla Numerals on Documents',
    )
    mushak_journal_ids = fields.Many2many(
        related='company_id.mushak_journal_ids',
        readonly=False,
        string='Mushak-Enabled Sales Journals',
    )
    mushak_vds_payable_account_id = fields.Many2one(
        related='company_id.mushak_vds_payable_account_id',
        readonly=False,
        string='VDS Payable Account',
    )
    mushak_vds_receivable_account_id = fields.Many2one(
        related='company_id.mushak_vds_receivable_account_id',
        readonly=False,
        string='VDS Receivable Account',
    )
    mushak_vds_include_sd = fields.Boolean(
        related='company_id.mushak_vds_include_sd',
        readonly=False,
        string='Include SD in VDS Base',
    )
