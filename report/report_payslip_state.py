# -*- coding:utf-8 -*-

from openerp import api, models, fields, tools

class HrPayslipState(models.Model):
    _name = "hr.payslip.state"
    _description = "Etat de paie"
    _auto = False

    employee_id = fields.Many2one("hr.employee", string="Employé", readonly=True)
    wage_net = fields.Float("Salaire Net", readonly=True)
    wage_brut = fields.Float("Salaire Brut", readonly=True)
    cnaps_emp = fields.Float("CNAPS Employé", readonly=True)
    cnaps_pat = fields.Float("CNAPS Patronal", readonly=True)
    medgest_emp = fields.Float("MEDGEST Employé", readonly=True)
    medgest_pat = fields.Float("MEDGEST Patronal", readonly=True)
    ostie_emp = fields.Float("OSTIE Employé", readonly=True)
    ostie_pat = fields.Float("OSTIE Patronal", readonly=True)
    irsa = fields.Float("IRSA 20%", readonly=True)
    thirteen_month = fields.Float("13 ème Mois", readonly=True)
    date_from = fields.Date("Date", readonly=True)

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self._cr, 'hr_payslip_state')
        self._cr.execute("""
            CREATE OR REPLACE VIEW hr_payslip_state AS (
                SELECT
                	p.id,
                    p.date_from as date_from,
                    emp.id as employee_id,
                    plnet.total as wage_net,
                    plbrut.total as wage_brut,
                    plcnaps.total as cnaps_emp,
                    plcnaps_pat.total as cnaps_pat,
                    plostie.total as ostie_emp,
                    plostie_pat.total as ostie_pat,
                    plmedgest.total as medgest_emp,
                    plmedgest_pat.total as medgest_pat,
                    plirsa.total as irsa,
                    hc.thirteen_month as thirteen_month
                    FROM hr_payslip p
                    INNER JOIN hr_employee emp on emp.id = p.employee_id
                    INNER JOIN  hr_contract hc on hc.id = p.contract_id
                    LEFT JOIN hr_payslip_line plnet on plnet.slip_id = p.id and plnet.code = 'NETAPAYER'
                    LEFT JOIN hr_payslip_line plbrut on plbrut.slip_id = p.id and plbrut.code = 'SBR'
                    LEFT JOIN hr_payslip_line plcnaps on plcnaps.slip_id = p.id and plcnaps.code = 'CNAPS'
                    LEFT JOIN hr_payslip_line plcnaps_pat on plcnaps_pat.slip_id = p.id and plcnaps_pat.code = 'CNAPS_PAT'
                    LEFT JOIN hr_payslip_line plostie on plostie.slip_id = p.id and plostie.code = 'OSTIE'
                    LEFT JOIN hr_payslip_line plostie_pat on plostie_pat.slip_id = p.id and plostie_pat.code = 'OSTIE_PAT'
                    LEFT JOIN hr_payslip_line plmedgest on plmedgest.slip_id = p.id and plmedgest.code = 'MEDGEST'
                    LEFT JOIN hr_payslip_line plmedgest_pat on plmedgest_pat.slip_id = p.id and plmedgest_pat.code = 'MEDGEST_PAT'
                    LEFT JOIN hr_payslip_line plirsa on plirsa.slip_id = p.id and plirsa.code = 'IRSA'

            )
        """)
