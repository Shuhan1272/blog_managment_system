from django.shortcuts import render, redirect
from django.db import connection
from django.contrib import messages


def blog_list(request):
    # Fetch all blogs along with the username of the author
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT b.id, b.title, b.content,u.username, u.id
            FROM blogs b
            JOIN users u ON b.user_id = u.id
            ORDER BY b.id DESC 
        """) #order by id desc to show the latest blogs first
        rows = cursor.fetchall()

    blogs = []
    for row in rows:
        blogs.append({
            'id': row[0],
            'title': row[1],
            'content': row[2],
            'username': row[3],
            'user_id': row[4],
        })

    return render(request, 'blog/blog_list.html', {'blogs': blogs})


def create_blog(request):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')
    
    # Fetch all categories to display in the form
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM categories ORDER BY name")
        category_rows = cursor.fetchall()

    categories = []
    for row in category_rows:
        categories.append({
            'id': row[0],
            'name': row[1]
        })

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        selected_categories = request.POST.getlist('categories') #will return a list of selected category ids as strings
        user_id = request.session.get('user_id')

        if not title or not content:
            messages.error(request, "Title and content are required.")
            return render(request, 'blog/create_blog.html', {
                'categories': categories
            })

        with connection.cursor() as cursor:
            #many to one relationship between blogs and users or one to many users and blogs 
            cursor.execute("""
                INSERT INTO blogs (title, content, user_id)
                VALUES (%s, %s, %s)
            """, [title, content, user_id])

            blog_id = cursor.lastrowid # Get the ID of the newly created blog

            #many to many relationship between blogs and categories
            for category_id in selected_categories:
                cursor.execute("""
                    INSERT INTO blog_categories (blog_id, category_id)
                    VALUES (%s, %s)
                """, [blog_id, category_id])

        messages.success(request, "Blog created successfully.")
        return redirect('blog_list')

    return render(request, 'blog/create_blog.html', {
        'categories': categories
    })


def blog_details(request, blog_id):
    with connection.cursor() as cursor:
        #fetch the blog details along with the username of the author
        cursor.execute("""
            SELECT b.id, b.title, b.content, u.username, b.user_id
            FROM blogs b
            JOIN users u ON b.user_id = u.id
            WHERE b.id = %s
        """, [blog_id])

        row = cursor.fetchone()

        if not row:
            messages.error(request, "Blog not found.")
            return redirect('blog_list')
        
        #fetch the categories associated with the blog
        cursor.execute("""
            SELECT c.name
            FROM categories c
            JOIN blog_categories bc ON c.id = bc.category_id
            WHERE bc.blog_id = %s
        """, [blog_id])

        category_rows = cursor.fetchall()

    categories = []
    for cat_row in category_rows:
        categories.append(cat_row[0])

    blog = {
        'id': row[0],
        'title': row[1],
        'content': row[2],
        'username': row[3],
        'user_id': row[4],
        'categories': categories,
    }

    return render(request, 'blog/blog_details.html', {
        'blog': blog
    })


def edit_blog(request, blog_id):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    user_id = request.session.get('user_id')
    
    #getting the blog 
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, title, content, user_id
            FROM blogs
            WHERE id = %s
        """, [blog_id])

        row = cursor.fetchone()

    blog = {
        'id': row[0],
        'title': row[1],
        'content': row[2],
    }

    #getting the categories associated with the blog

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT c.id,c.name
            FROM categories c
            JOIN blog_categories bc ON c.id = bc.category_id
            WHERE bc.blog_id = %s
        """, [blog_id])

        category_rows = cursor.fetchall()
      

    blog_categories = []
    for row in category_rows:
        blog_categories.append({
            'id': row[0],
            'name': row[1]
        })

    #all categories to display in the form
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name FROM categories")

        category_rows = cursor.fetchall()
      

    categories = []
    for row in category_rows:
        categories.append({
            'id': row[0],
            'name': row[1]
                    })

    

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        selected_categories = request.POST.getlist('categories')

        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE blogs
                SET title = %s, content = %s
                WHERE id = %s
            """, [title, content, blog_id])

        # Update the blog categories
        with connection.cursor() as cursor:
            cursor.execute("""
                DELETE FROM blog_categories
                WHERE blog_id = %s
            """, [blog_id])

            for category_id in selected_categories:
                cursor.execute("""
                    INSERT INTO blog_categories (blog_id, category_id)
                    VALUES (%s, %s)
                """, [blog_id, category_id])

        messages.success(request, "Blog updated successfully.")
        return redirect('blog_details', blog_id=blog_id)

    


    return render(request, 'blog/edit_blog.html', {
        'blog': blog,
        'categories': categories,
        'blog_categories': blog_categories,
    })


def delete_blog(request, blog_id):
    if 'user_id' not in request.session:
        messages.error(request, "Please login first.")
        return redirect('login')

    user_id = request.session.get('user_id')

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT user_id
            FROM blogs
            WHERE id = %s
        """, [blog_id])

        row = cursor.fetchone()

        if not row:
            messages.error(request, "Blog not found.")
            return redirect('blog_list')

        if row[0] != user_id:
            messages.error(request, "You can only delete your own blog.")
            return redirect('blog_list')

        cursor.execute("""
            DELETE FROM blog_categories
            WHERE blog_id = %s
        """, [blog_id])

        cursor.execute("""
            DELETE FROM blogs
            WHERE id = %s
        """, [blog_id])

    messages.success(request, "Blog deleted successfully.")
    return redirect('blog_list')