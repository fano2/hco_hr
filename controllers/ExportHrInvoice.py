# -*- coding: utf-8 -*-

import xlwt
from cStringIO import StringIO
import base64
from PIL import Image
import tempfile
import os

from openerp import api, models, fields
from openerp import http
from openerp.http import request
from odoo.http import content_disposition

NOM_COLONNE = [
    'DESIGNATION', 'MONTANT HT', 'TVA', 'TOTAL'
    ]

STYLE_HEADER = "font: align"

class ExportHrInvoice(http.Controller):
    """ Controller for export Hr Invoice """
    
    @http.route('/web/binary/donwload_hr_invoice', type='http', auth='public')
    def download_hr_invoice(self, id_invoice, **arg):
        """ Download HR Invoice """
        invoice = request.env['hr.invoice'].browse(int(id_invoice))
        company_id = request.env['res.company'].browse(1)
        
        filename = "Facture %s" % (invoice.name)
        
        workbook = xlwt.Workbook()
        sheet_invoice = workbook.add_sheet(filename)
        
        # Style
        style_head = xlwt.easyxf("font: bold 1, height 280; ")
        style_line = xlwt.easyxf("font: height 220; ")
        style_line_center = xlwt.easyxf("font: height 220; align: horiz center; ")
        style_line_center_bold = xlwt.easyxf("font: height 220, bold 1; align: horiz center; ")
        style_line_bold = xlwt.easyxf("font: height 220, bold 1;")
        xlwt.add_palette_colour("custom_colour", 0x21)
        workbook.set_colour_RGB(0x21, 220, 220, 220)
        style_line_head_table = xlwt.easyxf("font: height 220, bold 1; align: horiz center;pattern: pattern solid, fore_colour custom_colour;")
        
        
        i = 1
        while i < 8: 
            num_col = sheet_invoice.col(i)
            num_col.width = 256 * 20
            i += 1
        
        
        logo_decode_data = base64.decodestring(company_id.logo)
        
        # create temporary file, and save the image
        fobj = tempfile.NamedTemporaryFile(delete=False)
        fname = fobj.name
        print "fname", fname
        fname_new = fname.replace("\\", "/").split("/") if "\\" in fname else fname.split("/")
        
        fname = ''
        fname_file = fname_new[len(fname_new)-1]
        for fn in range(len(fname_new)-1):
            fname += fname_new[fn] + '/'
            
        fobj.write(logo_decode_data)
        fobj.close()
        
        # change the file extension for file in a folder to .jpg
        os.rename(fobj.name, fobj.name+'.jpg')
        
        
        img = Image.open(fname+fname_file+'.jpg').resize((80, 80), Image.ANTIALIAS)
        r, g, b, a = img.split()
        img = Image.merge("RGB", (r, g, b))
        img.save('imagetoadd.bmp')
        sheet_invoice.insert_bitmap('imagetoadd.bmp', 0, 3)
        
        sheet_invoice.write(5, 3, company_id.name, style_head)
        
        street = company_id.street if company_id.street else ''
        street2 = company_id.street if company_id.street2 else ''
        city = company_id.city if company_id.city else ''
        zip_ad = company_id.zip if company_id.zip else ''
        country_id = company_id.country_id.name if company_id.country_id else ''
        adress = street + " " + street2 + " " + city + " " + zip_ad + " " + country_id 
        sheet_invoice.write(6, 3, adress, style_line_center)
        
        nif =  "NIF: " + company_id.nif if company_id.nif else ''
        stat = " - STAT: " + company_id.stat if company_id.stat else ' '
        cif = " - RCS: " + company_id.rcs if company_id.rcs else ' '
        fisc = nif + stat + cif
        sheet_invoice.write(7, 3, fisc, style_line_center)
        
        sheet_invoice.write(10, 3, filename, style_head)
        create_date = "Antananarivo le " + fields.Datetime.from_string(invoice.create_date).strftime("%d/%m/%Y")
        sheet_invoice.write(12, 1, create_date, style_line)
        client = "Client: " + invoice.partner_id.name if invoice.partner_id else " Client:"
        sheet_invoice.write(14, 1, client, style_line)
        
        row = 15
        if invoice.partner_id: 
            if invoice.partner_id.street: 
                sheet_invoice.write(row, 1, invoice.partner_id.street, style_line)
                row += 1
            if invoice.partner_id.street2:
                city = invoice.partner_id.city 
                zip_ad = invoice.partner_id.zip
                ad_partner_id = invoice.partner_id.street2 + " " + city + " " + zip_ad
                sheet_invoice.write(row, 1, ad_partner_id, style_line)
                row += 1
        
        col = 1
        row += 1
        for nom_col in NOM_COLONNE:
            sheet_invoice.write(row, col, nom_col, style_line_head_table)
            col += 1   
        row += 1
        
        sheet_invoice.write(row, 1, invoice.designation or '', style_line_center)
        sheet_invoice.write(row, 2,  '{:,.2f}'.format(invoice.amount_HT).replace(',', ' ').replace('.', ','), style_line_center)
        sheet_invoice.write(row, 3,  '{:,.2f}'.format(invoice.amount_taxe).replace(',', ' ').replace('.', ','), style_line_center)
        sheet_invoice.write(row, 4,  '{:,.2f}'.format(invoice.amount_TTC).replace(',', ' ').replace('.', ','), style_line_center)
        row += 1
        
        sheet_invoice.write(row, 3, "TOTAL", style_line_center_bold)
        sheet_invoice.write(row, 4, '{:,.2f}'.format(invoice.amount_TTC).replace(',', ' ').replace('.', ','), style_line_center)
        row += 2
        
        sheet_invoice.write(row, 1, u"Arrêtée la présente facture à la somme de:" + invoice.amount_in_text, style_line)
        row += 2
        payment_term = u"Conditions de règlement: " + invoice.payment_term_id.name if invoice.payment_term_id else u'Conditions de règlement:'
        sheet_invoice.write(row, 1, payment_term, style_line_bold)
        row += 2
        sheet_invoice.write(row, 4, u"Le service Facturation", style_line_bold)
        
        
        fp = StringIO()
        workbook.save(fp)
        fp.seek(0)
        file_out = fp.read()
        fp.close()
        xlsheader = [('Content-Type', 'application/octet-stream'),
                     ('Content-Disposition', content_disposition(filename))
         ]
        return request.make_response(file_out, xlsheader)
        
        