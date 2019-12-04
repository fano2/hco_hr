# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

import odoo.addons.convert.convert as conv

STATE_INVOICE = [
    ("draft", "Brouillon"),
    ("done", "Validé"),
    ("cancel", "Annulé")
]

class HrInvoice(models.Model):
    _name = "hr.invoice"
    _description = "Facture RH"
    
    @api.one
    @api.depends("hr_invoice_line_ids", "amount_other")
    def _compute_total(self):
        """Compute Total Amount """
        self.wage_net = sum(l.wage_net for l in self.hr_invoice_line_ids )
        self.wage_brut = sum(l.wage_brut for l in self.hr_invoice_line_ids )
        self.amount_cnaps = sum(l.amount_cnaps for l in self.hr_invoice_line_ids )
        self.amount_medgest = sum(l.amount_medgest for l in self.hr_invoice_line_ids )
        self.amount_ostie = sum(l.amount_ostie for l in self.hr_invoice_line_ids )
        self.irsa = sum(l.irsa for l in self.hr_invoice_line_ids )
        self.thirteen_month = sum(l.thirteen_month for l in self.hr_invoice_line_ids )
        self.amount_HT = self.wage_net + self.amount_cnaps + self.amount_medgest + \
                         self.amount_ostie + self.irsa + self.thirteen_month + self.amount_other
    
    @api.one
    @api.depends("wage_brut", "taux_commission")
    def _compute_commission(self):
        """ Compute total amoount comission """
        self.amount_comission = self.taux_commission / 100 * self.wage_brut
    
    @api.one
    @api.depends("amount_HT", "taxe_id")
    def _compute_total_taxe(self):
        """ Compute total taxe """
        taxes = self.taxe_id.compute_all(self.amount_HT, self.currency_id, 1, product=None, partner=None)
        self.update({
            'amount_taxe': taxes['total_included'] - taxes['total_excluded'],
            'amount_TTC': taxes['total_included']
        })
        
    @api.depends('amount_TTC')
    def amount_total_in_text(self):
        """Convert Total to Text"""
        for inv in self:
            inv.amount_in_text = conv.amount_to_text_mg(inv.amount_TTC , inv.currency_id.name)
    
    name = fields.Char("Reference", default="Nouveau" )
    state = fields.Selection(STATE_INVOICE, "State", default="draft")
    wage_net = fields.Monetary("Total Salaire Net", compute="_compute_total")
    wage_brut = fields.Monetary("Total Salaire BRUT", compute="_compute_total")
    amount_cnaps = fields.Monetary("Total CNAPS ", compute="_compute_total")
    amount_medgest = fields.Monetary("Total MEDGEST", compute="_compute_total")
    amount_ostie = fields.Monetary("Total OSTIE", compute="_compute_total")
    irsa = fields.Monetary("Total IRSA", compute="_compute_total")
    thirteen_month = fields.Monetary("13 ème Mois", compute="_compute_total")
    taux_commission = fields.Float("Taux Comission")
    amount_comission = fields.Monetary("Comission", compute="_compute_commission")
    designation = fields.Char("Designation")
    designation_other = fields.Char(" Autre Designation")
    amount_other = fields.Monetary("Montant autre")
    amount_HT = fields.Monetary("Montant HT", compute="_compute_total")
    taxe_id = fields.Many2one('account.tax', string='Taxe', domain=['|', ('active', '=', False), ('active', '=', True)])
    amount_taxe = fields.Monetary("TVA", compute="_compute_total_taxe")
    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms')
    amount_TTC = fields.Monetary("Montant TTC", compute="_compute_total_taxe")
    amount_in_text = fields.Char("Montant en Texte", compute='amount_total_in_text')
    currency_id = fields.Many2one('res.currency', 'Devise',
        default=lambda self: self.env.user.company_id.currency_id.id)
    hr_invoice_line_ids = fields.One2many("hr.invoice.line", "hr_invoice_id", "Lignes Factures")
    partner_id = fields.Many2one("res.partner", "Client", domain=[('customer', '=', True)])
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'Nouveau') == 'Nouveau':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.invoice') or 'Nouveau'
        res = super(HrInvoice, self).create(vals)
        return res
    
    @api.one
    def action_done(self):
        if self.state == 'draft':
            self.state = 'done'
            
    @api.one
    def action_cancel(self):
        if self.state == 'done':
            self.state = 'cancel'
    
    @api.multi
    def export_invoice(self):
        """ Export Invoice """
        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': 'web/binary/donwload_hr_invoice?id_invoice=%s' % (self[0].id)
        }
    

class HrInvoiceLine(models.Model):
    _name = "hr.invoice.line"
    _description = " Ligne dans Facture RH"

    employee_id = fields.Many2one("hr.employee", string="Employé", readonly=True)
    wage_net = fields.Monetary("Salaire Net", readonly=True)
    wage_brut = fields.Monetary("Salaire BRUT", readonly=True)
    amount_cnaps = fields.Monetary("CNAPS ", readonly=True)
    amount_medgest = fields.Monetary("MEDGEST", readonly=True)
    amount_ostie = fields.Monetary("OSTIE", readonly=True)
    irsa = fields.Monetary("IRSA 20%", readonly=True)
    thirteen_month = fields.Monetary("13 è Mois", readonly=True)
    hr_invoice_id = fields.Many2one("hr.invoice", "Facture RH")
    currency_id = fields.Many2one('res.currency', 'Devise', related="hr_invoice_id.currency_id")
