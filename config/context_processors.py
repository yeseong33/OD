from config.settings import AWS_S3_CUSTOM_DOMAIN, MEDIA_URL, FILE_SAVE_POINT

def get_file_path():
    if FILE_SAVE_POINT == 'local':
        return MEDIA_URL
    else:
        return AWS_S3_CUSTOM_DOMAIN

def common_context(request):
    return {'file_path': get_file_path()}