# -*- coding:utf-8 -*-

from openerp import api, models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    seuil_irsa = fields.Float("Seuil IRSA")
    abat_irsa = fields.Float("Abattement IRSA")
    taux_irsa = fields.Float("Taux IRSA")
    plafond_cnaps = fields.Float("Plafond Cnaps")
    taux_cnaps = fields.Float("Taux Cnaps")
    taux_ostie = fields.Float("Taux Ostie")
    taux_medgest = fields.Float("Taux MedGest")
    amount_allocation = fields.Float("Montant Allocation Familiale")
    taux_cnaps_patr = fields.Float("Taux Patronal CNAPS")
    taux_ostie_patr = fields.Float("Taux Patronal OSTIE")
    taux_medgest_patr = fields.Float("Taux Patronal MEDGEST")
    capital_social = fields.Monetary("Capital Social")
    activity = fields.Html("Activités")
