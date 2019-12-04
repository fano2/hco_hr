# -*- coding:utf-8 -*-

from openerp import api, models, fields


class HRSalaryRule(models.Model):
    _inherit = "hr.salary.rule"
    
    is_dynamic = fields.Boolean("Is dynamic Rule ?")
    is_compute_prorata = fields.Boolean("Is compute prorata ?")
    account_id = fields.Many2one("account.account", "Compte")
    
    @api.onchange("is_dynamic")
    def onchange_is_dynamic(self):
        """CHange Amount Select """
        if self.is_dynamic:
            self.amount_select = 'code'

    @api.model
    def create(self, values):
        res = super(HRSalaryRule, self).create(values)
        if res.is_dynamic:
            res.amount_select = 'code'
            res.amount_python_compute = "result = inputs.%s.amount if inputs.%s and inputs.%s.amount else 0" % (res.code, res.code, res.code)
            self.env['hr.rule.input'].create({'code': res.code, 'name': res.name, 'input_id': res.id})
        return res
    
    @api.multi
    def write(self, values):
        res = super(HRSalaryRule, self).write(values)
        if "is_dynamic" in values:
            for rec in self:
                rec.amount_select = 'code'
                rec.amount_python_compute = "result = inputs.%s.amount if inputs.%s and inputs.%s.amount else 0" % (rec.code, rec.code, rec.code)
                rec.input_ids.unlink()
                self.env['hr.rule.input'].create({'code': rec.code, 'name': rec.name, 'input_id': rec.id})
        return res
                
            