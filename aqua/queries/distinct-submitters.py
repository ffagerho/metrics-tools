import sys, queryrunner

project_id = sys.argv[1]

ds = queryrunner.DistinctSubmitters()
ds.run(project_id)

bpa = queryrunner.BugsPerAuthor()
bpa.run(project_id)
total_bugs = sum([x[1] for x in bpa.res])

print """Distinct submitters: %d
Average bugs per submitter: %d
Total bugs: %d""" % (ds.res, total_bugs/ds.res, total_bugs)
