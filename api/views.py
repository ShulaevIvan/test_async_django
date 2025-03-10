import os
import json
import re
from datetime import datetime
from django.shortcuts import render
from django.core.mail import EmailMessage
from rest_framework.response import Response
from rest_framework import status
from adrf.views import APIView
import asyncio
from asgiref.sync import sync_to_async
from docxtpl import DocxTemplate

from django.conf import settings

from .models import TestModel
from .utils import select_email_template_by_order

# Create your views here.

class TestView(APIView):

    async def post(self, request):
        respone_data = {
            "status": 'ok',
            "description": '',
        }

        try:
            order_type = 'contract'
            data = json.loads(request.body)
            send_data = dict()
            send_data = {
                'name': data.get('name'),
                'phone': data.get('phone'),
                'client_email': ''
            }
            user_data = asyncio.create_task(create_user(send_data))
            email_send_task = asyncio.create_task(sendEmail(send_data, order_type))
            file_create_task = asyncio.create_task(create_docx_file(send_data))
            result_status = await asyncio.gather(user_data, email_send_task, file_create_task)

            if not email_send_task.result():
                return Response({"result": {'status': respone_data['status'], 'description': 'err to send email'}})


            return Response({"result": {'status': respone_data['status'], 'description': 'ok'}})

        except Exception as err:
            respone_data['status'] = 'err'
            respone_data['description']= 'program err'

            return Response({"result": {'status': respone_data['status']}})
       
async def sendEmail(email_data, email_type='order', to_email=None):

    email_pattern = r'\S*\@\S*\.\w{2,10}$'
    feedback_email = email_data.get('client_email')
    order_email = settings.EMAIL_HOST_USER
    send_feedback_to_client = True
    email_template = await select_email_template_by_order('specification_req')


    if not re.match(email_pattern, order_email) and not re.match(email_pattern, feedback_email):
        return False
    elif not re.match(email_pattern, feedback_email) or not feedback_email:
        send_feedback_to_client = False
    elif len(email_template) < 1:
        return False
    try:
        msg_mail = EmailMessage(
            f"{email_template.get('email_subject')}", 
            f"""
               <h3>Номер заказа: №{email_template.get('order_number')}</h3>
               <h4>Время запроса: {email_template.get('order_date')}</h4>
               <h4>Описание:</h4>
               <p>{email_template.get('email_body_description')}</p>
                <h3>Данные:</h3>
                <ul>
            """ + ''.join(f"<li>{field.get('value')}:</li>"for field in email_template.get('fields')) + '</ul>',
            f'{settings.EMAIL_HOST_USER}', [f"{settings.EMAIL_ORDER_ADDRESS}"]
        )
        msg_mail.content_subtype = "html"
        msg_mail.send()

        if send_feedback_to_client:
            try:
                client_mail = EmailMessage(
                f"test", 
                f"""
                    test
                """,
                f'{settings.EMAIL_HOST_USER}', [f"{feedback_email}"]
                )
                client_mail.content_subtype = "html"
                client_mail.send()

            except Exception as err:
                await write_err_email_log(settings.EMAIL_HOST_USER, feedback_email, err)
        
        return True
    
    except Exception as err:
        await write_err_email_log(settings.EMAIL_HOST_USER, settings.EMAIL_ORDER_ADDRESS, err)

        return False

async def create_docx_file(data):
    doc_tmp = DocxTemplate(f'{os.getcwd()}/files/test.docx')

    doc_tmp.render(data)
    doc_tmp.save(f'{os.getcwd()}/files/test1.docx')


async def create_user(data):
    await TestModel.objects.all().adelete()
    await TestModel.objects.acreate(
        name=data.get('name'),
        phone=data.get('phone')
    )
    user = await TestModel.objects.aget(
        name=data.get('name'),
        phone=data.get('phone')
    )
    return user

async def write_err_email_log(from_email, to_email, err_code):
    if not os.path.exists(settings.ERR_LOG_FOLDER):
        os.mkdir(settings.ERR_LOG_FOLDER)

    err_date = re.sub(r'.\d+$', '', str(datetime.now()))
    err_description = f"date: {err_date} from: {from_email} to: {to_email} err: {err_code}"

    with open(f'{settings.ERR_LOG_FOLDER}/email_send_err.txt', 'a+') as file:
        file.write(f'{err_description} \n')