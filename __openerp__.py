# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2009 Tiny SPRL (<http://tiny.be>).
#
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Personnalisation RH Odoo ",
    "author": "INDEX CO ",
    "sequence": 150,
    "version": "8.0.1.1",
    "contributors": [
        'Ny Zo(INDEX CO)',
    ],
    "category": "Human Resources",
    "depends": [
        "hr_payroll",
        "partner_fisc",
        "account",
        "hr_payroll_account"
    ],
    "data": [
        "data/hr_payroll_data.xml",
        "data/sequence_data.xml",
        "security/ir.model.access.csv",
        "views/layout_template_inherit.xml",
        "views/report_hr_payslip.xml",
        "views/report_hr_invoice.xml",
        "views/hco_hr_report.xml",
        "views/res_company_inherit.xml",
        "views/hr_contract_view.xml",
        "views/hr_payslip_view.xml",
        "views/hr_employee_view.xml",
        "views/hr_invoice_view.xml",
        "views/hr_salary_rule_view.xml",
        "views/hr_health_organization_view.xml",
        "views/hr_payslip_line_view.xml",
        "views/hr_holiday_view.xml",
        "report/report_payslip_state_view.xml",
        "wizard/hr_invoice_wizard_view.xml"
    ],
    "license": 'AGPL-3',
    "installable": True,
    "application": True,
}
