import werkzeug

from odoo.exceptions import AccessDenied
from odoo import api, models, fields

import logging
_logger = logging.getLogger(__name__)

from ..validator import validator

class ResPartner(models.Model):
    _name = 'res.partner'
    _inherit = 'res.partner'

    chatbot_message_token = fields.Char(
        string='Facebook msg id',
    )
    
    first_name = fields.Char(
        string='Facebook first name',
    )
    last_name = fields.Char(
        string='Facebook last name',
    )
    
    
