# -*- coding:utf-8 -*-

from openerp import models, api, fields


class HrHealthOrganization(models.Model):
    _name = "hr.health.organization"
    
    name = fields.Char("Nom")
    code = fields.Char("Code")
    taux_emp = fields.Float("Taux Employé")
    taux_pat = fields.Float("Taux Patronal")
    
    @api.model
    def create(self, vals):
        res = super(HrHealthOrganization, self).create(vals)
        hr_rule_obj = self.env["hr.salary.rule"]
        code_pat = res.code + "_PAT"
        rule_emp_python = "result = (SBR*contract.hr_health_id.taux_emp/100 if SBR < employee.company_id.plafond_cnaps else employee.company_id.plafond_cnaps*contract.hr_health_id.taux_emp/100 )" 
        rule_pat_python = "result = (SBR*contract.hr_health_id.taux_pat/100 if SBA < employee.company_id.plafond_cnaps else employee.company_id.plafond_cnaps*contract.hr_health_id.taux_pat/100 )" 
        condition_python = "result = contract.hr_health_id.code == '%s'" % (res.code)
        vals_rule_emp = {
            "name": "Retenue " + res.name,
            "sequence": 12, 
            "code": res.code,
            "category_id": self.env.ref("hr_payroll.DED").id,
            "condition_select": "python",
            "condition_python": condition_python,
            "amount_select": "code",
            "amount_python_compute": rule_emp_python
        }
        
        vals_rule_pat = {
            "name": "Charges Patronal " + res.name ,
            "sequence": 50,
            "code": code_pat,
            "category_id": self.env.ref("hco_hr.PATRONAL").id,
            "condition_select": "python",
            "condition_python": condition_python,
            "amount_select": "code",
            "amount_python_compute": rule_pat_python
        }
        
        rule_emp = hr_rule_obj.create(vals_rule_emp)
        rule_pat = hr_rule_obj.create(vals_rule_pat)
        struct_obj = self.env.ref("hco_hr.structure_base_gasy")
        struct_mlg_lobj = self.env.ref("hco_hr.structure_base_malagasy")
        struct_obj.write({'rule_ids': [(4, rule_emp.id, None), (4, rule_pat.id, None)]})
        struct_mlg_lobj.write({'rule_ids': [(4, rule_emp.id, None), (4, rule_pat.id, None)]})
        return res
    