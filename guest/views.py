from django.shortcuts import render
from rest_framework.renderers import JSONRenderer, TemplateHTMLRenderer
from rest_framework.views import APIView
from rest_framework.response import Response

# Create your views here.
class IndexHTML(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'audiobook/main.html'

    def get(self, request):
        user_id =99
        # context = {
        #     "user": request.user,
        #     'active_tab': 'book_inquiry'
        # }
        return Response(template_name=self.template_name)