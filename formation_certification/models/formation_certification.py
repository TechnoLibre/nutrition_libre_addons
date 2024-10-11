import os
import base64
from datetime import datetime
from odoo import models, fields, api
from docx import Document
from docx2pdf import convert
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import smtplib

class FormationCertification(models.Model):
    _name = 'formation.certification'
    _description = 'Certification de Formation'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Définition des champs du modèle
    name = fields.Char(string='Nom', required=True, tracking=True)
    formation_number = fields.Char(string='Numéro de Formation', required=True, tracking=True)
    formation_title = fields.Char(string='Titre de Formation', required=True, tracking=True)
    completion_date = fields.Date(string='Date de Complétion', required=True, tracking=True)
    attestation_file = fields.Binary(string='Attestation', attachment=True)
    state = fields.Selection([
        ('draft', 'Brouillon'),
        ('generated', 'Attestation Générée'),
        ('sent', 'Attestation Envoyée')
    ], string='État', default='draft', tracking=True)

    @api.model
    def generate_attestation(self, user_data, formation_data):
        # Génération de l'attestation à partir du modèle
        module_path = os.path.dirname(os.path.dirname(__file__))
        template_path = os.path.join(module_path, 'data', 'attestation_template.docx')
        doc = Document(template_path)

        # Remplacement des placeholders dans le document
        for paragraph in doc.paragraphs:
            paragraph.text = paragraph.text.replace('[NOM_PRENOM]', f"{user_data['prenom']} {user_data['nom']}")
            paragraph.text = paragraph.text.replace('[DATE]', formation_data['completion_date'].strftime('%Y-%m-%d'))
            paragraph.text = paragraph.text.replace('[FORMATION_NUMBER]', formation_data['number'])
            paragraph.text = paragraph.text.replace('[FORMATION_TITLE]', formation_data['title'])

        # Sauvegarde du document modifié
        output_docx = f"/tmp/attestation_{user_data['id']}.docx"
        doc.save(output_docx)

        # Conversion du document en PDF
        output_pdf = f"/tmp/attestation_{user_data['id']}.pdf"
        convert(output_docx, output_pdf)

        # Lecture et encodage du PDF en base64
        with open(output_pdf, 'rb') as pdf_file:
            pdf_data = pdf_file.read()
            pdf_base64 = base64.b64encode(pdf_data).decode('utf-8')

        # Nettoyage des fichiers temporaires
        os.remove(output_docx)
        os.remove(output_pdf)

        return pdf_base64

    def send_attestation_email(self):
        # Envoi de l'attestation par email
        self.ensure_one()
        sender_email = self.env['ir.config_parameter'].sudo().get_param('harmonie_certification.sender_email')
        sender_password = self.env['ir.config_parameter'].sudo().get_param('harmonie_certification.sender_password')

        # Préparation du message email
        message = MIMEMultipart()
        message['From'] = sender_email
        message['To'] = self.name  # Assuming 'name' field contains the email address
        message['Subject'] = "Votre attestation de formation"

        body = "Félicitations pour avoir complété votre formation. Veuillez trouver ci-joint votre attestation."
        message.attach(MIMEText(body, 'plain'))

        # Ajout de l'attestation en pièce jointe
        attachment = MIMEApplication(base64.b64decode(self.attestation_file), _subtype="pdf")
        attachment.add_header('Content-Disposition', 'attachment', filename="attestation.pdf")
        message.attach(attachment)

        # Envoi de l'email
        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(message)
            self.write({'state': 'sent'})
        except Exception as e:
            self.message_post(body=f"Erreur lors de l'envoi de l'email: {str(e)}")

    @api.model
    def process_certification(self, user_id, formation_id):
        # Traitement complet de la certification
        user = self.env['res.users'].browse(user_id)
        formation = self.env['formation.course'].browse(formation_id)

        user_data = {
            'id': user.id,
            'nom': user.name,
            'prenom': user.name.split()[0] if user.name else '',
            'email': user.email
        }

        formation_data = {
            'number': formation.number,
            'title': formation.title,
            'completion_date': fields.Date.today()
        }

        # Génération de l'attestation
        attestation_pdf = self.generate_attestation(user_data, formation_data)

        # Création de l'enregistrement de certification
        certification = self.create({
            'name': f"{user_data['prenom']} {user_data['nom']}",
            'formation_number': formation_data['number'],
            'formation_title': formation_data['title'],
            'completion_date': formation_data['completion_date'],
            'attestation_file': attestation_pdf,
            'state': 'generated'
        })

        return certification.id

    @api.model
    def get_dashboard_data(self):
        # Récupération des données pour le tableau de bord
        return {
            'total_certifications': self.search_count([]),
            'draft_certifications': self.search_count([('state', '=', 'draft')]),
            'sent_certifications': self.search_count([('state', '=', 'sent')]),
        }