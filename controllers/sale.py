# -*- coding: utf-8 -*-
import werkzeug
import jwt
import requests
import calendar
import time
from odoo import http
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from ..helper import helper
from ..validator import validator
import dateutil.parser
import json

import logging
_logger = logging.getLogger(__name__)


class SaleController(http.Controller):
	
    
    @http.route('/api/create_sale', type='json',auth='public', csrf=False, methods=['POST'])
    def post_create_sale(self, **kw):
        try:
            # http_method, body, headers = helper.parse_request()
            body =http.request.params
            res_partner = request.env['res.partner'].sudo().search([
                            ('chatbot_message_token', '=', body['recipient_id']),					
                            ], limit=1)
            # check customer 
            if not res_partner:
                # cteate customer if not exist
                res_partner = request.env['res.partner'].sudo().create({
                                'name':body['cutomer_name'],
								'chatbot_message_token': body['recipient_id'],
							})
            # check draft sale order  of customer
            sale_order = request.env['sale.order']
            sale_order = request.env['sale.order'].sudo().search([
                ('partner_id','=',res_partner.id),
                ('state','=','draft'),
            ])
            # check product
            product = request.env['product.product'].sudo().search([
                            ('default_code', '=', body['SKU']),					
                            ], limit=1)
            res = ""
            if not product:
                # create product if not exist
                product = request.env['product.product'].sudo().create({
                                'name':body['product_name'],
								'default_code': body['SKU'],
							})
            order_line = request.env['sale.order.line']
            if sale_order:
                # check product order of sale order
                order_line = sale_order.order_line.search([('product_id','=',product.id)])
                if order_line:
                    # increase qty if exist product order
                    order_line.sudo().write({
                        'product_uom_qty':order_line.product_uom_qty+float(body['qty']),
                    })
                else:
                    # create prduct order if not exist
                    order_line.sudo().create({
                        'order_id':sale_order.id,
                        'product_id':product.id,
                        'product_uom_qty':float(body['qty'])})                   
            else:
                #create sale order if not exist draft sale order of customer 
                so=sale_order.sudo().create({
                    'partner_id':res_partner.id,
                    'partner_invoice_id':res_partner.id,
                    'partner_shipping_id':res_partner.id,
                })
                order_line.sudo().create({'order_id':so.id,'product_id':product.id,
                        'product_uom_qty':float(body['qty'])})                
            item=[]
            for line in sale_order.order_line:
                item.append({'product': line.name, 'qty': line.product_uom_qty})
            
            response = {
                'message':"Success",
                'recipient_id': body['recipient_id'],
                'customer_id': res_partner.id,
                'sale_order':so.name,
            }
            return json.dumps(response,ensure_ascii=False)
            # Response.make_response(data=response, message="Success")
            
        except Exception as e:
            print(e)
            _logger.error(e)
            return helper.errcode(code=500, message="Something went wrong!")

    @http.route('/api/confirm_sale', type='json',auth='public', csrf=False, methods=['POST'])
    def post_confirm_sale(self,**kw):
        try:
            # http_method, body, headers = helper.parse_request()
            body =http.request.params            
            sale_order = request.env['sale.order'].sudo().search([
                ('name','=',body['sale_order']),                
            ])            
            if sale_order:
                sale_order.state='sale'             
            item=[]
            for line in sale_order.order_line:
                item.append({'product': line.name, 'qty': line.product_uom_qty})
            
            res_partner = request.env['res.partner'].sudo().search([
                            ('chatbot_message_token', '=', body['recipient_id']),					
                            ], limit=1)
            
            response = {
                'message':"Success",
                'recipient_id': body['recipient_id'],
                'customer_id': res_partner.id,
                'sale_order':sale_order.name,
                'item':item,
            }
            return json.dumps(response,ensure_ascii=False)
            # Response.make_response(data=response, message="Success")
        except Exception as e:
            print(e)
            _logger.error(e)
            return helper.errcode(code=500, message="Something went wrong!")

    @http.route('/api/update_address', type='json',auth='public', csrf=False, methods=['POST'])
    def post_update_address(self,**kw):
        try:
            # http_method, body, headers = helper.parse_request()
            body =http.request.params            
            sale_order = request.env['sale.order'].sudo().search([
                ('name','=',body['sale_order']),                
            ])            
            if sale_order:
                res_partner = request.env['res.partner'].sudo().search([
                            ('id', '=', sale_order.partner_id.id),					
                            ], limit=1)             
                res_partner.write({
                    'name':body['First Name']+' '+body['Last Name'],
                    'first_name':body['First Name'],
                    'last_name':body['Last Name'],
                    'chatbot_message_token':body['User Id'],
                    'street':body['address_1'],
                    'street2':body['address_2'],
                    'city':body['city'],
                    'zip':body['zip'],
                    'phone':body['phone'],
                })
            item=[]
            for line in sale_order.order_line:
                item.append({'product': line.name, 'qty': line.product_uom_qty})           
            
            response = {
                'message':"Success",
                'recipient_id': res_partner.chatbot_message_token,
                'customer_id': res_partner.id,
                'address':{'customer_name':res_partner.name,
                    'address_1':res_partner.street,
                    'address_2':res_partner.street2,
                    'city':res_partner.name,
                    'zip':res_partner.zip,
                    'phone':res_partner.phone,},
                'sale_order':sale_order.name,
                'item':item,
            }
            return json.dumps(response,ensure_ascii=False)
            # Response.make_response(data=response, message="Success")
        except Exception as e:
            print(e)
            _logger.error(e)
            return helper.errcode(code=500, message="Something went wrong!")
    
    
    @http.route('/api/get_product_avilable', type='json',auth='public', csrf=False, methods=['POST'])
    def get_product_avilable(self, **kw):
        try:
            # http_method, body, headers = helper.parse_request()
            body =http.request.params
            product = request.env['product.product'].sudo().search([
                            ('default_code', '=', body['SKU']),					
                            ], limit=1)
            res = ""
            if not product:
                product = request.env['product.product'].sudo().create({
                                'name':body['product_name'],
								'default_code': body['SKU'],
							})
            else:
                res = "unavailable" if product.qty_available ==0 else "available %s qty" % product.qty_available
            response = {
                'SKU':body['SKU'],
                'result': res,
                'qty_available': product.qty_available,
            }
            return json.dumps(response,ensure_ascii=False)
            # Response.make_response(data=response, message="Success")
            
        except Exception as e:
            print(e)
            _logger.error(e)
            return helper.errcode(code=500, message="Something went wrong!")


    