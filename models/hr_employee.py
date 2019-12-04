# -*- coding:utf-8 -*-

from openerp import models, api, fields


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    num_domicile = fields.Char("Contact Domicile")
    matricule = fields.Char("Matricule")
    indice = fields.Char("Indice")
    num_cnaps = fields.Char("Numero CNAPS")
    nombre_enfant_cnaps = fields.Integer("Nombre d'enfant allouée CNaPS")
    classification = fields.Char("Classification Professsionnelle")
    contract_salary_ids = fields.One2many("hr.contract.salary.history", "employee_id", "Historique des salaires")
    firstname = fields.Char("Prénom")
    street = fields.Char("Rue")
    street2 =  fields.Char("Rue 2")
    city = fields.Char("Ville")
    zip = fields.Char("Code Postal")

    @api.multi
    def name_get(self):
        res = []
        for employee in self:
            name = "%s  %s" % (employee.name or '', employee.firstname or '')
            res.append((employee.id, name))
        return res
