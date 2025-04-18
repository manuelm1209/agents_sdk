from django.shortcuts import render

def home(request):
    """
    View for the home page
    """
    context = {}
    return render(request, 'home.html', context)
