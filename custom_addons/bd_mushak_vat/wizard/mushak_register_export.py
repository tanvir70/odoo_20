# -*- coding: utf-8 -*-
import base64
import io
from datetime import date
from dateutil.relativedelta import relativedelta
import xlsxwriter

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class MushakRegisterExport(models.TransientModel):
    _name = 'mushak.register.export'
    _description = 'Export Statutory Mushak Registers'

    register_type = fields.Selection(
        selection=[
            ('6.1', 'Mushak 6.1 (Purchase Register / ক্রয় হিসাব পুস্তক)'),
            ('6.2', 'Mushak 6.2 (Sales Register / বিক্রয় হিসাব পুস্তক)'),
        ],
        string='Register Type',
        required=True,
        default=lambda self: self.env.context.get('default_register_type', '6.2'),
    )
    date_from = fields.Date(
        string='From Date',
        required=True,
        default=lambda self: date.today().replace(day=1) - relativedelta(months=1),
    )
    date_to = fields.Date(
        string='To Date',
        required=True,
        default=lambda self: date.today().replace(day=1) - relativedelta(days=1),
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
    )
    include_cancelled = fields.Boolean(
        string='Include Cancelled Challans',
        default=True,
        help='Include cancelled invoices with 0 amount to maintain unbroken statutory sequence trail.',
    )

    def action_view_on_screen(self):
        """Open the register records directly in on-screen list and pivot view."""
        self.ensure_one()
        domain = [
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]
        if self.register_type == '6.1':
            action = self.env['ir.actions.act_window']._for_xml_id('bd_mushak_vat.action_mushak_register_61')
            action['domain'] = domain
            action['display_name'] = _("Mushak 6.1 Purchase Register (%s to %s)") % (self.date_from, self.date_to)
            return action
        else:
            if not self.include_cancelled:
                domain.append(('state', '=', 'posted'))
            action = self.env['ir.actions.act_window']._for_xml_id('bd_mushak_vat.action_mushak_register_62')
            action['domain'] = domain
            action['display_name'] = _("Mushak 6.2 Sales Register (%s to %s)") % (self.date_from, self.date_to)
            return action

    def action_export_xlsx(self):
        """Generate and download statutory register formatted in Excel."""
        self.ensure_one()
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Register')

        # Styles
        title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})
        subtitle_format = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'center'})
        meta_format = workbook.add_format({'font_size': 10, 'align': 'center'})
        header_format = workbook.add_format({
            'bold': True, 'bg_color': '#D9E1F2', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'text_wrap': True
        })
        cell_format = workbook.add_format({'border': 1, 'font_size': 10})
        num_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00', 'font_size': 10})
        total_format = workbook.add_format({'bold': True, 'border': 1, 'num_format': '#,##0.00', 'bg_color': '#F2F2F2'})
        total_label_format = workbook.add_format({'bold': True, 'border': 1, 'align': 'right', 'bg_color': '#F2F2F2'})

        domain = [
            ('company_id', '=', self.company_id.id),
            ('invoice_date', '>=', self.date_from),
            ('invoice_date', '<=', self.date_to),
        ]

        if self.register_type == '6.1':
            records = self.env['mushak.register.purchase'].search(domain)
            title = "ক্রয় হিসাব পুস্তক (মূসক-৬.১)"
            sub_title = "Purchase Register (Mushak 6.1) [Rule 40(1)]"
            headers = [
                'Sl (ক্রমিক)', 'Date (তারিখ)', 'Bill No (বিল নং)', 'Supplier Name (সরবরাহকারী)',
                'Supplier BIN (বিআইএন)', 'Supplier Address (ঠিকানা)', 'Supplier Challan No (চালান নং)',
                'Challan Date (চালান তারিখ)', 'Description (বিবরণ)', 'HS Code (এইচএস)',
                'Quantity (পরিমাণ)', 'Unit (একক)', 'Value Excl. Tax (মূল্য)', 'SD (সম্পূরক শুল্ক)',
                'VAT (মূসক)', 'Total (সর্বমোট)', 'Input Credit (রেয়াতযোগ্য)'
            ]
        else:
            if not self.include_cancelled:
                domain.append(('state', '=', 'posted'))
            records = self.env['mushak.register.sales'].search(domain)
            title = "বিক্রয় হিসাব পুস্তক (মূসক-৬.২)"
            sub_title = "Sales Register (Mushak 6.2) [Rule 40(1)]"
            headers = [
                'Sl (ক্রমিক)', 'Date (তারিখ)', 'Challan No (চালান নং)', 'Type (ধরণ)',
                'Issue Datetime (ইস্যুর সময়)', 'Buyer Name (ক্রেতার নাম)', 'Buyer BIN (ক্রেতার বিআইএন)',
                'Buyer Address (ঠিকানা)', 'Description (পণ্য/সেবা)', 'HS Code (এইচএস)',
                'Quantity (পরিমাণ)', 'Unit (একক)', 'Value Excl. Tax (মূল্য)', 'SD (সম্পূরক শুল্ক)',
                'VAT (মূসক)', 'Total (সর্বমোট)', 'Status (অবস্থা)'
            ]

        # Write Title Block
        worksheet.merge_range(0, 0, 0, len(headers) - 1, "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার - জাতীয় রাজস্ব বোর্ড", subtitle_format)
        worksheet.merge_range(1, 0, 1, len(headers) - 1, f"{title} - {sub_title}", title_format)
        worksheet.merge_range(2, 0, 2, len(headers) - 1, f"প্রতিষ্ঠান: {self.company_id.name} | বিআইএন: {self.company_id.mushak_bin or 'N/A'}", subtitle_format)
        worksheet.merge_range(3, 0, 3, len(headers) - 1, f"কর মেয়াদ / সময়কাল: {self.date_from} হতে {self.date_to}", meta_format)

        # Write Column Headers
        row = 5
        for col, h in enumerate(headers):
            worksheet.write(row, col, h, header_format)
        worksheet.set_row(row, 28)

        # Freeze Panes below headers
        worksheet.freeze_panes(row + 1, 0)

        # Populate Data
        row += 1
        start_data_row = row + 1  # 1-indexed for excel formula

        for idx, rec in enumerate(records, start=1):
            if self.register_type == '6.1':
                worksheet.write(row, 0, idx, cell_format)
                worksheet.write(row, 1, str(rec.invoice_date or ''), cell_format)
                worksheet.write(row, 2, rec.move_id.name or '', cell_format)
                worksheet.write(row, 3, rec.partner_name or '', cell_format)
                worksheet.write(row, 4, rec.partner_bin or '', cell_format)
                worksheet.write(row, 5, rec.partner_address or '', cell_format)
                worksheet.write(row, 6, rec.supplier_challan_number or '', cell_format)
                worksheet.write(row, 7, str(rec.supplier_challan_date or ''), cell_format)
                worksheet.write(row, 8, rec.product_name or '', cell_format)
                worksheet.write(row, 9, rec.hs_code or '', cell_format)
                worksheet.write(row, 10, rec.quantity, num_format)
                worksheet.write(row, 11, rec.uom_name or '', cell_format)
                worksheet.write(row, 12, rec.value_excl_tax, num_format)
                worksheet.write(row, 13, rec.sd_amount, num_format)
                worksheet.write(row, 14, rec.vat_amount, num_format)
                worksheet.write(row, 15, rec.total_value, num_format)
                worksheet.write(row, 16, 'Yes' if rec.is_input_vat_claimable else 'No', cell_format)
            else:
                worksheet.write(row, 0, idx, cell_format)
                worksheet.write(row, 1, str(rec.invoice_date or ''), cell_format)
                worksheet.write(row, 2, rec.mushak_number or '', cell_format)
                worksheet.write(row, 3, rec.mushak_form or '', cell_format)
                worksheet.write(row, 4, str(rec.issue_datetime or ''), cell_format)
                worksheet.write(row, 5, rec.partner_name or '', cell_format)
                worksheet.write(row, 6, rec.partner_bin or '', cell_format)
                worksheet.write(row, 7, rec.partner_address or '', cell_format)
                worksheet.write(row, 8, rec.product_name or '', cell_format)
                worksheet.write(row, 9, rec.hs_code or '', cell_format)
                worksheet.write(row, 10, rec.quantity, num_format)
                worksheet.write(row, 11, rec.uom_name or '', cell_format)
                worksheet.write(row, 12, rec.value_excl_tax, num_format)
                worksheet.write(row, 13, rec.sd_amount, num_format)
                worksheet.write(row, 14, rec.vat_amount, num_format)
                worksheet.write(row, 15, rec.total_value, num_format)
                worksheet.write(row, 16, rec.state or '', cell_format)
            row += 1

        end_data_row = row  # 1-indexed

        # Write Totals Row
        if len(records) > 0:
            worksheet.write(row, 0, '', total_label_format)
            worksheet.merge_range(row, 0, row, 9, "সর্বমোট (Total):", total_label_format)
            # Quantity total
            worksheet.write_formula(row, 10, f"=SUM(K{start_data_row}:K{end_data_row})", total_format)
            worksheet.write(row, 11, '', total_format)
            # Value excl tax
            worksheet.write_formula(row, 12, f"=SUM(M{start_data_row}:M{end_data_row})", total_format)
            # SD
            worksheet.write_formula(row, 13, f"=SUM(N{start_data_row}:N{end_data_row})", total_format)
            # VAT
            worksheet.write_formula(row, 14, f"=SUM(O{start_data_row}:O{end_data_row})", total_format)
            # Total value
            worksheet.write_formula(row, 15, f"=SUM(P{start_data_row}:P{end_data_row})", total_format)
            worksheet.write(row, 16, '', total_format)

        # Autofit column widths
        worksheet.set_column(0, 0, 8)
        worksheet.set_column(1, 1, 12)
        worksheet.set_column(2, 2, 16)
        worksheet.set_column(3, 3, 24)
        worksheet.set_column(4, 4, 18)
        worksheet.set_column(5, 5, 26)
        worksheet.set_column(6, 6, 16)
        worksheet.set_column(7, 7, 14)
        worksheet.set_column(8, 8, 25)
        worksheet.set_column(9, 9, 12)
        worksheet.set_column(10, 10, 10)
        worksheet.set_column(11, 11, 8)
        worksheet.set_column(12, 15, 14)
        worksheet.set_column(16, 16, 12)

        workbook.close()
        output.seek(0)
        file_data = output.read()
        output.close()

        file_name = f"Mushak_{self.register_type}_{self.date_from}_to_{self.date_to}.xlsx"
        attachment = self.env['ir.attachment'].create({
            'name': file_name,
            'type': 'binary',
            'datas': base64.b64encode(file_data),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'res_model': self._name,
            'res_id': self.id,
        })

        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'self',
        }
