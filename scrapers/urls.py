from django.conf.urls import url
from django.contrib import admin

from api_scraper.view import ToDoView

admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', 'scrapers.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', admin.site.urls),
    url(r'^api/scrapers/$', ToDoView.as_view()),
]
