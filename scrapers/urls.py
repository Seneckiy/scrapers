from django.conf.urls import url
from django.contrib import admin

from api_scraper.view import ToDoView, DiscountView

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'scrapers.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    url(r'^api/scrapers/$', ToDoView.as_view()),
    url(r'^api/scrapers/(?P<pk>[0-9a-z]{24})/$', DiscountView.as_view()),
]
