from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.shortcuts import (
    redirect, get_object_or_404, render, render_to_response)
from django.utils import dateformat
from django.utils import timezone
from django.utils import simplejson as json
from django.utils.html import escape
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from geonode.base.enumerations import CHARSETS
from geonode.documents.models import Document
from geonode.layers.models import UploadSession, Style
from geonode.layers.utils import file_upload
from geonode.people.models import Profile
from geonode.people.views import profile_detail
from geonode.security.views import _perms_info_json

import geonode.settings as settings

from geonode.datarequests.forms import (
    ProfileRequestForm,
    DataRequestProfileForm, DataRequestProfileShapefileForm, DataRequestDetailsForm,
    DataRequestForm, DataRequestShapefileForm)
    
from geonode.datarequests.models import DataRequestProfile, DataRequest, ProfileRequest

from pprint import pprint

def register(request):
    return HttpResponseRedirect(
        reverse('datarequests:profile_request_form'))

def profile_request_view(request):
    profile_request_obj = request.session.get('profile_request_obj', None)
    data_request_session=request.session.get('data_request_session', None)

    form = ProfileRequestForm()

    if request.user.is_authenticated():
        return HttpResponseRedirect(
            reverse('datarequests:data_request_form')
        )
    else:
        if request.method == 'POST':
            form = ProfileRequestForm(request.POST)
            if form.is_valid():
                if profile_request_obj and data_request_session:
                    profile_request_obj.first_name = form.cleaned_data['first_name']
                    profile_request_obj.middle_name = form.cleaned_data['middle_name']
                    profile_request_obj.last_name = form.cleaned_data['last_name']
                    profile_request_obj.organization = form.cleaned_data['organization']
                    profile_request_obj.organization_type=form.cleaned_data['organization_type']
                    profile_request_obj.contact_number = form.cleaned_data['contact_number']
                    if not profile_request_obj.email == form.cleaned_data['email']:
                        profile_request_obj.email = form.cleaned_data['email']
                        profile_request_obj.save()
                        profile_request_obj.send_verification_email()
                else:
                    profile_request_obj = form.save()
                    profile_request_obj.send_verification_email()
                
                request.session['profile_request_obj']= profile_request_obj
                request.session.set_expiry(900)
                return HttpResponseRedirect(
                    reverse('datarequests:data_request_form')
                )
        elif request.method == 'GET':
            if data_request_session and profile_request_obj:
                ## the user pressed back
                initial = {
                    'first_name': profile_request_obj.first_name,
                    'middle_name': profile_request_obj.middle_name,
                    'last_name': profile_request_obj.last_name,
                    'organization': profile_request_obj.organization,
                    'organization_type': profile_request_obj.organization_type,
                    'organization_other': profile_request_obj.organization_other,
                    'email': profile_request_obj.email,
                    'contact_number': profile_request_obj.contact_number,
                    'location': profile_request_obj.location
                }
                form = ProfileRequestForm(initial = initial)
        
        return render(
            request,
            'datarequests/registration/profile.html',
            {'form': form}
        )        

