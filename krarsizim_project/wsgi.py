"""
WSGI config for krarsizim_project project.

It exposes the WSGI callable as a module-level variable named ``application``.
For Vercel deployment, it also exposes ``app = application``.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'krarsizim_project.settings')

application = get_wsgi_application()

# Vercel serverless entrypoint
app = application
