import sys, queryrunner

project_id = sys.argv[1]

tcom = queryrunner.TotalCommits()
tcom.run(project_id)

cpa = queryrunner.CommitsPerAuthorHistogram()
cpa.run(project_id)
cpa.plot(bins=(0,50,500))
counts = cpa.hist[0]
commits = cpa.hist[1]

core_devs = counts[2]
core_commits = commits[2]
co_devs = counts[1]
co_commits = commits[1]
act_users = counts[0]
act_commits = commits[0]
tot_authors = len(cpa.res)
tot_commits = tcom.res

print """Core developers: %d (%.2f %%) (>= %d commits)
Co-developers: %d (%.2f %%) (>= %d commits)
Active users: %d (%.2f %%) (>= %d commits)
Total authors: %d (%d %%)
Total commits: %d""" % \
		(core_devs, float(core_devs)/float(tot_authors)*100.0, core_commits,
		co_devs, float(co_devs)/float(tot_authors)*100.0, co_commits,
		act_users, float(act_users)/float(tot_authors)*100.0, act_commits,
		tot_authors, float(tot_authors)/float(tot_authors)*100.0,
		tot_commits)
