import logging
import jwt
import re
import datetime
import traceback
from odoo import http, service, registry, SUPERUSER_ID
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)

SECRET_KEY = "skjdfe48ueq893rihesdio*($U*WIO$u8"
regex = r"^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"

class Validator:
    def is_valid_email(self, email):
        return re.search(regex, email)

    def create_token(self, user):
        try:
            # Expires 5 year 
            exp = datetime.datetime.utcnow() + datetime.timedelta(days=1825)
            payload = {
                'exp': exp,
                'iat': datetime.datetime.utcnow(),
                'sub': user['id'],
                'lgn': user['login'],
            }

            token = jwt.encode(
                payload,
                SECRET_KEY,
                algorithm='HS256'
            )

            self.save_token(token, user['id'], exp)

            return token.decode('utf-8')
        except Exception as ex:
            _logger.error(ex)
            raise

    def save_token(self, token, uid, exp):
        request.env['api_attendance.access_token'].sudo().create({
            'user_id': uid,
            'expires': exp.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'token': token,
        })

    def verify(self, token):
        record = request.env['api_attendance.access_token'].sudo().search([
            ('token', '=', token)
        ])

        if len(record) == 0:
            _logger.info('not found %s' % token)
            return False

        if record.is_expired:
            return False

        return True

    def verify_token(self, token):
        try:
            result = {
                'status': False,
                'message': None,
            }
            payload = jwt.decode(token, SECRET_KEY)
            if not self.verify(token):
                result['message'] = 'Unauthorized'
                result['code'] = 401
                _logger.info('401 Unauthorized')
                return result

            user = request.env['res.users'].sudo().search([
                ('id', '=', payload['sub'])
            ])

            if not user:
                result['message'] = 'Unauthorized'
                result['code'] = 401
                _logger.info('401 Unauthorized')
                return result

            if not user['active']:
                result['message'] = 'Unauthorized'
                result['code'] = 401
                _logger.info('401 Unauthorized')
                return result

            result['status'] = True
            result['user'] = user
            _logger.info('________________________________')
            _logger.info('User: %s ', user['name'])
            return result
        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, Exception) as e:
            result['code'] = 401
            result['message'] = 'Unauthorized'
            _logger.error(traceback.format_exc())
            return result

validator = Validator()