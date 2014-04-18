# -*- coding: utf-8 -*-
from django.conf.urls import patterns, url

from .views import(
    CreateOrderView, LoadAddressView, CreateSuccessView, MyOrderView
)


urlpatterns = patterns(
    '',
    url(r'^create/$', CreateOrderView.as_view(), name='create'),
    url(r'^me/$', MyOrderView.as_view(), name='me'),
    url(r'^load_address/$', LoadAddressView.as_view(), name='load_address'),
    url(r'^(?P<pk>\d+)/create_success/$', CreateSuccessView.as_view(),
        name='create_success'),
)