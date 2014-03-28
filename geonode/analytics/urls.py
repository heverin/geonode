from django.conf.urls.defaults import patterns, url

js_info_dict = {
    'packages': ('geonode.analytics',),
}

urlpatterns = patterns('geonode.analytics.views',
    url(r'^$', 'analytic_list', name='analytics_browse'),
    url(r'^new/$', 'new_analysis', name='new_analysis'),
    url(r'^(?P<analysisid>\d+)/$', 'analysis_detail', name='analysis_detail'),
    url(r'^(?P<analysisid>\d+)/permissions$', 'analysis_permissions', name='analysis_permissions'),
    url(r'^new/data/$', 'new_analysis_json', name='new_analysis_json'),
    url(r'^(?P<analysisid>\d+)/view', 'analysis_view', name='analysis_view'),
    url(r'^(?P<analysisid>\d+)/remove', 'analysis_remove', name='analysis_remove'),
    url(r'^(?P<analysisid>\d+)/metadata/$', 'analysis_metadata', name='analysis_metadata'),
    )
