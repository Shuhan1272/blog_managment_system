from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password, check_password


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()
        confirm_password = request.POST.get('confirm_password').strip()

        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'account/register.html')
        
        #checking user with this email already exists or not, if exists then show error message
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM users WHERE email = %s", [email])
            existing_user = cursor.fetchone()

        if existing_user:
            messages.error(request, 'Email already exists.')
            return render(request, 'account/register.html')
        
        #will not store password in plain text, will hash it before storing
        hashed_password = make_password(password)

        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO users (username, email, password)
                VALUES (%s, %s, %s)
            """, [username, email, hashed_password])

        messages.success(request, 'Registration successful. Please login.')
        return redirect('login')

    return render(request, 'account/register.html') #return html template and shows in browser


def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email').strip()
        password = request.POST.get('password').strip()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, username, email, password
                FROM users
                WHERE email = %s
            """, [email])
            user = cursor.fetchone()

        #if no user found with this email then show error message
        if user is None:
            messages.error(request, 'Invalid email or password.')
            return render(request, 'account/login.html')

        #here user is tuple containing (id, username, email, hashed_password) we will unpack it to get these values
        user_id, username, user_email, hashed_password = user


        if not check_password(password, hashed_password):
            messages.error(request, 'Invalid email or password.')
            return render(request, 'account/login.html')
        
        #session is used to remember information about a user between requests #DJANGO SESSION FRAMEWORK
        request.session['user_id'] = user_id
        request.session['username'] = username
        request.session['user_email'] = user_email

        messages.success(request, 'Login successful.')
        return redirect('blog_list') #move to another url after successful login

    return render(request, 'account/login.html')


def logout_view(request):
    #removing all session data for the user
    request.session.flush()
    messages.success(request, 'Logged out successfully.')
    return redirect('login')


def dashboard_view(request):
    if 'user_id' not in request.session:
        messages.error(request, 'Please login first.')
        return redirect('login')

    user_data = {
        #request.session['key'] will throw error if key not found but request.session.get('key') will return None if key not found(safer)
        'id': request.session.get('user_id'),
        'username': request.session.get('username'),
        'email': request.session.get('user_email'),
    }

    return render(request, 'account/dashboard.html', {'user_data': user_data})