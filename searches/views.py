from django.shortcuts import redirect, render
from searches.pubmed import TopicSearch

# Create your views here.
def home_page(request):
    if request.method == 'POST':
        search_term_str = request.POST['topic_text']
        return redirect('/searches/%s/' % '_'.join(search_term_str.split()))    
    return render(request,'home.html')

def view_networks(request,search_term_str):
    if request.method == 'POST':
        search_term_str = request.POST['topic_text']
        return redirect('/searches/%s/' % '_'.join(search_term_str.split()))    
    orig_term_str = ' '.join(search_term_str.split('_'))
    json_fname = 'searches/static/coauthors.json'
    #json_fname = '../static/coauthors.json'
    ts = TopicSearch(orig_term_str)
    ts.plot_coauthor_network(json_fname)
    return render(request,'network.html',{'term_str':orig_term_str})
