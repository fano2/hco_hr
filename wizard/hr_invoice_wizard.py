# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class HrInvoiceWizard(models.TransientModel):
    """
    This Wizard help to create Factures in Invoices 
    """
    
    _name = 'hr.invoice.wizard'
    _description = 'Create wizard based to selected lines'
    
    def get_val_hr_invoice_line(self, state_id):
        """Get values to insert in invoice line"""
        vals = {
            "employee_id" : state_id.employee_id.id,
            "wage_net" : state_id.wage_net,
            "wage_brut" : state_id.wage_brut,
            "amount_cnaps" : state_id.cnaps_emp + state_id.cnaps_pat,
            "amount_medgest" : state_id.medgest_emp + state_id.medgest_pat,
            "amount_ostie" : state_id.ostie_emp + state_id.ostie_pat,
            "irsa" : state_id.irsa,
            "thirteen_month" : state_id.thirteen_month
        }
        return vals
        
    
    @api.multi
    def create_hr_invoice(self):
        context = dict(self._context or {})
        active_ids = context.get('active_ids', []) or []
        hr_invoice_obj = self.env["hr.invoice"]
        hr_invoice = None
        
        vals_invoice_lines = []
        for record in self.env['hr.payslip.state'].browse(active_ids):
            line = self.get_val_hr_invoice_line(record)
            vals_invoice_lines.append(line)
        if vals_invoice_lines:
            lines_val = [(0, 0, l) for l in vals_invoice_lines ]
            hr_invoice = hr_invoice_obj.create({"hr_invoice_line_ids": lines_val})
            
        action = self.env.ref('hco_hr.action_hr_invoice')
        result = action.read()[0]

        
        if len(hr_invoice) == 1:
            res = self.env.ref('hco_hr.hr_invoice_form_view', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = hr_invoice.id or False
        return result
    
