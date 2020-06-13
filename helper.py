# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request, Response
from .validator import validator
import simplejson as json
import json as jsonDecoder
import requests
import logging
from datetime import datetime, timedelta
from math import sin, cos, sqrt, atan2, radians
import dateutil.parser
_logger = logging.getLogger(__name__)

return_fields = ['id', 'login', 'name', 'company_id', 'employee_ids']

class Helper:

    def get_state(self):
        return {
            'd': request.session.db
        }

    def parse_request(self):
        http_method = request.httprequest.method
        headers = dict(list(request.httprequest.headers.items()))
        try:
            if http_method == 'GET':
                body =  http.request.params
            if http_method == 'POST':
                body = http.request.params
                if headers['User-Agent'].find('Postman') == -1:
                    keys = body.keys()
                    body = jsonDecoder.loads(keys[0])
        except Exception:
            body = {}

        if 'wsgi.input' in headers:
            del headers['wsgi.input']
        if 'wsgi.errors' in headers:
            del headers['wsgi.errors']
        if 'HTTP_AUTHORIZATION' in headers:
            headers['Authorization'] = headers['HTTP_AUTHORIZATION']

        # extract token
        token = ''
        if 'Authorization' in headers:
            try:
                # Bearer token_string
                token = headers['Authorization'].split(' ')[1]
            except Exception:
                pass
        _logger.info('Body: %s ', body)
        return http_method, body, headers, token

    def date2str(self, d, f='%Y-%m-%d %H:%M:%S'):
        """
        Convert datetime to string
            :param self: 
            :param d: datetime object
            :param f='%Y-%m-%d%H:%M:%S': string format
        """
        try:
            s = d.strftime(f)
        except:
            s = None
        finally:
            return s

    def response(self, success=True, message=None, data=None, code=200):
        """
        Create a HTTP Response for controller 
            :param success=True indicate this response is successful or not
            :param message=None message string
            :param data=None data to return
            :param code=200 http status code
        """
        payload = json.dumps({
            'success': success,
            'message': message,
            'data': data,
        })
        return Response(payload, status=code, headers=[
            ('Content-Type', 'application/json'),
        ])

    def response_500(self, message='Internal Server Error', data=None):
        return self.response(success=False, message=message, data=data, code=500)

    def response_404(self, message='404 Not Found', data=None):
        return self.response(success=False, message=message, data=data, code=404)

    def response_403(self, message='403 Forbidden', data=None):
        return self.response(success=False, message=message, data=data, code=403)

    def errcode(self, code, message=None):
        return self.response(success=False, code=code, message=message)
    def error(self, code, message=None):
        return self.response(success=False, code=code, message=message)

    def do_login(self, login, password, line_user_id=None, display_name=None):
        # get current db
        state = self.get_state()
        uid = request.session.authenticate(state['d'], login, password)
        if not uid:
            return self.response(data={ "status_code": "01" }, message='incorrect login')
        # login success, generate token
        user = request.env.user.read(return_fields)[0]
        richmenu = False
        if line_user_id is not None:
            record = request.env['api_attendance.line_user'].sudo().search([
                ('user_id', '=', user['id']),
                ('line_user_id', '=', line_user_id)
            ])
            if len(record) == 0:
                request.env['api_attendance.line_user'].sudo().create({
                    'user_id': user['id'],
                    'line_user_id': line_user_id,
                    'line_display_name': display_name,
                })
            richmenu = self.get_rich_menu(line_user_id)

        if user['employee_ids']:
            for emp_id in user['employee_ids']:
                user['job_title'] = self.get_job_title(emp_id)

        response = {  
            'name': user['name'],
            'job_title': user['job_title'],
        }
        
        token = validator.create_token(user)
        
        return self.response(data={ 'user': response, 'token': token, 'rich_status': richmenu, "status_code": "00" }, message="Success")

    def do_logout(self, token):
        request.session.logout()
        request.env['api_attendance.access_token'].sudo().search([
            ('token', '=', token)
        ]).unlink()

    def get_job_title(self, emp_id): 
        employee = request.env['hr.employee'].sudo().search([
            ('id', '=', emp_id)
        ])
        return employee.job_id.name

    def cleanup(self):
        request.session.logout()

    def get_directors(self, director_ids):
        directors = []
        if len(director_ids) > 0:
            for director_id in director_ids:
                directors.append(director_id.partner_id.display_name)
        return directors

    def get_rich_menu(self, line_user_id):
        try:
            config = request.env['api.attendance.config.setting'].sudo().search([
                ('line_token', '!=', None)
            ])
            if not config:
                return helper.errcode(code='422', message="Please config Line Token")

            url = "https://api.line.me/v2/bot/user/"+ line_user_id +"/richmenu/"+ config.rich_menu_id
            headers = {
                "Authorization": "Bearer "+ config.line_token
            }
            
            r = requests.post(url, headers=headers)
            _logger.info("Api get richmenu")
            _logger.info(r.json())
            return True
        except Exception as e:
            print(e)
            _logger.error(e)
            return False

    def validate_field(self, body, fields_required):
        field_invalid = []
        for key in fields_required:
            if not key in body:
              field_invalid.append(key)

        return field_invalid

    def gen_time_sheet(self, employee_id, date_start):
        Sheet = request.env['hr_timesheet_sheet.sheet']
        date_use = datetime.strftime(date_start, "%Y-%m-%d")
        start = date_start - timedelta(days=date_start.weekday())
        end = start + timedelta(days=6)
        sheet_obj = Sheet.sudo().search([('date_from', '<=', date_use),('date_to', '>=', date_use)])
        if sheet_obj:
        	return sheet_obj
        else:
            return request.env['hr_timesheet_sheet.sheet'].sudo().create({
                'employee_id': employee_id,
                'date_from':start,
                'date_to':end,
            })

    def get_monday(self, date):
        dt = datetime.strptime(date, '%Y-%m-%d')
        start = dt - timedelta(days=dt.weekday())
        return start

    def convert_float_time(self, time):
    	result = '{0:02.0f}:{1:02.0f}:00'.format(*divmod(time * 60, 60))
    	return result

    def get_time_diff(self, time1, time2):
    	return int(time2.replace(":", "")) - int(time1.replace(":", ""))

    def calculate_diff(self, time1, time2, FMT='%Y-%m-%d %H:%M:%S'):
        return datetime.strptime(time2, FMT) - datetime.strptime(time1, FMT)

    def convert_time(self, date, GMT=-7):
        if date:
            return str(datetime.strptime(date, '%Y-%m-%d %H:%M:%S') + timedelta(hours=GMT))
        else:
            return None

    def sort_array(self, arrs):
        normals = []
        lates = []
        absence = []

        for arr in arrs:
            if arr['status'] == 'normal':
                normals.append(arr)
            elif arr['status'] == 'late':
                lates.append(arr)
            else:
                absence.append(arr)

        normals.sort(key=lambda x: x['check_in'])
        lates.sort(key=lambda x: x['check_in'])
        return normals + lates + absence

    def push_line_message(self, message, line_id):
        config = request.env['api.attendance.config.setting'].sudo().search([
            ('line_token', '!=', None)
        ])
        url = "https://api.line.me/v2/bot/message/multicast"
        headers =  {
          'Content-Type': 'application/json',
          'Authorization': "Bearer %s" % config.line_token,
        }
        msg = {
            "type": "text",
            "text": message
        }
        params = {
            "to": line_id,
            "messages": [msg]
        }

        data = json.dumps(params)
        _logger.info("Push message to %s" % ','.join(line_id))
        r = requests.post(url, data=data, headers=headers)
        return True

    def notify_message(self, message):
        config = request.env['api.attendance.config.setting'].sudo().search([
            ('line_token', '!=', None)
        ])
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers =  {
          'Content-Type': 'application/json',
          'Authorization': "Bearer %s" % config.line_token,
        }
        msg = {
            "type": "text",
            "text": message
        }
        params = {
            "messages": [msg]
        }
        data = json.dumps(params)
        _logger.info("Broadcast Message %s" % message)
        r = requests.post(url, data=data, headers=headers)
        return True
            
helper = Helper()
