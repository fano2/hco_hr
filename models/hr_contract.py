# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class HrContractSalaryHistory(models.Model):
    _name = "hr.contract.salary.history"
    
    date = fields.Datetime("Date")
    contract_id = fields.Many2one("hr.contract","Contrat")
    employee_id = fields.Many2one("hr.employee", "Employe")
    amount = fields.Float("Montant")
    

class HrContract(models.Model):
    _inherit = "hr.contract"

    @api.multi
    @api.depends("wage")
    def _compute_amount_by_hour(self):
        for rec in self:
            rec.amount_by_hour = rec.wage / 173.33

    amount_by_hour = fields.Float("Montant par Heure", compute="_compute_amount_by_hour")
    thirteen_month = fields.Monetary("13 ème Mois")
    currency_id = fields.Many2one('res.currency', 'Devise', default=lambda self: self.env.user.company_id.currency_id.id)
    hr_health_id = fields.Many2one("hr.health.organization", "Organisme de santé")
    
    @api.model
    def create(self,values):
        res = super(HrContract, self).create(values)
        val_history = {
            "date": fields.Datetime.now(), 
            "contract_id": res.id,
            "employee_id": res.employee_id.id,
            "amount": res.wage
        }
        self.env["hr.contract.salary.history"].create(val_history)
        return res
    
    @api.multi
    def write(self, vals):
        res = super(HrContract, self).write(vals)
        if "wage" in vals: 
            for rec in self:
                val_history = {
                    "date": fields.Datetime.now(), 
                    "contract_id": rec.id,
                    "employee_id": rec.employee_id.id,
                    "amount": vals["wage"]
                }
                self.env["hr.contract.salary.history"].create(val_history)
        return res