def data_request_view(request):
    profile_request_obj = request.session.get('profile_request_obj', None)
    if not request.user.is_authenticated() and not profile_request_obj:
        return redirect(reverse('datarequests:profile_request_form'))

    request.session['data_request_session'] = True

    form = DataRequestForm()

    if request.method == 'POST' :
        post_data = request.POST.copy()
        post_data['permissions'] = '{"users":{"dataRegistrationUploader": ["view_resourcebase"] }}'
        form = DataRequestForm(post_data, request.FILES)
        if u'base_file' in request.FILES:
            form = DataRequestShapefileForm(post_data, request.FILES)

        tempdir = None
        errormsgs = []
        out = {}
        place_name = None
        if form.is_valid():
            data_request_obj = DataRequestForm(post_data, request.FILES).save()

            if form.cleaned_data:
                if form.clean()['letter_file']:
                    request_letter = None
                    if request.user.is_authenticated() and request.user is not Profile.objects.get(username="AnonymousUser"):
                        request_letter = create_letter_document(form.clean()['letter_file'], profile=request.user)
                        data_request_obj.profile =  request.user
                    else:
                        request_letter = create_letter_document(form.clean()['letter_file'], profile_request=profile_request_obj)
                        data_request_obj.profile_request = profile_request_obj
                        profile_request_obj.data_request = data_request_obj
                        profile_request_obj.save()
                    data_request_obj.request_letter = request_letter
                    data_request_obj.save()
                    
                if u'base_file' in request.FILES:
                    pprint(request.FILES)
                    title = form.cleaned_data["layer_title"]

                    # Replace dots in filename - GeoServer REST API upload bug
                    # and avoid any other invalid characters.
                    # Use the title if possible, otherwise default to the filename
                    if title is not None and len(title) > 0:
                        name_base = title
                    else:
                        name_base, __ = os.path.splitext(
                            form.cleaned_data["base_file"].name)

                    name = slugify(name_base.replace(".", "_"))

                    try:
                        # Moved this inside the try/except block because it can raise
                        # exceptions when unicode characters are present.
                        # This should be followed up in upstream Django.
                        tempdir, base_file = form.write_files()
                        registration_uploader, created = Profile.objects.get_or_create(username='dataRegistrationUploader')
                        pprint("saving jurisdiction")
                        saved_layer = file_upload(
                            base_file,
                            name=name,
                            user=registration_uploader,
                            overwrite=False,
                            charset=form.cleaned_data["charset"],
                            abstract=form.cleaned_data["abstract"],
                            title=form.cleaned_data["layer_title"],
                        )

                    except Exception as e:
                        exception_type, error, tb = sys.exc_info()
                        print traceback.format_exc()
                        out['success'] = False
                        out['errors'] = "An unexpected error was encountered. Check the files you have uploaded, clear your selected files, and try again."
                        # Assign the error message to the latest UploadSession of the data request uploader user.
                        latest_uploads = UploadSession.objects.filter(
                            user=registration_uploader
                        ).order_by('-date')
                        if latest_uploads.count() > 0:
                            upload_session = latest_uploads[0]
                            upload_session.error = str(error)
                            upload_session.traceback = traceback.format_exc(tb)
                            upload_session.context = "Data requester's jurisdiction file upload"
                            upload_session.save()
                            out['traceback'] = upload_session.traceback
                            out['context'] = upload_session.context
                            out['upload_session'] = upload_session.id
                    else:
                        out['success'] = True
                        out['url'] = reverse(
                            'layer_detail', args=[
                                saved_layer.service_typename])

                        upload_session = saved_layer.upload_session
                        upload_session.processed = True
                        upload_session.save()
                        permissions = {
                            'users': {'dataRegistrationUploader': []},
                            'groups': {}
                        }
                        if request.user.is_authenticated():
                            permissions = {
                                'users': {request.user.username : ['view_resourcebase']},
                                'groups': {}
                            }

                        data_request_obj.jurisdiction_shapefile = interest_layer
                        data_request_obj.save()

                        if permissions is not None and len(permissions.keys()) > 0:

                            saved_layer.set_permissions(permissions)
                        
                        jurisdiction_style.delay(saved_layer)
                        place_name_update.delay([data_request_obj])
                        compute_size_update.delay([data_request_obj])

                    finally:
                        if tempdir is not None:
                            shutil.rmtree(tempdir)

                else:
                    pprint("unable to retrieve request object")

                    for e in form.errors.values():
                        errormsgs.extend([escape(v) for v in e])
                    out['success'] = False
                    out['errors'] =  dict(
                        (k, map(unicode, v))
                        for (k,v) in form.errors.iteritems()
                    )
                    pprint(out['errors'])
                    out['errormsgs'] = out['errors']
        else:
            for e in form.errors.values():
                errormsgs.extend([escape(v) for v in e])
            out['success'] = False
            out['errors'] = dict(
                    (k, map(unicode, v))
                    for (k,v) in form.errors.iteritems()
            )
            pprint(out['errors'])
            out['errormsgs'] = out['errors']

        if out['success']:
            status_code = 200
            pprint("request has been succesfully submitted")
            if profile_request_obj and not request.user.is_authenticated():
            #    request_data.send_verification_email()

                out['success_url'] = reverse('datarequests:email_verification_send')

                out['redirect_to'] = reverse('datarequests:email_verification_send')

            elif request.user.is_authenticated():
                messages.info("Your request has been submitted")
                out['success_url'] = reverse('home')

                out['redirect_to'] = reverse('home')

            del request.session['data_request_session']
            del request.session['profile_request_obj']
        else:
            status_code = 400
        return HttpResponse(
            json.dumps(out),
            mimetype='application/json',
            status=status_code)
    return render(
        request,
        'datarequests/registration/shapefile.html',
        {
            'charsets': CHARSETS,
            'is_layer': True,
            'form': form,
            'support_email': settings.LIPAD_SUPPORT_MAIL,
        })

def email_verification_send(request):

    if request.user.is_authenticated():
        return HttpResponseRedirect(reverse('home'))

    context = {
        'support_email': settings.LIPAD_SUPPORT_MAIL,
    }
    return render(
        request,
        'datarequests/registration/verification_sent.html',
        context
    )

def email_verification_confirm(request):
    key = request.GET.get('key', None)
    email = request.GET.get('email', None)

    context = {
        'support_email': settings.LIPAD_SUPPORT_MAIL,
    }

    if key and email:
        try:
            profile_request = ProfileRequest.objects.get(
                email=email,
                verification_key=key,
            )
            # Only verify once
            if not data_request.verification_date:
                profile_request.request_status = 'pending'
                profile_request.date = timezone.now()
                pprint(email+" has been confirmed")
                profile_request.save()
                profile_request.send_new_request_notif_to_admins()
                if profile_request.data_request:
                    dr = profile_request.data_request
                    dr.request_status = 'pending'
                    dr.save()
                    
        except ObjectDoesNotExist:
            profile_request = None

        if data_request:
            return render(
                request,
                'datarequests/registration/verification_done.html',
                context
            )

    return render(
        request,
        'datarequests/registration/verification_failed.html',
        context
    )

def create_letter_document(request_letter, profile=None, profile_request=None):
    if not profile or not profile_request:
        raise PermissionDenied
        
    details = None
    letter_owner = None
    permissions = None
    
    if profile:
        details = profile
        letter_owner = profile
        permissions = {"users":{profile.username:["view_resourcebase","download_resourcebase"]}}
    else:
        details = profile_request
        letter_owner = Profile.objects.get_or_create(username='dataRegistrationUploader')
        permissions = {"users":{"dataRegistrationUploader":["view_resourcebase"]}}
        
    requester_name = unidecode(details.first_name+" " +details.last_name)
    letter = Document()
    letter.owner = letter_owner
    letter.doc_file = request_letter
    letter.title = requester_name + " Request Letter " +datetime.datetime.now().strftime("%Y-%m-%d")
    letter.is_published = False
    letter.save()
    letter.set_permissions(permissions)
    
    return letter
