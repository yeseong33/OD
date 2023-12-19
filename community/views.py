from django.shortcuts import render
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()  # 환경 변수를 로드함

class BookSearchView(APIView):
    renderer_classes = [TemplateHTMLRenderer]
    template_name = 'community/book_search.html'

    def get(self, request):
        query = request.GET.get('query', '')
        context = {'books': None}

        if query:
            url = "https://openapi.naver.com/v1/search/book.json"
            headers = {
                "X-Naver-Client-Id": os.getenv('CLIENT_ID'),
                "X-Naver-Client-Secret": os.getenv('CLIENT_SECRET'),
            }
            params = {'query': query}
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                context['books'] = response.json()['items']
            else:
                context['error'] = "An error occurred while searching for books."

        return Response(context)