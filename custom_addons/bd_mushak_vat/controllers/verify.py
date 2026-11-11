# -*- coding: utf-8 -*-
import json
import re
from odoo import http
from odoo.http import request


TOKEN_REGEX = re.compile(r'^[A-Za-z0-9_-]{43}$')


class MushakVerifyController(http.Controller):

    def _mask_name(self, name):
        """Mask name for public privacy protection (e.g. 'Dhaka Trading Corp' -> 'Dha***')."""
        if not name:
            return 'N/A'
        clean = name.strip()
        if len(clean) <= 3:
            return clean + '***'
        return clean[:3] + '***'

    def _get_document_data(self, token):
        """Locate account.move or mushak.vds.certificate and extract only sanitized public fields."""
        if not token or not TOKEN_REGEX.match(token):
            return None

        # 1. Search account.move (6.3, 6.7, 6.8)
        Move = request.env['account.move'].sudo()
        move = Move.search([('mushak_access_token', '=', token)], limit=1)

        if move:
            # Never verify draft documents
            if move.state == 'draft':
                return None

            form_names = {
                '6.3': 'Mushak 6.3 Tax Invoice (কর চালানপত্র)',
                '6.7': 'Mushak 6.7 Credit Note (ক্রেডিট নোট)',
                '6.8': 'Mushak 6.8 Debit Note (ডেবিট নোট)',
            }
            doc_type = form_names.get(move.mushak_form, 'Mushak Document')
            status = 'Cancelled' if move.state == 'cancel' else 'Valid / Authenticated'

            total_val = sum(move.invoice_line_ids.mapped('mushak_value_excl_tax_company_curr'))
            total_sd = sum(move.invoice_line_ids.mapped('mushak_sd_amount_company_curr'))
            total_vat = sum(move.invoice_line_ids.mapped('mushak_vat_amount_company_curr'))
            grand_total = total_val + total_sd + total_vat

            return {
                'found': True,
                'document_type': doc_type,
                'document_number': move.mushak_number or move.name,
                'issue_datetime': str(move.mushak_issue_datetime or move.invoice_date or ''),
                'supplier_name': move.company_id.name,
                'supplier_bin': move.company_id.mushak_bin or 'N/A',
                'buyer_name_masked': self._mask_name(move.partner_id.name),
                'buyer_bin': move.partner_id.mushak_bin or 'Unregistered / N/A',
                'currency': 'BDT',
                'total_value': total_val,
                'total_sd': total_sd,
                'total_vat': total_vat,
                'grand_total': grand_total,
                'status': status,
                'is_valid': move.state == 'posted',
            }

        # 2. Search mushak.vds.certificate (6.6)
        Cert = request.env['mushak.vds.certificate'].sudo()
        cert = Cert.search([('mushak_access_token', '=', token)], limit=1)

        if cert:
            if cert.state == 'draft':
                return None

            status = 'Cancelled' if cert.state == 'cancel' else 'Valid / Authenticated'
            supplier = cert.partner_id if cert.direction == 'issued' else cert.company_id.partner_id
            withholder = cert.company_id if cert.direction == 'issued' else cert.partner_id

            return {
                'found': True,
                'document_type': 'Mushak 6.6 VDS Certificate (উৎসে মূসক কর্তন সনদপত্র)',
                'document_number': cert.name or 'N/A',
                'issue_datetime': str(cert.date or ''),
                'supplier_name': supplier.name,
                'supplier_bin': supplier.mushak_bin or 'N/A',
                'buyer_name_masked': self._mask_name(withholder.name),
                'buyer_bin': withholder.mushak_bin or 'N/A',
                'currency': cert.currency_id.name or 'BDT',
                'total_value': sum(cert.line_ids.mapped('value_excl_vat')),
                'total_sd': 0.0,
                'total_vat': sum(cert.line_ids.mapped('vat_amount')),
                'grand_total': cert.amount_total,
                'status': status,
                'is_valid': cert.state in ('issued', 'received', 'adjusted'),
            }

        return None

    @http.route('/mushak/verify/<string:token>', type='http', auth='public', website=False, csrf=False, sitemap=False)
    def verify_document_html(self, token, **kwargs):
        data = self._get_document_data(token)
        response = request.render('bd_mushak_vat.verify_page', {'data': data})
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        if not data:
            response.status_code = 404
        return response

    @http.route('/mushak/verify/<string:token>.json', type='http', auth='public', website=False, csrf=False, sitemap=False)
    def verify_document_json(self, token, **kwargs):
        data = self._get_document_data(token)
        if not data:
            res = json.dumps({'error': 'No statutory document found', 'status': 404})
            response = request.make_response(res, [('Content-Type', 'application/json')])
            response.status_code = 404
        else:
            res = json.dumps(data)
            response = request.make_response(res, [('Content-Type', 'application/json')])
        response.headers['X-Robots-Tag'] = 'noindex, nofollow'
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
        return response
