import os
import json
from django.shortcuts import render
from django.core.mail import EmailMessage
from rest_framework.response import Response
from rest_framework import status
from adrf.views import APIView
import asyncio
from asgiref.sync import sync_to_async
from docxtpl import DocxTemplate

from .models import TestModel

# Create your views here.

class TestView(APIView):

    async def post(self, request):
        data = json.loads(request.body)
        send_data = {
            'name': data.get('name'),
            'phone': data.get('phone')
        }
        user_data = await asyncio.create_task(create_user(send_data))
        email = asyncio.create_task(sendEmail())
        file = asyncio.create_task(create_docx_file(send_data))
        result = await asyncio.gather(file, email)
        print(user_data.name)

        return Response({"result": {'status': 'ok', 'file': ''}})

async def sendEmail():
    msg_mail = EmailMessage(
        f"test", 
        f"""test
        """,
        'test@smprof.ru', [f"pro@cosmtech.ru"]
    )
    msg_mail.content_subtype = "html"
    msg_mail.send()


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