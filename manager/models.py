from django.db import models


class FAQ(models.Model):
    faq_id = models.AutoField(primary_key=True)
    faq_title = models.CharField(max_length=255)
    faq_content = models.TextField(null=True, blank=True)