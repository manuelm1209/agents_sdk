from django.shortcuts import render

# Create your views here.
def agent_test(request):
    """
    Render the agent test template.
    """
    return render(request, 'agents_test/agents-test.html')