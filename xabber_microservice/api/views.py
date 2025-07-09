from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from xabber_microservice.api.mixins import AdminMethodMixin
from xabber_microservice.api.models import Account

import json


@method_decorator(csrf_exempt, name='dispatch')
class WebhookView(View, AdminMethodMixin):
    def post(self, request, *args, **kwargs):
        # request body to json
        try:
            self._authenticate()
        except Exception as e:
            return JsonResponse({
                "message": str(e)
            }, status=401)
        
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({
                "message": "Invalid JSON"
            }, status=400)

        if data:
            event = data.get('event', None)
            
            # get class method by event and call if exists
            method = getattr(self, event, None)
            if method and callable(method):
                success, response = method(data)
            else:
                return JsonResponse({
                    "message": "Event not found"
                }, status=404)

            if not success:
                return JsonResponse({
                    "message": response
                }, status=400)
        return JsonResponse(response, status=200)
    
    def account_updated(self, data):
        jid = data.get('jid')
        attributes = data.get('attributes', [])
        
        # Get max message retention from attributes
        message_retention = 0
        unlimited = False
        for attribute in attributes:
            attribute_message_retention = attribute.get('message_retention', 0)

            # convert to integer if str is a number
            try:
                attribute_message_retention = int(attribute_message_retention)
            except:
                pass

            if attribute_message_retention == 'Unlimited':
                message_retention = 0
                unlimited = True
                break
            elif isinstance(attribute_message_retention, int) and attribute_message_retention > message_retention:
                message_retention = attribute_message_retention

        if not jid:
            return False, {"message": "Jid is required"}

        try:
            Account.objects.update_or_create(
                jid=jid,
                defaults={
                    "message_retention": message_retention,
                    "unlimited": unlimited
                }
            )
        except Exception:
            return False, {"message": "Internal service exception"}

        return True, {"message": "Webhook processed successfully"}


    def account_deleted(self, data):
        jid = data.get('jid')

        if not jid:
            return False, {"message": "Jid is required"}

        try:
            Account.objects.filter(
                jid=jid
            ).delete()
        except Exception:
            return False, {"message": "Internal service exception"}
        
        return True, {"message": "Webhook processed successfully"}