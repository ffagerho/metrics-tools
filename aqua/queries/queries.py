import queryrunner
from datetime import datetime, timedelta

start_time = datetime.now()

def fig(queryClass, project_seq, file_prefix):
    for project_id in project_seq:
        print """Running %s for project %s""" % (queryClass, project_id)
        q = queryClass()
        q.run(project_id)
        q.plot()
        queryrunner.savefig("%s-%d.eps" % (file_prefix, project_id))

fig(queryrunner.CommitsPerAuthor, (1,2,3,4), "commits-per-author")
fig(queryrunner.CommitsPerAuthorHistogram, (1,2,3,4), "commits-per-author-hist")
fig(queryrunner.PostsPerAuthor, (1,3,4), "posts-per-poster")
fig(queryrunner.PostsPerAuthorHistogram, (1,3,4), "posts-per-poster-hist")
fig(queryrunner.BugsPerAuthor, (1,3,4), "bugs-per-submitter")
fig(queryrunner.BugsPerAuthorHistogram, (1,3,4), "bugs-per-submitter-hist")

for project_id in (1,2,3,4):
    print """Running %s for project %d""" % \
            (queryrunner.StaticMetrics, project_id)
    q = queryrunner.StaticMetrics()
    q.run(project_id)
    q.plot(sloc=True)
    queryrunner.savefig("%s-%d.eps" % ("sloc-evolution", project_id))
    q.plot(fanin=True, fanout=True)
    queryrunner.savefig("%s-%s.eps" % ("fanin-fanout-evolution", project_id))
    q.plot_sloc_per_nom()
    queryrunner.savefig("%s-%d.eps" % ("sloc-per-nom", project_id))
    q.plot_cyclomatic_per_nom()
    queryrunner.savefig("%s-%d.eps" % ("cyclomatic-per-nom", project_id))
    q.plot_fanin_fanout_per_sloc()
    queryrunner.savefig("%s-%d.eps" % ("fanin-fanout-per-sloc", project_id))

def freq(queryClass, project_id, start_time, end_time, freq_window, file_prefix):
    print """Running %s for project %d""" % \
            (queryClass, project_id)
    q = queryClass()
    q.run(project_id, start_time=start_time, end_time=end_time,
            freq_window=freq_window)
    q.plot()
    queryrunner.savefig("%s-%d.eps" % (file_prefix, project_id))

freq(queryrunner.CommitFrequency, 1, datetime(2004, 9, 1),
        datetime(2008, 1, 1), timedelta(days=30), "commit-freq")
freq(queryrunner.CommitFrequency, 2, datetime(2001, 11, 1),
        datetime(2005, 6, 1), timedelta(days=30), "commit-freq")
freq(queryrunner.CommitFrequency, 3, datetime(2002, 8, 1),
        datetime(2007, 11, 1), timedelta(days=30), "commit-freq")
freq(queryrunner.CommitFrequency, 4, datetime(1997, 11, 1),
        datetime(2008, 1, 1), timedelta(days=30), "commit-freq")

freq(queryrunner.PostFrequency, 1, datetime(2000, 7, 1),
        datetime(2007, 12, 31), timedelta(days=30), "post-freq")
freq(queryrunner.PostFrequency, 3, datetime(2002, 6, 1),
        datetime(2007, 12, 31), timedelta(days=30), "post-freq")
freq(queryrunner.PostFrequency, 4, datetime(1999, 6, 1),
        datetime(2007, 12, 31), timedelta(days=30), "post-freq")

freq(queryrunner.BugFrequency, 1, datetime(2002, 10, 1),
        datetime(2008, 1, 1), timedelta(days=30), "bug-freq")
freq(queryrunner.BugFrequency, 3, datetime(2002, 12, 1),
        datetime(2008, 1, 1), timedelta(days=30), "bug-freq")
freq(queryrunner.BugFrequency, 4, datetime(1999, 10, 1),
        datetime(2008, 1, 1), timedelta(days=30), "bug-freq")

freq(queryrunner.BugFreqPerCommitFreq, 1, datetime(2005, 4, 1),
        datetime(2007, 10, 1), timedelta(days=30), "bug-freq-per-commit-freq")
freq(queryrunner.BugFreqPerCommitFreq, 3, datetime(2003, 1, 1),
        datetime(2007, 10, 1), timedelta(days=30), "bug-freq-per-commit-freq")
freq(queryrunner.BugFreqPerCommitFreq, 4, datetime(2000, 1, 1),
        datetime(2007, 8, 1), timedelta(days=30), "bug-freq-per-commit-freq")

q = queryrunner.CCCCModuleMetrics()
q.run(3)
q.plot_totals(plot_cbo=True, plot_wmc=True, plot_fanin=True)
queryrunner.savefig("%s-%d.eps" % ("cccc-module-metrics-cbo-wmc-fanin", 3))
q.plot_totals(plot_dit=True, plot_noc=True)
queryrunner.savefig("%s-%d.eps" % ("cccc-module-metrics-dit-noc", 3))
q.plot_totals(plot_iflow=True)
queryrunner.savefig("%s-%d.eps" % ("cccc-module-metrics-if", 3))

# This requires a *lot* of memory
def staticmodule(project_id, prefixes):
    print """Running %s for project %d""" % \
            (queryrunner.StaticModuleMetrics, project_id)
    q = queryrunner.StaticModuleMetrics()
    q.run(project_id)
    q.plot(prefixes, sloc=True)
    queryrunner.savefig("%s-%d.eps" % ("static-module", project_id))

prefixes=(("/drivers", 'x'), ("/fs", 'v'), ("/kernel", 'o'), ("/net", 's'))
staticmodule(1, prefixes)
staticmodule(2, prefixes)
prefixes=(("/extern/ffmpeg", 'o'), ("/extern/verse", 'v'), ("/source", 'x'))
staticmodule(3, prefixes)
prefixes=(("/app", '.'), ("/libgimp", 'o'), ("/plug-ins", 'v'))
staticmodule(4, prefixes)

end_time = datetime.now()

print "Total time elapsed: %s" % (end_time - start_time)
