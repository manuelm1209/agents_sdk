from django.shortcuts import render

DATABASE_ID = "1cbbd9fe4dd680b6a1d8cc680254bc88"


# Create your views here.
def notion_dashboard(request):
    """
    Render the Notion dashboard page.
    """
    return render(request, "notion_dashboard/notion-dashboard.html")


