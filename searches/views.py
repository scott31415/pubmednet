from django.shortcuts import redirect, render
from searches.pubmed import TopicSearch

def home_page(request):
    if request.method == 'POST':
        search_term_str = request.POST['topic_text']
        #json_fname = '_'.join(search_term_str.split())+'.json'
        json_fname = 'searches/static/coauthors.json'
        ts = TopicSearch(search_term_str)
        ts.plot_coauthor_network(json_fname)
        return redirect('/searches/%s/' % '_'.join(search_term_str.split()))    
    return render(request,'home.html')

def view_networks(request,search_term_str):
    orig_term_str = ' '.join(search_term_str.split('_'))
    return render(request,'network.html',{'term_str':orig_term_str})
# Create your views here.
