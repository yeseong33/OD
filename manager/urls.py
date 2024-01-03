from django.urls import path
from . import views

app_name = 'manager'

urlpatterns = [
    ## 책 수요 변화
    path('book/view/', views.book_view, name='book_view'),
    path('book/view/count', views.book_view_count, name='book_view_count'),
    
    ## 신규 도서 등록
    path('book/request/', views.BookRequestListView.as_view(), name='book_request'),
    path('book/register/<int:book_isbn>/', views.BookRegisterView.as_view(), name='book_register'),
    path('book/register/complete/', views.BookRegisterCompleteView.as_view(), name='book_register_complete'),
    
    ## 1:1 문의 관리
    path('inquiries/', views.inquiry_list, name='inquiries'),
    path('inquiries/<int:inquiry_id>/', views.inquiry_detail, name='inquiry_detail'),
    # REST API endpoints
    path('api/inquiries/', views.InquiryListAPI.as_view(), name='api_inquiries'),  # REST API endpoints
    path('api/inquiries/<int:inquiry_id>/', views.InquiryDetailAPI.as_view(), name='inquiry_detail'),  
    
    ## 수익 현황
    path('subscription/', views.show_subscription, name='subscription'),
    path('api/subscription-count/', views.SubscriptionCountAPI.as_view(), name='api_subscription_count'), 
    
    ## FAQ
    path('faq/', views.faq, name='faq'),
]