import os, sys
from django.utils import timezone
from .models import Post, Comment, Profile
from django.contrib.messages import constants as messages
from django.contrib.sites.shortcuts import get_current_site
from django.shortcuts import render, get_object_or_404, redirect
from .forms import PostForm, CommentForm, SignupForm, ImageUploadForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.contrib.auth import login, authenticate
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from cloudinary.api import delete_resources_by_tag, resources_by_tag


def post_list(request):
    user = request.user
    posts = Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user = request.user
    if user.is_authenticated:
        profile = Profile.objects.filter(user = user)
    return render(request, 'blog/post_detail.html', {'post': post})

@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.postpic = form.cleaned_data['image']
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = PostForm(request.POST, instance=post)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm(instance=post)
    return render(request, 'blog/post_edit.html', {'form': form})

@login_required
def post_draft_list(request):
    posts = Post.objects.filter(published_date__isnull=True).order_by('created_date')
    return render(request, 'blog/post_draft_list.html', {'posts': posts})

@login_required
def post_publish(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)

@login_required
def post_remove(request, pk):
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('post_list')

@login_required
def user_profile(request, userp):

    prof_user = get_object_or_404(User, username=userp)
    profile = Profile.objects.filter(user = prof_user)
    posts = Post.objects.filter(published_date__lte=timezone.now(), author=prof_user).order_by('-published_date')
    if request.method == 'POST':
        form = ImageUploadForm(request.POST, request.FILES)
        if form.is_valid():
            user = request.user
            profile = Profile.objects.filter(user = user)
            user.profile.profpic.delete()
            user.profile.profpic = form.cleaned_data['image']
            user.profile.save()
            return render(request, 'blog/user_profile.html', {'prof_user': prof_user, 'posts': posts, 'form': form})
    else:
        form = ImageUploadForm()
    return render(request, 'blog/user_profile.html', {'prof_user': prof_user, 'posts': posts, 'form': form})


@login_required
def subscribe_to_user(request, targetuser):
    user = request.user
    neededuser = get_object_or_404(User, username=targetuser)
    profile = Profile.objects.filter(user = user)
    user.profile.subscribes.add(neededuser)
    user.save()

    neededuser.profile.subscribers.add(user)
    neededuser.save()
    return_path  = request.META.get('HTTP_REFERER','/')
    return redirect(return_path)

@login_required
def unsubscribe_to_user(request, targetuser):
    user = request.user
    neededuser = get_object_or_404(User, username=targetuser)
    profile = Profile.objects.filter(user = user)

    user.profile.subscribes.remove(neededuser)
    user.save()

    neededuser.profile.subscribers.remove(user)
    neededuser.save()
    return_path  = request.META.get('HTTP_REFERER','/')
    return redirect(return_path)

@login_required
def add_like(request, pk):
    user_tags = User.objects.filter(users_likes = pk)
    current_user = request.user
    if current_user not in user_tags:
            post = get_object_or_404(Post, pk=pk)
            post.likes += 1
            post.save()
            post.likedone.add(current_user)
    else:
            post = get_object_or_404(Post, pk=pk)
            if post.likes > 0:
                post.likes -= 1
            post.likedone.remove(current_user)
            post.save()

    return_path  = request.META.get('HTTP_REFERER','/')
    return redirect(return_path)

@login_required
def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'blog/add_comment_to_post.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False

            user.save()
            current_site = get_current_site(request)
            message = render_to_string('blog/acc_active_email.html', {
                'user':user,
                'domain':current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            })
            mail_subject = 'Activate your blog account.'
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(mail_subject, message, to=[to_email])
            email.send()
            return HttpResponse('Please confirm your email address to complete the registration')
    else:
        form = SignupForm()

    return render(request, 'blog/signup.html', {'form': form})

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('post_list')
    else:
        return HttpResponse('Activation link is invalid!')

@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect('post_detail', pk=comment.post.pk)
