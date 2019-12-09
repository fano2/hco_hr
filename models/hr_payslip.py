# -*- coding:utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import UserError
from openerp import api, models, fields, tools, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

MODE_PAYMENT = [
    ('espece', u'Espece'),
    ('virement', 'Virement'),
]

CODE_HOURS = ['HS1', 'HS2', 'HS3', 'HS4', 'HSD']


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'


    @api.depends("payslip_hours_ids.subtotal_add_hours")
    def _compute_total_hours(self):
        """ Compute total additionnal hours """
        for rec in self:
            total = sum(l.subtotal_add_hours for l in rec.payslip_hours_ids)
            total_130 = sum(l.amount_hs130 for l in rec.payslip_hours_ids)
            total_150 = sum(l.amount_hs150 for l in rec.payslip_hours_ids)
            rec.amount_add_hours = total
            rec.amount_hours130 = total_130
            rec.amount_hours150 = total_150

    @api.one
    @api.depends("nb_day_base", "nb_day_leave")
    def _compute_rate(self):
        """Compute Rate in Payslip"""
        self.nb_days = self.nb_day_base - self.nb_day_leave
        self.rate = self.nb_days * 100 / self.nb_day_base

    @api.one
    @api.depends("contract_id.date_start", "date_to")
    def _compute_seniority(self):
        """ Compute Seniority at Date Payslip """
        date_start = fields.Date.from_string(self.contract_id.date_start)
        date_end = fields.Date.from_string(self.date_to)
        current = relativedelta(date_end, date_start)
        #print current
        years = " 0 année(s)" if not current.years else str(current.years) + " année(s) "
        months = " 0 mois " if not current.months else str(current.months) + " mois "
        days = " 0 Jour" if not current.days else str(current.days) + " jour(s) "
        self.seniority = months + years

    @api.onchange("contract_id")
    def onchange_contract_id(self):
        if self.contract_id:
            if self.payslip_hours_ids:
                self.payslip_hours_ids.update({'wage_by_hours': self.contract_id.amount_by_hour})
            else:
                list_code = []
                for code in CODE_HOURS:
                    vals_c = {'code': code, 'wage_by_hours': self.contract_id.amount_by_hour}
                    list_code.append((0, 0, vals_c))
                self.payslip_hours_ids = list_code

    payment_mode = fields.Selection(MODE_PAYMENT, "Mode de paiement")
    payslip_hours_ids = fields.One2many('hr.payslip.hours', "payslip_id", "Heures Supplementaires")
    amount_add_hours = fields.Float("Total", compute="_compute_total_hours")
    amount_hours130 = fields.Float("Total 130", compute="_compute_total_hours")
    amount_hours150 = fields.Float("Total 150", compute="_compute_total_hours")
    seniority = fields.Char("Ancienneté", compute='_compute_seniority')
    nb_day_base = fields.Integer("Base", default=30)
    nb_day_leave = fields.Integer("Jour Manqué", default=0)
    rate = fields.Integer("Taux", compute='_compute_rate')
    nb_days = fields.Integer("Nbr de jour travaillé", compute='_compute_rate')

    stc = fields.Boolean('STC')
    half_salary = fields.Boolean('Demi-salaire')
    priornotice = fields.Float(u"Préavis", store=True)
    average_gross_notice = fields.Float(u"SBR moyen préavis", store=True, compute='compute_sheet') #, compute='get_average_gross_notice'
    average_gross = fields.Float("SBR Moyen", store=True, compute='compute_sheet') #, compute='get_average_gross'
    rest_leave = fields.Float(string=u"Congé payé", store=True)#, compute='_rest_leave'
    preavis = fields.Float(store=True, compute='get_preavis')
    additional_gross = fields.Float("SBR additionnel", store=True, delault=0.00)


    #sbr moyen et sbr moyen preavis

    @api.multi
    def get_last_hr_holidays(self):
        """ Get last remaining leaves employee before payslip"""
        if self.employee_id:
            last_holiday = self.env['hr.holidays'].search([
                ('employee_id', '=', self.employee_id.id),
                ('type', '=', 'add'), ('state', 'in', ('validate', 'validate'))], order='date_to desc', limit=1)
            print('last holiday', last_holiday.number_of_days)
        return last_holiday.number_of_days

    @api.depends('employee_id')
    def get_preavis(self):
        payslip2obj = self.search([('employee_id', '=', self.employee_id.id), ('date_from', '<', self.date_from)], limit=2, order='date_from desc')
        if payslip2obj:
            sum_amount = 0.0
            i = 1
            for payslip in payslip2obj:
                payslip_lineobj = self.env['hr.payslip.line'].search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')])
                if payslip_lineobj:
                    sum_amount += payslip_lineobj.mapped('amount')[0]
                    i += 1
            self.preavis = sum_amount / i    

    @api.multi
    def get_holidays_in_period(self):
        """ Compute number day leaves takes employee in period slip """
        domain_holiday = [
            ('state', '=', 'validate'),
            ('employee_id', '=', self.employee_id.id),
            ('type', '=', 'remove'),
            ('date_from', '>=', self.date_from),
            ('date_to', '<=', self.date_to)
        ]
        holidays = self.env['hr.holidays'].search(domain_holiday)
        print(domain_holiday)
        number_day_leaves = sum(h.number_of_days_temp for h in holidays)
        print("number day leaves", number_day_leaves)
        return number_day_leaves

    @api.model
    def create(self, vals):
        res = super(HrPayslip, self).create(vals)

        if "payslip_hours_ids" not in vals:
            hours_obj = self.env['hr.payslip.hours']
            for code in CODE_HOURS:
                hours_obj.create({'code': code, 'payslip_id': res.id})

        return res

    def get_average_gross_funct(self):
        average_gross = 0.0
        if self.employee_id:
            date_start = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)]).mapped(
                'date_start')
            payslip_line_obj = self.env['hr.payslip.line']
            if date_start:
                date_start = datetime.strptime(date_start[0], tools.DEFAULT_SERVER_DATE_FORMAT)
                date_from = datetime.strptime(self.date_from, tools.DEFAULT_SERVER_DATE_FORMAT)
                seniority = self.diff_month(date_from, date_start)
                if seniority < 12 and seniority != 0:
                    payslips = self.search([('employee_id', '=', self.employee_id.id), ('date_from', '<', self.date_from)])
                    average_gross_done = 0.0
                    for payslip in payslips:
                        if payslip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')]).mapped('amount'):
                            average_gross_done += payslip_line_obj.search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')]).mapped('amount')[0]
                    average_gross = (average_gross_done + self.additional_gross) / seniority
                elif seniority > 12:
                    payslip_line_obj_last_year = self.search([('employee_id', '=', self.employee_id.id), ('date_from', '<', self.date_from)], limit=12)
                    average_gross_last_year = 0.0
                    for payslip_line in payslip_line_obj_last_year:

                        if payslip_line_obj.search([('slip_id', '=', payslip_line.id), ('code', '=', 'SBR')]).mapped('amount'):
                            average_gross_last_year += payslip_line_obj.search([('slip_id', '=', payslip_line.id), ('code', '=', 'SBR')]).mapped('amount')[0]
                    average_gross = (average_gross_last_year + self.additional_gross) / 12
                else:
                    average_gross = 0.0
            else:
                raise UserError(_('la date debut de contrat est vide'))
        else:
            self.average_gross = 0.0
        return average_gross    
        
    def get_average_gross_notice_funct(self):
        average_gross_notice = 0.0
        if self.employee_id:
            date_start = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)]).mapped(
                'date_start')
            payslip_line = self.env['hr.payslip.line']
            if date_start:
                date_start = datetime.strptime(date_start[0], tools.DEFAULT_SERVER_DATE_FORMAT)
                date_from = datetime.strptime(self.date_from, tools.DEFAULT_SERVER_DATE_FORMAT)
                seniority = self.diff_month(date_from, date_start)
                print (seniority)
                if seniority >= 2:
                    payslip2obj = self.search([('employee_id', '=', self.employee_id.id), ('date_from', '<', self.date_from)], limit=2, order='date_from desc')
                    sum_gross_done_notice = 0.0
                    for payslip in payslip2obj:
                        if payslip_line.search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')]):
                            sum_gross_done_notice += payslip_line.search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')]).mapped('amount')[0]
                    average_gross_notice = (sum_gross_done_notice + self.additional_gross) / seniority
                elif seniority < 2 and seniority > 0:
                    sum_gross_done = 0.0
                    payslips = self.search([('employee_id', '=', self.employee_id.id)])

                    for payslip in payslips:
                        if payslip_line.search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')]):
                            sum_gross_done += payslip_line.search([('slip_id', '=', payslip.id), ('code', '=', 'SBR')]).mapped('amount')[0]
                    average_gross_notice = (sum_gross_done + self.additional_gross) / seniority
                elif seniority < 0:
                    raise UserError(_("la date de paiement doit être superieur à l'ancienneté"))
                else:
                    average_gross_notice = 0.0
            else:
                raise UserError(_("cet employer n'a pas encore de contrat"))
        else:
            self.average_gross_notice = 0.0
        return average_gross_notice   

    def diff_month(self, d1, d2):
        diff = (d1.year - d2.year) * 12 + d1.month - d2.month
        return diff     

    
    # OMG, just for name
    @api.model
    def get_payslip_lines(self, contract_ids, payslip_id):
        def _sum_salary_rule_category(localdict, category, amount):
            if category.parent_id:
                localdict = _sum_salary_rule_category(localdict, category.parent_id, amount)
            if category.code in localdict['categories'].dict:
                amount += localdict['categories'].dict[category.code]
            localdict['categories'].dict[category.code] = amount
            return localdict

        class BrowsableObject(object):
            def __init__(self, employee_id, dict, env):
                self.employee_id = employee_id
                self.dict = dict
                self.env = env

            def __getattr__(self, attr):
                return attr in self.dict and self.dict.__getitem__(attr) or 0.0

        class InputLine(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(amount) as sum
                        FROM hr_payslip as hp, hr_payslip_input as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()[0] or 0.0

        class WorkedDays(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def _sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""
                        SELECT sum(number_of_days) as number_of_days, sum(number_of_hours) as number_of_hours
                        FROM hr_payslip as hp, hr_payslip_worked_days as pi
                        WHERE hp.employee_id = %s AND hp.state = 'done'
                        AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pi.payslip_id AND pi.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                return self.env.cr.fetchone()

            def sum(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[0] or 0.0

            def sum_hours(self, code, from_date, to_date=None):
                res = self._sum(code, from_date, to_date)
                return res and res[1] or 0.0

        class Payslips(BrowsableObject):
            """a class that will be used into the python code, mainly for usability purposes"""

            def sum(self, code, from_date, to_date=None):
                if to_date is None:
                    to_date = fields.Date.today()
                self.env.cr.execute("""SELECT sum(case when hp.credit_note = False then (pl.total) else (-pl.total) end)
                                FROM hr_payslip as hp, hr_payslip_line as pl
                                WHERE hp.employee_id = %s AND hp.state = 'done'
                                AND hp.date_from >= %s AND hp.date_to <= %s AND hp.id = pl.slip_id AND pl.code = %s""",
                                    (self.employee_id, from_date, to_date, code))
                res = self.env.cr.fetchone()
                return res and res[0] or 0.0

        # we keep a dict with the result because a value can be overwritten by another rule with the same code
        result_dict = {}
        rules_dict = {}
        worked_days_dict = {}
        inputs_dict = {}
        blacklist = []
        payslip = self.env['hr.payslip'].browse(payslip_id)
        for worked_days_line in payslip.worked_days_line_ids:
            worked_days_dict[worked_days_line.code] = worked_days_line
        for input_line in payslip.input_line_ids:
            inputs_dict[input_line.code] = input_line

        categories = BrowsableObject(payslip.employee_id.id, {}, self.env)
        inputs = InputLine(payslip.employee_id.id, inputs_dict, self.env)
        worked_days = WorkedDays(payslip.employee_id.id, worked_days_dict, self.env)
        payslips = Payslips(payslip.employee_id.id, payslip, self.env)
        rules = BrowsableObject(payslip.employee_id.id, rules_dict, self.env)

        baselocaldict = {'categories': categories, 'rules': rules, 'payslip': payslips, 'worked_days': worked_days,
                         'inputs': inputs}
        # get the ids of the structures on the contracts and their parent id as well
        contracts = self.env['hr.contract'].browse(contract_ids)
        structure_ids = contracts.get_all_structures()
        # get the rules of the structure and thier children
        rule_ids = self.env['hr.payroll.structure'].browse(structure_ids).get_all_rules()
        # run the rules by sequence
        sorted_rule_ids = [id for id, sequence in sorted(rule_ids, key=lambda x: x[1])]
        sorted_rules = self.env['hr.salary.rule'].browse(sorted_rule_ids)

        for contract in contracts:
            employee = contract.employee_id
            localdict = dict(baselocaldict, employee=employee, contract=contract)
            for rule in sorted_rules:
                key = rule.code + '-' + str(contract.id)
                localdict['result'] = None
                localdict['result_qty'] = 1.0
                localdict['result_rate'] = 100
                # check if the rule can be applied
                if rule.satisfy_condition(localdict) and rule.id not in blacklist:
                    # compute the amount of the rule
                    amount, qty, rate = rule.compute_rule(localdict)
                    # check if there is already a rule computed with that code
                    previous_amount = rule.code in localdict and localdict[rule.code] or 0.0
                    # set/overwrite the amount computed for this rule in the localdict
                    tot_rule = amount * qty * rate / 100.0
                    localdict[rule.code] = tot_rule
                    rules_dict[rule.code] = rule
                    # sum the amount for its salary category
                    localdict = _sum_salary_rule_category(localdict, rule.category_id, tot_rule - previous_amount)
                    # get input_line_ids name
                    input_line_name = payslip.mapped('input_line_ids').filtered(lambda x: x.code == rule.code)
                    # create/overwrite the rule in the temporary results
                    result_dict[key] = {
                        'salary_rule_id': rule.id,
                        'contract_id': contract.id,
                        'name': rule.name if not input_line_name else input_line_name[:1].name,
                        'code': rule.code,
                        'category_id': rule.category_id.id,
                        'sequence': rule.sequence,
                        'appears_on_payslip': rule.appears_on_payslip,
                        'condition_select': rule.condition_select,
                        'condition_python': rule.condition_python,
                        'condition_range': rule.condition_range,
                        'condition_range_min': rule.condition_range_min,
                        'condition_range_max': rule.condition_range_max,
                        'amount_select': rule.amount_select,
                        'amount_fix': rule.amount_fix,
                        'amount_python_compute': rule.amount_python_compute,
                        'amount_percentage': rule.amount_percentage,
                        'amount_percentage_base': rule.amount_percentage_base,
                        'register_id': rule.register_id.id,
                        'amount': amount,
                        'employee_id': contract.employee_id.id,
                        'quantity': qty,
                        'rate': rate,
                    }
                else:
                    # blacklist this rule and its children
                    blacklist += [id for id, seq in rule._recursive_search_of_rules()]

        return [value for code, value in result_dict.items()]

    #calcule de la SBR moyen



    @api.multi
    def compute_sheet(self):
        for payslip in self:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            # delete old payslip lines
            payslip.line_ids.unlink()
            # set the list of contract for which the rules have to be applied
            # if we don't give the contract, then the rules to apply should be for all current contracts of the employee
            contract_ids = payslip.contract_id.ids or \
                           self.get_contract(payslip.employee_id, payslip.date_from, payslip.date_to)
            lines = [(0, 0, line) for line in self.get_payslip_lines(contract_ids, payslip.id)]
            payslip.write({'line_ids': lines, 'number': number})
            self.average_gross = self.get_average_gross_funct()
            self.average_gross_notice = self.get_average_gross_notice_funct()
        return True    


class HrPayslipHourAdditionnal(models.Model):
    _name = 'hr.payslip.hours'

    @api.multi
    @api.depends("hours_done")
    def _compute_additional_hours(self):
        """ Compute hours additional """
        for rec in self:
            if not rec.code:
                continue
            if rec.code == 'HSD':
                rec.hs150 = rec.hours_done
            else:
                if rec.hours_done <= 8:
                    rec.hs130 = rec.hours_done
                else:
                    rec.hs130 = 8
                    rec.hs150 = rec.hours_done - 8

    @api.multi
    @api.depends("hs130", "hs150", "wage_by_hours")
    def _compute_amount_hours(self):
        for rec in self:
            if not rec.code:
                continue
            if rec.hs130:
                rec.amount_hs130 = rec.hs130 * rec.wage_by_hours * 1.3
            if rec.hs150:
                rec.amount_hs150 = rec.hs150 * rec.wage_by_hours * 1.5

    @api.multi
    @api.depends("hs130", "hs150", "wage_by_hours")
    def _compute_subtotal(self):
        for rec in self:
            if not rec.code:
                continue
            rec.subtotal_add_hours = rec.amount_hs130 + rec.amount_hs150

    code = fields.Char("H.S Hebdomadaire")
    hours_done = fields.Integer("Effectues")
    hs130 = fields.Integer("HS 130", compute="_compute_additional_hours")
    hs150 = fields.Integer("HS 150", compute="_compute_additional_hours")
    wage_by_hours = fields.Float("Salaire / Heures")
    amount_hs130 = fields.Float("Total 130", compute="_compute_amount_hours")
    amount_hs150 = fields.Float("Total 150", compute="_compute_amount_hours")
    subtotal_add_hours = fields.Float("Montant", compute='_compute_subtotal')
    payslip_id = fields.Many2one("hr.payslip", "Bulletin de paie")


class HrPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    payslip_run_id = fields.Many2one('hr.payslip.run', string='Lot de Bulletin de Paie',
                                     related="slip_id.payslip_run_id")
