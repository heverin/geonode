from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView

from braces.views import (
    SuperuserRequiredMixin, LoginRequiredMixin,
)

class ProfileRequestTestList(LoginRequiredMixin, TemplateView):
    template_name = 'datarequests/profile_request_list.html'
    raise_exception = True
    
@login_required
def profile_request_csv(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    response = HttpResponse(content_type='text/csv')
    datetoday = timezone.now()
    response['Content-Disposition'] = 'attachment; filename="datarequests-"'+str(datetoday.month)+str(datetoday.day)+str(datetoday.year)+'.csv"'

    writer = csv.writer(response)
    fields = ['id','name','email','contact_number', 'organization', 'organization_type','organization_other', 'created','status', 'status changed','rejection_reason','has_data_request']
    writer.writerow( fields)

    objects = ProfileRequestTest.objects.all().order_by('pk')

    for o in objects:
        writer.writerow(o.to_values_list(fields))

    return response

    
def profile_request_detail(request, pk, template='datarequests/profile_detail.html'):

    profile_request = get_object_or_404(ProfileRequestTest, pk=pk)

    if not request.user.is_superuser and not profile_request.profile == request.user:
        return HttpResponseRedirect('/forbidden')

    context_dict={"profile_request": profile_request}

    context_dict["request_reject_form"]= RejectionForm(instance=profile_request)

    return render_to_response(template, RequestContext(request, context_dict))

def profile_request_approve(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')
    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequestTest, pk=pk)

        if not profile_request.has_verified_email or profile_request.request_status != 'pending':
            return HttpResponseRedirect('/forbidden')

        result = True
        message = ''

        result, message = profile_request.create_account() #creates account in AD if AD profile does not exist

        if not result:
            messages.error (request, _(message))
        else:
            profile_request.profile.organization_type = profile_request.organization_type
            profile_request.profile.organization_other = profile_request.organization_other
            profile_request.profile.save()

            profile_request.set_approved('approved',administrator = request.user)
            
            if profile_request.data_request:
                profile_request.data_request.set_status('pending')
            
            profile_request.send_approval_email()

        return HttpResponseRedirect(profile_request.get_absolute_url())

    else:
        return HttpResponseRedirect("/forbidden/")
        
def profile_request_cancel(request, pk):
    profile_request = get_object_or_404(ProfileRequestTest, pk=pk)
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if data_request.request_status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        data_request.rejection_reason = form['rejection_reason'][0]
        data_request.save()
        
        if not request.user.is_superuser:
            data_request.set_status('cancelled')
        else:
            data_request.set_status('cancelled',administrator = request.user)
            
    url = request.build_absolute_uri(data_request.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def profile_request_reject(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden/')

    if not request.method == 'POST':
         return HttpResponseRedirect('/forbidden/')

    profile_request = get_object_or_404(ProfileRequestTest, pk=pk)

    if profile_request.request_status == 'pending':
        form = parse_qs(request.POST.get('form', None))
        profile_request.rejection_reason = form['rejection_reason'][0]
        if 'additional_rejection_reason' in form.keys():
            profile_request.additional_rejection_reason = form['additional_rejection_reason'][0]
        profile_request.save()
        
        profile_request.set_status('rejected',administrator = request.user)
        profile_request.send_rejection_email()

    url = request.build_absolute_uri(data_request.get_absolute_url())

    return HttpResponse(
        json.dumps({
            'result': 'success',
            'errors': '',
            'url': url}),
        status=200,
        mimetype='text/plain'
    )

def profile_request_reconfirm(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequestTest, pk=pk)

        profile_request.send_verification_email()
        
        messages.info("Confirmation email resent")
        return HttpResponseRedirect(request_profile.get_absolute_url())

def profile_request_recreate_dir(request, pk):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    if request.method == 'POST':
        profile_request = get_object_or_404(ProfileRequestTest, pk=pk)

        profile_request.create_directory()
        
        messages.info("Folder creation has been scheduled. Check folder location in a few minutes")
        return HttpResponseRedirect(profile_request.get_absolute_url())



def profile_request_facet_count(request):
    if not request.user.is_superuser:
        return HttpResponseRedirect('/forbidden')

    if not request.method == 'POST':
        return HttpResponseRedirect('/forbidden')

    facets_count = {
        'pending': DataRequestTest.objects.filter(
            request_status='pending').exclude(date=None).count(),
        'approved': DataRequestTest.objects.filter(
            request_status='approved').count(),
        'rejected': DataRequestTest.objects.filter(
            request_status='rejected').count(),
        'cancelled': DataRequestTest.objects.filter(
            request_status='cancelled').exclude(date=None).count(),
    }

    return HttpResponse(
        json.dumps(facets_count),
        status=200,
        mimetype='text/plain'
    )
