import sys, queryrunner

project_id = sys.argv[1]

dp = queryrunner.DistinctPosters()
dp.run(project_id)

ppa = queryrunner.PostsPerAuthor()
ppa.run(project_id)
total_posts = sum([x[1] for x in ppa.res])

print """Distinct posters: %d
Average posts per poster: %d
Total posts: %d""" % (dp.res, total_posts/dp.res, total_posts)
