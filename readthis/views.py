from django.shortcuts import render, render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from readthis.models import Category, Page
from readthis.forms import CategoryForm, PageForm, UserForm, UserProfileForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from datetime import datetime
from django.utils import timezone

def encode(category_name):
	return category_name.replace(' ', '_')

def decode(category_name):
	return category_name.replace('_', ' ')

def index(request):
    context = RequestContext(request)
    category_list = Category.objects.order_by('-likes')[:5]
    context_dict = {'categories': category_list}
    pages_list = Page.objects.order_by('-views')[:5]
    context_dict['pages'] = pages_list
    response = render_to_response('readthis/index.html', context_dict, context)
    visits = int(request.COOKIES.get('visits','0'))
    now = timezone.now()
    if 'last_visit' in request.COOKIES:
    	print "COOKIE HERE"
    	last_visit = request.COOKIES['last_visit']
    	last_visit_time = datetime.strptime(last_visit[:-7], "%Y-%m-%d %H:%M:%S")

    	if (datetime.now() - last_visit_time).days > 0:
    		response.set_cookie('visits', visits+1)
    		response.set_cookie('last_visit', now)
    else:
    	response.set_cookie('last_visit', now)
    	print "COOKIE MADE"

    for category in category_list:
    	category.url = encode(category.name)

    return render_to_response('readthis/index.html', context_dict, context)

def about(request):
	context = RequestContext(request)
	return render_to_response('readthis/about.html', context)

def category(request, category_name_url):
	context = RequestContext(request)
	category_name = decode(category_name_url)
	context_dict = {'category_name': category_name, 'category_name_url': category_name_url}
	
	try:
		category = Category.objects.get(name=category_name)
		pages = Page.objects.filter(category=category)
		context_dict['pages'] = pages
		context_dict['category'] = category
	except Category.DoesNotExist:
		pass

	return render_to_response('readthis/category.html', context_dict, context)

@login_required
def add_category(request):
	context = RequestContext(request)
	if request.method == 'POST':
		form = CategoryForm(request.POST)
		if form.is_valid():
			form.save(commit=True)
			return index(request)
		else:
			print form.errors
	else:
		form = CategoryForm()

	return render_to_response('readthis/add_category.html', {'form': form}, context)

@login_required
def add_page(request, category_name_url):
	context = RequestContext(request)
	category_name = decode(category_name_url)

	if request.method == 'POST':
		form = PageForm(request.POST)

		if form.is_valid():
			page = form.save(commit=False)
		try:
			cat = Category.objects.get(name = category_name)
			page.category = cat
		except Category.DoesNotExist:
			return render_to_response('readthis/add_category.html', {}, context)

		page.views = 0
		page.save()

		return category(request, category_name_url)
	else:
		form = PageForm()

	return render_to_response('readthis/add_page.html',
		{'category_name_url': category_name_url,
		'category_name': category_name, 'form':form},
		context)

def register(request):
	context = RequestContext(request)
	registered = False

	if request.method == 'POST':
		user_form = UserForm(data=request.POST)
		profile_form = UserProfileForm(data=request.POST)
		
		if user_form.is_valid() and profile_form.is_valid():
			user = user_form.save()
			user.set_password(user.password)
			user.save()

			profile = profile_form.save(commit=False)
			profile.user = user

			if 'picture' in request.FILES:
				profile.picture = request.FILES['picture']

			profile.save()

			registered = True
		else:
			print user_form.errors, profile_form.errors
	else:
		user_form = UserForm()
		profile_form = UserProfileForm()

	return render_to_response(
		'readthis/register.html',
		{'user_form': user_form, 'profile_form': profile_form, 'register': registered},
		context)

def user_login(request):
	context = RequestContext(request)
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(username=username, password=password)

		if user:
			if user.is_active:
				login(request, user)
				return HttpResponseRedirect('/readthis/')
			else:
				return HttpResponse("Your readthis account is disabled.")
		else:
			print "Invalid login details: {0}, {1}".format(username, password)
			return HttpResponse("Invalid login details supplied.")
	else:
		return render_to_response('readthis/login.html', {}, context)

@login_required
def user_logout(request):
	logout(request)
	return HttpResponseRedirect('/readthis/')

@login_required
def restricted(request):
    context=RequestContext(request)
    return render_to_response('readthis/restricted.html', {}, context)