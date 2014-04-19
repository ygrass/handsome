# -*- coding: utf-8 -*-
from datetime import datetime

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.views.generic.base import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView
from django.views.generic.list import ListView

from braces.views import(
    LoginRequiredMixin, AjaxResponseMixin, JSONResponseMixin,
    StaffuserRequiredMixin
)

from .forms import CreateOrderForm
from .models import Order, Province, City, Country
from accounts.models import Profile


class CreateOrderView(LoginRequiredMixin, AjaxResponseMixin, JSONResponseMixin,
                      CreateView):
    """
    Create order 
    """
    model = Order
    form_class = CreateOrderForm
    template_name = 'orders/create_order.html'

    def get_context_data(self, **kwargs):
        """
        Override. Add extra data to context
        """
        data = super(CreateOrderView, self).get_context_data(**kwargs)
        data.update({'provinces': Province.objects.all()})
        return data

    def form_valid(self, form):
        """
        Override. Set current user as creator. Return JSON if it's AJAX.
        """
        profile = self.request.user.profile

        order = form.save(commit=False)
        order.prepayment = order.total_price * 0.1
        order.creator = profile.user
        order.style = profile.preferred_style
        order.age_group = profile.age_group
        order.height = profile.height
        order.weight = profile.weight
        order.waistline = profile.waistline
        order.chest = profile.chest
        order.hipline = profile.hipline
        order.foot = profile.foot
        order.preferred_designer = profile.user
        order.save()

        if self.request.is_ajax():
            url = reverse('orders:create_success', kwargs={'pk': order.id})
            return self.render_json_response({'success': True, 'next': url})

        return super(CreateOrderView, self).form_valid(form)

    def form_invalid(self, form):
        """
        Override. Return JSON if it's AJAX.
        """
        if self.request.is_ajax():
            return self.render_json_response({'success': False})
        return super(CreateOrderView, self).form_invalid(form)


class LoadAddressView(LoginRequiredMixin, AjaxResponseMixin, JSONResponseMixin,
                      View):
    """
    Load cities or countries or towns.
    """
    def get_ajax(self, request, *args, **kwargs):
        """
        Load address data.
        """
        level = request.GET['level']
        pk = request.GET['pk']
        if level == 'city':
            objs = Province.objects.get(pk=pk).city_set.all()
            return self.render_json_object_response(objs)
        elif level == 'country':
            objs = City.objects.get(pk=pk).country_set.all()
            return self.render_json_object_response(objs)
        elif level == 'town':
            objs = Country.objects.get(pk=pk).town_set.all()
            return self.render_json_object_response(objs)


class CreateSuccessView(LoginRequiredMixin, DetailView):
    """
    Order create success page view
    """
    model = Order
    template_name = 'orders/create_order_success.html'


class MyOrderView(LoginRequiredMixin, ListView):
    """
    Display all my orders
    """
    model = Order
    template_name = 'orders/me.html'

    def get_queryset(self):
        """
        My orders only
        """
        qs = super(MyOrderView, self).get_queryset()
        return qs.filter(creator=self.request.user).order_by('-created_at')


class OrderListView(StaffuserRequiredMixin, ListView):
    """
    Designer is the staff. We display all the orders assigned to the designer.
    """
    model = Order

    def get_context_data(self, **kwargs):
        """
        Override. Add extra data to context
        """
        data = super(OrderListView, self).get_context_data(**kwargs)
        data.update({
            'STATUS_CHOICES': Order.STATUS_CHOICES,
            'AGE_GROUP_CHOICES': Profile.AGE_GROUP_CHOICES,
            'STYLE_CHOICES': Profile.STYLE_CHOICES
        })
        data.update(self.get_params_from_request())

        return data

    def get_params_from_request(self):
        """
        Get params from request GET
        """
        # status
        status = self.request.GET.get('status')
        status = status if status else 'all'

        # style
        style = self.request.GET.get('style')
        style = style if style else 'all'

        # age group
        age_group = self.request.GET.get('age-group')
        age_group = age_group if age_group else 'all'

        # created time
        try:
            created_from = self.request.GET.get('created-from')
            created_from_dt = datetime.strptime(created_from,
                                                 '%m/%d/%Y')
        except:
            created_from_dt = None
        try:
            created_to = self.request.GET.get('created-to')
            created_to_dt = datetime.strptime(created_to, '%m/%d/%Y')
        except:
            created_to_dt = None

        return {'status': status, 'style': style, 'age_group': age_group,
                'created_from': created_from_dt, 'created_to': created_to_dt}

    def get_queryset(self):
        """
        Override. Filter the orders
        """
        qs = super(OrderListView, self).get_queryset()
        qs = qs.filter(preferred_designer=self.request.user)

        params = self.get_params_from_request()

        # status
        status = params['status']
        status_Q = Q(status=status) if status != 'all' else Q()

        # style
        style = params['style']
        style_Q = Q(style=style) if style != 'all' else Q()

        # age group
        age_group = params['age_group']
        age_group_Q = Q(age_group=age_group) if age_group != 'all' else Q()

        # created time
        from_dt = params['created_from']
        to_dt = params['created_to']
        created_time_Q = Q()
        if from_dt and to_dt:
            created_time_Q = Q(created_at__range=(from_dt, to_dt))
        elif from_dt:
            created_time_Q = Q(created_at__gte=from_dt)
        elif to_dt:
            created_time_Q = Q(created_at__lte=to_dt)

        qs = qs.filter(status_Q, style_Q, age_group_Q, created_time_Q)

        return qs.order_by('-created_at')
