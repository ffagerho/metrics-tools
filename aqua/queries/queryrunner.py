import psycopg2
import matplotlib
matplotlib.use('PS')
from pylab import *
from datetime import datetime, timedelta
from time import sleep

"""
This is a simple framework for running queries.
"""

majorFormatter = ScalarFormatter(useMathText=False)

class Query:
    def __init__(self):
        self.dbconn = psycopg2.connect(database="foss", user="foss",
                password="f055", host="localhost", port="19000")
        self.dbconn.set_client_encoding('UTF8')
        self.curs = self.dbconn.cursor()
    
    def run(self):
        raise NotImplementedError

    def plot(self):
        raise NotImplementedError

    def save(self, file=None):
        if not file:
            file = self.__class__.__name__
        self.plot()
        savefig(file)

    def __str__(self):
        return "<%s>" % (self.__class__.__name__)

    def latex_output(self):
        raise NotImplementedError

    def get_project_name(self, project_id):
        self.curs.execute("""SELECT name FROM project
                             WHERE id = %(project_id)s""",
                             {'project_id': project_id})
        self.project_name = self.curs.fetchone()[0]

class TotalCommits(Query):
    """
    Count the total amount of commits in a specific project, during a
    specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT count(revision.id) AS commits
                 FROM revision JOIN
                      vcs ON revision.vcs_id = vcs.id JOIN
                      project ON vcs.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      revision.timestamp >= %(start_time)s AND
                      revision.timestamp <= %(end_time)s"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    })
        self.res = self.curs.fetchone()[0]

class CommitsPerAuthor(Query):
    """
    Number of commits for each author in a specific project, during a
    specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT revision.author AS author,
            count(revision.id) AS commits
            FROM revision JOIN
                vcs ON revision.vcs_id = vcs.id JOIN
                project ON vcs.project_id = project.id
            WHERE
                project.id = %(project_id)s AND
                revision.timestamp >= %(start_time)s AND
                revision.timestamp <= %(end_time)s
            GROUP BY author
            ORDER BY commits DESC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    })
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)
    
    def plot(self):
        clf()
        ydata = [y[1] for y in self.res]
        line, = plot(ydata, '.')
        line.set_label("Commits for author")
        xlabel("Author")
        ylabel("Commits")
        title(self.project_name)
        show()
    
class CommitsPerAuthorHistogram(CommitsPerAuthor):
    """
    Histogram of commits per author in a specific project, during a
    specific time interval.
    """

    def plot(self, bins=10):
        clf()
        ydata = [y[1] for y in self.res]
        self.hist = hist(ydata, bins=bins)
        xlabel("Commits")
        ylabel("Authors")
        title(self.project_name)
        axis('tight')
        show()
    
class PostsPerAuthor(Query):
    """
    Number of posts for each author in a specific project, during a
    specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT post."from" AS poster,
                        count(post.id) AS posts
                 FROM post JOIN
                      mailinglist ON post.mailinglist_id = mailinglist.id JOIN
                      project ON mailinglist.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      post.timestamp >= %(start_time)s AND
                      post.timestamp <= %(end_time)s
                 GROUP BY poster
                 ORDER BY posts DESC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    })
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)

    def plot(self):
        clf()
        ydata = [y[1] for y in self.res]
        plot(ydata, '.')
        xlabel("Poster")
        ylabel("Messages")
        title(self.project_name)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        show()

class PostsPerAuthorHistogram(PostsPerAuthor):
    """
    Histogram of posts per author in a specific project, during a
    specific time interval.
    """

    def plot(self, bins=10):
        clf()
        ydata = [y[1] for y in self.res]
        hist(ydata, bins=bins)
        xlabel("Messages")
        ylabel("Posters")
        title(self.project_name)
        axis('tight')
        show()

class DistinctPosters(Query):
    """
    Count the total amount of distinct posters for a specific project,
    during a specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT DISTINCT post."from"
                 FROM post JOIN
                      mailinglist ON post.mailinglist_id = mailinglist.id JOIN
                      project ON mailinglist.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      post.timestamp >= %(start_time)s AND
                      post.timestamp <= %(end_time)s"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    })
        res = self.curs.fetchall()
        self.res = len(res)

class DistinctSubmitters(Query):
    """
    Count the number of distinct submitters for a specific project,
    during a specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT DISTINCT bug.submitter
                 FROM bug JOIN
                      bts ON bug.bts_id = bts.id JOIN
                      project ON bts.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      bug.creation_time >= %(start_time)s AND
                      bug.creation_time <= %(end_time)s"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    })
        res = self.curs.fetchall()
        self.res = len(res)

class BugsPerAuthor(Query):
    """
    Number of bugs for each author in a specific project, during a
    specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT bug.submitter AS submitter,
                        count(bug.id) AS bugs
                 FROM bug JOIN
                      bts ON bug.bts_id = bts.id JOIN
                      project ON bts.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      bug.creation_time >= %(start_time)s AND
                      bug.creation_time <= %(end_time)s
                 GROUP BY submitter
                 ORDER BY bugs DESC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time,
                    })
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)
    
    def plot(self):
        clf()
        ydata = [y[1] for y in self.res]
        plot(ydata, '.')
        xlabel("Submitter")
        ylabel("Bugs")
        title(self.project_name)
        show()

class BugsPerAuthorHistogram(BugsPerAuthor):
    """
    Histogram of bugs per author in a specific project, during a
    specific time interval.
    """

    def plot(self, bins=10):
        clf()
        ydata = [y[1] for y in self.res]
        hist(ydata, bins=bins)
        xlabel("Bugs")
        ylabel("Submitters")
        title(self.project_name)
        axis('tight')
        show()

class CommitsXPosts(Query):
    """
    Correlation between number of commits and number of posts of each author
    in a specific project, during a specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        commits_query = CommitsPerAuthor()
        commits_query.run(project_id, start_time, end_time)
        self.commits_res = commits_query.res

        posts_query = PostsPerAuthor()
        posts_query.run(project_id, start_time, end_time)
        self.posts_res = posts_query.res

        sql = """SELECT count(revision.id) AS commits,
                        count(post.id) AS posts
                 FROM revision JOIN
                      vcs ON revision.vcs_id = vcs.id JOIN
                      project ON vcs.project_id = project.id JOIN
                      post ON revision.author = post."from" JOIN
                      mailinglist ON post.mailinglist_id = mailinglist.id JOIN
                      project ON mailinglist.project_id = project.id
                 GROUP BY revision.author,
                          post."from",
                          revision.id,
                          post.id"""

        self.get_project_name(project_id)

    def plot(self):
        clf()
        xdata = [x[1] for x in self.commits_res]
        ydata = [y[1] for y in self.posts_res]
        plot(xdata, ydata, '.')
        xlabel("Commits")
        ylabel("Posts")
        title(self.project_name)
        axis('tight')
        show()

class CommitFrequency(Query):
    """
    Measures number of commits during a specified time window (eg. a day)
    in a specific project, during a specific time interval.
    """

    def run(self, project_id, start_time=datetime(1980, 1, 1),
            end_time=datetime(3000, 1, 1), freq_window=timedelta(days=1)):
        self.res = []
        window_start = start_time
        window_end = window_start + freq_window
        while window_start < end_time:
            # print "%s -- %s" % (window_start, window_end)
            sql = """SELECT count(revision.id) AS commits
                     FROM revision JOIN
                          vcs ON revision.vcs_id = vcs.id JOIN
                          project ON vcs.project_id = project.id
                     WHERE
                          project.id = %(project_id)s AND
                          revision.timestamp >= %(start_time)s AND
                          revision.timestamp <= %(end_time)s AND
                          revision.timestamp >= %(window_start)s AND
                          revision.timestamp <= %(window_end)s
                     ORDER BY commits DESC"""
            self.curs.execute(sql,
                    {'project_id': project_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'window_start': window_start,
                        'window_end': window_end,
                        })
            res = self.curs.fetchall()

            #self.res.append((window_start, res[0][0]))
            #self.res.append((window_end, res[0][0]))
            window_middle_timestamp = ( date2num(window_start) + date2num(window_end) ) / 2.0
            self.res.append((window_middle_timestamp, res[0][0]))

            window_start = window_end
            window_end = window_end + freq_window

        self.get_project_name(project_id)
        self.freq_window = freq_window

    def plot(self):
        clf()
        commit_values = [y[1] for y in self.res]
        #timestamps = [date2num(x[0]) for x in self.res]
        timestamps = [x[0] for x in self.res]

        line, = plot_date(timestamps, commit_values)
        line.set_label("Commits per %d days" % self.freq_window.days)
        line.set_marker('.')
        line.set_linestyle('-')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        v = axis('auto')
        v2 = axis('tight')
        axis((v2[0], v2[1], v[2], v[3]))
        show()

class PostFrequency(Query):
    """
    Measures number of posts during a specified time window (eg. a day)
    in a specific project, during a specific time interval.
    """

    def run(self, project_id, start_time=datetime(1980, 1, 1),
            end_time=datetime(3000, 1, 1), freq_window=timedelta(days=1)):
        self.res = []
        window_start = start_time
        window_end = window_start + freq_window
        while window_start < end_time:
            # print "%s -- %s" % (window_start, window_end)
            sql = """SELECT count(post.id) AS posts
                     FROM post JOIN
                     mailinglist ON post.mailinglist_id = mailinglist.id JOIN
                     project ON mailinglist.project_id = project.id
                     WHERE
                         project.id = %(project_id)s AND
                         post.timestamp >= %(start_time)s AND
                         post.timestamp <= %(end_time)s AND
                         post.timestamp >= %(window_start)s AND
                         post.timestamp <= %(window_end)s
                     ORDER BY posts DESC"""
            self.curs.execute(sql,
                    {'project_id': project_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'window_start': window_start,
                        'window_end': window_end,
                        })
            res = self.curs.fetchall()

            #self.res.append((window_start, res[0][0]))
            #self.res.append((window_end, res[0][0]))
            window_middle_timestamp = ( date2num(window_start) + date2num(window_end) ) / 2.0
            self.res.append((window_middle_timestamp, res[0][0]))

            window_start = window_end
            window_end = window_end + freq_window

        self.get_project_name(project_id)
        self.freq_window = freq_window

    def plot(self):
        clf()
        post_values = [y[1] for y in self.res]
        #timestamps = [date2num(x[0]) for x in self.res]
        timestamps = [x[0] for x in self.res]

        line, = plot_date(timestamps, post_values)
        line.set_label("Posts per %d days" % self.freq_window.days)
        line.set_marker('.')
        line.set_linestyle('-')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        axis('tight')
        show()

class BugFrequency(Query):
    """
    Measures number of bugs during a specified time window (eg. a day)
    in a specific project, during a specific time interval.
    """

    def run(self, project_id, start_time=datetime(1980, 1, 2),
            end_time=datetime(3000, 1, 1), freq_window=timedelta(days=1)):
        self.res = []
        window_start = start_time
        window_end = window_start + freq_window
        while window_start < end_time:
            # print "%s -- %s" % (window_start, window_end)
            sql = """SELECT count(bug.id) AS bugs
                     FROM bug JOIN
                          bts ON bug.bts_id = bts.id JOIN
                          project ON bts.project_id = project.id
                     WHERE
                          project.id = %(project_id)s AND
                          bug.creation_time >= %(start_time)s AND
                          bug.creation_time <= %(end_time)s AND
                          bug.creation_time >= %(window_start)s AND
                          bug.creation_time <= %(window_end)s
                     ORDER BY bugs DESC"""
            self.curs.execute(sql,
                    {'project_id': project_id,
                        'start_time': start_time,
                        'end_time': end_time,
                        'window_start': window_start,
                        'window_end': window_end,
                        })
            res = self.curs.fetchall()

            #self.res.append((window_start, res[0][0]))
            #self.res.append((window_end, res[0][0]))
            window_middle_timestamp = ( date2num(window_start) + date2num(window_end) ) / 2.0
            self.res.append((window_middle_timestamp, res[0][0]))

            window_start = window_end
            window_end = window_end + freq_window

        self.get_project_name(project_id)
        self.freq_window = freq_window

    def plot(self):
        clf()
        bug_values = [y[1] for y in self.res]
        #timestamps = [date2num(x[0]) for x in self.res]
        timestamps = [x[0] for x in self.res]

        line, = plot_date(timestamps, bug_values)
        line.set_label("Bugs per %d days" % self.freq_window.days)
        line.set_marker('.')
        line.set_linestyle('-')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        v = axis('auto')
        v2 = axis('tight')
        axis((v2[0], v2[1], v[2], v[3]))
        show()

class CCCCMetrics(Query):
    """
    Measures CCCC metrics in a specific project, during a specific
    time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT cccc_metrics.sloc AS sloc,
                        cccc_metrics.cloc AS cloc,
                        cccc_metrics.rejloc AS rejloc,
                        cccc_metrics.cyclomatic AS cyclomatic,
                        cccc_metrics.if AS if,
                        cccc_metrics.nom AS nom,
                        revision.timestamp AS timestamp
                 FROM cccc_metrics JOIN
                      revision ON cccc_metrics.revision_id = revision.id JOIN
                      vcs ON revision.vcs_id = vcs.id JOIN
                      project ON vcs.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      revision.timestamp >= %(start_time)s AND
                      revision.timestamp <= %(end_time)s
                 ORDER BY timestamp ASC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time})
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)

    def plot(self, sloc=False, cloc=False, rejloc=False, cyclomatic=False,
            iflow=False, nom=False):
        clf()
        sloc_values = [y[0] for y in self.res]
        cloc_values = [y[1] for y in self.res]
        rejloc_values = [y[2] for y in self.res]
        cyclomatic_values = [y[3] for y in self.res]
        if_values = [y[4] for y in self.res]
        nom_values = [y[5] for y in self.res]
        timestamps = [date2num(x[6]) for x in self.res]

        if sloc:
            line, = plot_date(timestamps, sloc_values)
            line.set_label("SLOC")
            line.set_color('r')
        if cloc:
            line, = plot_date(timestamps, cloc_values)
            line.set_label("CLOC")
        if rejloc:
            line, = plot_date(timestamps, rejloc_values)
            line.set_label("REJLOC")
        if cyclomatic:
            line, = plot_date(timestamps, cyclomatic_values)
            line.set_label("CYC")
        if iflow:
            line, = plot_date(timestamps, if_values)
            line.set_label("IF")
        if nom:
            line, = plot_date(timestamps, nom_values)
            line.set_label("NOM")

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

    def plot_sloc_per_nom(self):
        clf()
        sloc_values = [y[0] for y in self.res]
        nom_values = [y[5] for y in self.res]
        sloc_per_nom_values = map(lambda s, n: s/n, sloc_values, nom_values)
        timestamps = [date2num(x[6]) for x in self.res]

        line, = plot_date(timestamps, sloc_per_nom_values)
        line.set_label("SLOC/NOM")
        line.set_color('#ff007f')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

class CCCCModuleMetrics(Query):
    """
    Measures CCCC module metrics in a specific project, during a specific
    time interval, and for a specific set of modules, given as a sequence
    to the run method.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT cccc_module_metrics.path AS path,
                        cccc_module_metrics.cbo AS cbo,
                        cccc_module_metrics.dit AS dit,
                        cccc_module_metrics.noc AS noc,
                        cccc_module_metrics.wmc AS wmc,
                        cccc_module_metrics.fanin AS fanin,
                        cccc_module_metrics.fanout AS fanout,
                        cccc_module_metrics.if AS if,
                        revision.timestamp AS timestamp
                 FROM cccc_module_metrics JOIN
                 revision ON cccc_module_metrics.revision_id = revision.id JOIN
                 vcs ON revision.vcs_id = vcs.id JOIN
                 project ON vcs.project_id = project.id
                 WHERE project.id = %(project_id)s AND
                       revision.timestamp >= %(start_time)s AND
                       revision.timestamp <= %(end_time)s
                 ORDER BY timestamp ASC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time})
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)

    def plot(self, modules, cbo=False, dit=False, noc=False, wmc=False,
            fanin=False, fanout=False, iflow=False):
        clf()
        for module in modules:
            cbo_values = [y[1] for y in self.res if y[0] == module]
            dit_values = [y[2] for y in self.res if y[0] == module]
            noc_values = [y[3] for y in self.res if y[0] == module]
            wmc_values = [y[4] for y in self.res if y[0] == module]
            fanin_values = [y[5] for y in self.res if y[0] == module]
            fanout_values = [y[6] for y in self.res if y[0] == module]
            iflow_values = [y[7] for y in self.res if y[0] == module]
            timestamps = [date2num(x[8]) for x in self.res if x[0] == module]

            if cbo:
                line, = plot_date(timestamps, cbo_values)
                line.set_label("CBO: %s" % (module))
            if dit:
                line, = plot_date(timestamps, dit_values)
                line.set_label("DIT: %s" % (module))
            if noc:
                line, = plot_date(timestamps, noc_values)
                line.set_label("NOC: %s" % (module))
            if wmc:
                line, = plot_date(timestamps, wmc_values)
                line.set_label("WMC: %s" % (module))
            if fanin:
                line, = plot_date(timestamps, fanin_values)
                line.set_label("FANIN: %s" % (module))
            if fanout:
                line, = plot_date(timestamps, fanout_values)
                line.set_label("FANOUT: %s" % (module))
            if iflow:
                line, = plot_date(timestamps, iflow_values)
                line.set_label("IF: %s" % (module))

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

    def plot_totals(self, plot_cbo=False, plot_dit=False, plot_noc=False,
            plot_wmc=False, plot_fanin=False, plot_fanout=False,
            plot_iflow=False):
        clf()
        data = {}
        for r in self.res:
            (path, cbo, dit, noc, wmc, fanin, fanout, iflow, timestamp) = r
            if data.has_key(timestamp):
                data[timestamp]['cbo'] += cbo
                data[timestamp]['dit'] += dit
                data[timestamp]['noc'] += noc
                data[timestamp]['wmc'] += wmc
                data[timestamp]['fanin'] += fanin
                data[timestamp]['fanout'] += fanout
                data[timestamp]['iflow'] += iflow
            else:
                data[timestamp] = {}
                data[timestamp]['cbo'] = cbo
                data[timestamp]['dit'] = dit
                data[timestamp]['noc'] = noc
                data[timestamp]['wmc'] = wmc
                data[timestamp]['fanin'] = fanin
                data[timestamp]['fanout'] = fanout
                data[timestamp]['iflow'] = iflow

        cbo_values = [y['cbo'] for y in [data[ts] for ts in data]]
        dit_values = [y['dit'] for y in [data[ts] for ts in data]]
        noc_values = [y['noc'] for y in [data[ts] for ts in data]]
        wmc_values = [y['wmc'] for y in [data[ts] for ts in data]]
        fanin_values = [y['fanin'] for y in [data[ts] for ts in data]]
        fanout_values = [y['fanout'] for y in [data[ts] for ts in data]]
        iflow_values = [y['iflow'] for y in [data[ts] for ts in data]]
        timestamps = [date2num(ts) for ts in data]
        
        if plot_cbo:
            line, = plot_date(timestamps, cbo_values)
            line.set_label("CBO")
            line.set_color('b')
        if plot_dit:
            line, = plot_date(timestamps, dit_values)
            line.set_label("DIT")
            line.set_color('g')
        if plot_noc:
            line, = plot_date(timestamps, noc_values)
            line.set_label("NOC")
            line.set_color('r')
        if plot_wmc:
            line, = plot_date(timestamps, wmc_values)
            line.set_label("WMC")
            line.set_color('c')
        if plot_fanin:
            line, = plot_date(timestamps, fanin_values)
            line.set_label("FANIN")
            line.set_color('m')
        if plot_fanout:
            line, = plot_date(timestamps, fanout_values)
            line.set_label("FANOUT")
            line.set_color('y')
        if plot_iflow:
            line, = plot_date(timestamps, iflow_values)
            line.set_label("IF")
            line.set_color('#ff00ff')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

class CCCCAllModules(Query):
    """
    Produce a list of all modules in the cccc module metrics for a
    specific project.
    """

    def run(self, project_id):
        sql = """SELECT DISTINCT cccc_module_metrics.path AS name
                 FROM
                 cccc_module_metrics JOIN
                 revision ON cccc_module_metrics.revision_id = revision.id JOIN
                 vcs ON revision.vcs_id = vcs.id JOIN
                 project ON vcs.project_id = project.id
                 WHERE project.id = %(project_id)s
                 ORDER BY cccc_module_metrics.path"""
        self.curs.execute(sql,
                {'project_id': project_id})
        self.res = self.curs.fetchall()
        self.get_project_name(project_id);
    
    def get_list(self):
        return [name[0] for name in self.res]

class StaticMetrics(Query):
    """
    Measures static metrics in a specific project, during a specific
    time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1)):
        sql = """SELECT static_metrics.sloc AS sloc,
                        static_metrics.ploc AS ploc,
                        static_metrics.bloc AS bloc,
                        static_metrics.cloc AS cloc,
                        static_metrics.nom AS nom,
                        static_metrics.cyclomatic AS cyclomatic,
                        static_metrics.fanin_tot AS fanin,
                        static_metrics.fanout_tot AS fanout,
                        static_metrics.type AS type,
                        revision.timestamp AS timestamp
                 FROM static_metrics JOIN
                      revision ON static_metrics.revision_id = revision.id JOIN
                      vcs ON revision.vcs_id = vcs.id JOIN
                      project ON vcs.project_id = project.id
                 WHERE
                      project.id = %(project_id)s AND
                      revision.timestamp >= %(start_time)s AND
                      revision.timestamp <= %(end_time)s
                 ORDER BY timestamp ASC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time})
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)

    def plot(self, type='both', sloc=False, ploc=False, bloc=False, cloc=False,
            nom=False, cyclomatic=False, fanin=False, fanout=False):
        clf()
        sloc_python_values = [y[0] for y in self.res if y[8] == 'python']
        sloc_c_values = [y[0] for y in self.res if y[8] == 'c']
        sloc_tot_values = map(add_or_zero, sloc_python_values,
                sloc_c_values)

        ploc_python_values = [y[1] for y in self.res if y[8] == 'python']
        ploc_c_values = [y[1] for y in self.res if y[8] == 'c']
        ploc_tot_values = map(add_or_zero, ploc_python_values,
                ploc_c_values)

        bloc_python_values = [y[2] for y in self.res if y[8] == 'python']
        bloc_c_values = [y[2] for y in self.res if y[8] == 'c']
        bloc_tot_values = map(add_or_zero, bloc_python_values,
                bloc_c_values)

        cloc_python_values = [y[3] for y in self.res if y[8] == 'python']
        cloc_c_values = [y[3] for y in self.res if y[8] == 'c']
        cloc_tot_values = map(add_or_zero, cloc_python_values,
                cloc_c_values)

        nom_python_values = [y[4] for y in self.res if y[8] == 'python']
        nom_c_values = [y[4] for y in self.res if y[8] == 'c']
        nom_tot_values = map(add_or_zero, nom_python_values,
                nom_c_values)

        cyclomatic_python_values = [y[5] for y in self.res if y[8] == 'python']
        cyclomatic_c_values = [y[5] for y in self.res if y[8] == 'c']
        cyclomatic_tot_values = map(add_or_zero,
                cyclomatic_python_values, cyclomatic_c_values)

        fanin_python_values = [y[6] for y in self.res if y[8] == 'python']
        fanin_c_values = [y[6] for y in self.res if y[8] == 'c']
        fanin_tot_values = map(add_or_zero, fanin_python_values,
                fanin_c_values)

        fanout_python_values = [y[7] for y in self.res if y[8] == 'python']
        fanout_c_values = [y[7] for y in self.res if y[8] == 'c']
        fanout_tot_values = map(add_or_zero, fanout_python_values,
                fanout_c_values)

        timestamps_python = [date2num(x[9]) for x in self.res
                if x[8] == 'python']
        timestamps_c = [date2num(x[9]) for x in self.res if x[8] == 'c']
        timestamps_tot = map(a_or_b, timestamps_python, timestamps_c)

        if sloc:
            if len(sloc_python_values) > 0:
                line1, = plot_date(timestamps_python, sloc_python_values)
                line1.set_label("SLOC: Python")
                line1.set_color('#00ff99')
            if len(sloc_c_values) > 0:
                line2, = plot_date(timestamps_c, sloc_c_values)
                line2.set_label("SLOC: C")
                line2.set_color('#0099ff')
            line3, = plot_date(timestamps_tot, sloc_tot_values)
            line3.set_label("SLOC")
            line3.set_color('r')
        if ploc:
            if len(ploc_python_values) > 0:
                line1, = plot_date(timestamps_python, ploc_python_values)
                line1.set_label("PLOC: Python")
            if len(ploc_c_values) > 0:
                line2, = plot_date(timestamps_c, ploc_c_values)
                line2.set_label("SLOC: C")
            line3, = plot_date(timestamps_tot, ploc_tot_values)
            line3.set_label("SLOC")
        if bloc:
            if len(bloc_python_values) > 0:
                line1, = plot_date(timestamps_python, bloc_python_values)
                line1.set_label("BLOC: Python")
                line1.set_color('g')
                line1.set_marker('v')
                line1.set_linestyle('-')
            if len(bloc_c_values) > 0:
                line2, = plot_date(timestamps_c, bloc_c_values)
                line2.set_label("BLOC: C")
                line2.set_color('g')
                line2.set_marker('x')
                line2.set_linestyle('-')
            line3, = plot_date(timestamps_tot, bloc_tot_values)
            line3.set_label("BLOC")
            line3.set_color('g')
            line3.set_marker('o')
            line3.set_linestyle('-')
        if cloc:
            if len(cloc_python_values) > 0:
                line1, = plot_date(timestamps_python, cloc_python_values)
                line1.set_label("CLOC: Python")
            if len(cloc_c_values) > 0:
                line2, = plot_date(timestamps_c, cloc_c_values)
                line2.set_label("CLOC: C")
            line3, = plot_date(timestamps_tot, cloc_tot_values)
            line3.set_label("CLOC")
        if nom:
            if len(nom_python_values) > 0:
                line1, = plot_date(timestamps_python, nom_python_values)
                line1.set_label("NOM: Python")
            if len(nom_c_values) > 0:
                line2, = plot_date(timestamps_c, nom_c_values)
                line2.set_label("NOM: C")
            line3, = plot_date(timestamps_tot, nom_tot_values)
            line3.set_label("NOM")
        if cyclomatic:
            if len(cyclomatic_python_values) > 0:
                line1, = plot_date(timestamps_python, cyclomatic_python_values)
                line1.set_label("CYC: Python")
            if len(cyclomatic_c_values) > 0:
                line2, = plot_date(timestamps_c, cyclomatic_c_values)
                line2.set_label("CYC: C")
            line3, = plot_date(timestamps_tot, cyclomatic_tot_values)
            line3.set_label("CYC")
        if fanin:
            if len(fanin_python_values) > 0:
                line1, = plot_date(timestamps_python, fanin_python_values)
                line1.set_label("FANIN: Python")
            if len(fanin_c_values) > 0:
                line2, = plot_date(timestamps_c, fanin_c_values)
                line2.set_label("FANIN: C")
            line3, = plot_date(timestamps_tot, fanin_tot_values)
            line3.set_label("FANIN")
        if fanout:
            if len(fanout_python_values) > 0:
                line1, = plot_date(timestamps_python, fanout_python_values)
                line1.set_label("FANOUT: Python")
            if len(fanout_c_values) > 0:
                line2, = plot_date(timestamps_c, fanout_c_values)
                line2.set_label("FANOUT: C")
            line3, = plot_date(timestamps_tot, fanout_tot_values)
            line3.set_label("FANOUT")

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        show()

    def plot_sloc_per_nom(self):
        clf()
        sloc_python_values = [y[0] for y in self.res if y[8] == 'python']
        sloc_c_values = [y[0] for y in self.res if y[8] == 'c']
        sloc_tot_values = map(add_or_zero, sloc_python_values, sloc_c_values)

        nom_python_values = [y[4] for y in self.res if y[8] == 'python']
        nom_c_values = [y[4] for y in self.res if y[8] == 'c']
        nom_tot_values = map(add_or_zero, nom_python_values, nom_c_values)

        timestamps_python = [date2num(x[9]) for x in self.res
                if x[8] == 'python']
        timestamps_c = [date2num(x[9]) for x in self.res if x[8] == 'c']
        timestamps_tot = map(a_or_b, timestamps_python, timestamps_c)

        sloc_per_nom_values = map(divide_or_zero, sloc_tot_values,
                nom_tot_values)

        line, = plot_date(timestamps_tot, sloc_per_nom_values)
        line.set_label("SLOC/NOM")
        line.set_color('#ff7f00')
        line.set_marker('.')
        line.set_linestyle('-')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

    def plot_cyclomatic_per_nom(self):
        clf()
        cyclomatic_python_values = [y[5] for y in self.res if y[8] == 'python']
        cyclomatic_c_values = [y[5] for y in self.res if y[8] == 'c']
        cyclomatic_tot_values = map(add_or_zero, cyclomatic_python_values,
                cyclomatic_c_values)

        nom_python_values = [y[4] for y in self.res if y[8] == 'python']
        nom_c_values = [y[4] for y in self.res if y[8] == 'c']
        nom_tot_values = map(add_or_zero, nom_python_values, nom_c_values)

        timestamps_python = [date2num(x[9]) for x in self.res
                if x[8] == 'python']
        timestamps_c = [date2num(x[9]) for x in self.res if x[8] == 'c']
        timestamps_tot = map(a_or_b, timestamps_python, timestamps_c)

        cyclomatic_per_nom_values = map(divide_or_one, cyclomatic_tot_values,
                nom_tot_values)

        line, = plot_date(timestamps_tot, cyclomatic_per_nom_values)
        line.set_label("CYC/NOM")
        line.set_color('#7f00ff')
        line.set_marker('.')
        line.set_linestyle('-')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

    def plot_fanin_fanout_per_sloc(self):
        clf()
        fanin_python_values = [y[6] for y in self.res if y[8] == 'python']
        fanin_c_values = [y[6] for y in self.res if y[8] == 'c']
        fanin_tot_values = map(add_or_zero, fanin_python_values,
                fanin_c_values)

        fanout_python_values = [y[7] for y in self.res if y[8] == 'python']
        fanout_c_values = [y[7] for y in self.res if y[8] == 'c']
        fanout_tot_values = map(add_or_zero, fanout_python_values,
                fanout_c_values)

        sloc_python_values = [y[0] for y in self.res if y[8] == 'python']
        sloc_c_values = [y[0] for y in self.res if y[8] == 'c']
        sloc_tot_values = map(add_or_zero, sloc_python_values, sloc_c_values)

        timestamps_python = [date2num(x[9]) for x in self.res
                if x[8] == 'python']
        timestamps_c = [date2num(x[9]) for x in self.res if x[8] == 'c']
        timestamps_tot = map(a_or_b, timestamps_python, timestamps_c)

        fanin_per_sloc_values = map(divide_or_zero, fanin_tot_values,
                sloc_tot_values)
        fanout_per_sloc_values = map(divide_or_zero, fanout_tot_values,
                sloc_tot_values)

        line1, = plot_date(timestamps_tot, fanin_per_sloc_values)
        line1.set_label("FANIN/SLOC")
        line1.set_color('#80ff00')
        line2, = plot_date(timestamps_tot, fanout_per_sloc_values)
        line2.set_label("FANOUT/SLOC")
        line2.set_color('#7f00ff')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        axis('tight')
        show()

class StaticModuleMetrics(Query):
    """
    Measures static module metrics in a specific project, during specific
    time interval, and for a specific set of modules, given as a sequence
    to the plot method.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1), prefixes=[]):
        sql = """SELECT static_module_metrics.path AS path,
                        static_module_metrics.sloc AS sloc,
                        static_module_metrics.ploc AS ploc,
                        static_module_metrics.bloc AS bloc,
                        static_module_metrics.cloc AS cloc,
                        static_module_metrics.cyclomatic AS cyclomatic,
                        static_module_metrics.fanin AS fanin,
                        static_module_metrics.fanout AS fanout,
                        revision.timestamp AS timestamp
                 FROM static_module_metrics JOIN
            revision ON static_module_metrics.revision_id = revision.id JOIN
            vcs ON revision.vcs_id = vcs.id JOIN
            project ON vcs.project_id = project.id
            WHERE project.id = %(project_id)s AND
                  revision.timestamp >= %(start_time)s AND
                  revision.timestamp <= %(end_time)s AND ("""
        for prefix in prefixes:
            sql += """static_module_metrics.path LIKE '%s%%%%' OR """ % (prefix)
        if len(prefixes) > 0:
            sql = sql[:-3] + ") "
        else:
            sql = sql[:-5]
        sql += """ORDER BY timestamp ASC"""
        self.curs.execute(sql,
                {'project_id': project_id,
                    'start_time': start_time,
                    'end_time': end_time})
        self.res = self.curs.fetchall()
        self.get_project_name(project_id)
    
    def plot(self, prefixes, sloc=False, ploc=False, bloc=False, cloc=False,
            cyclomatic=False, fanin=False, fanout=False):
        clf()
        data = {}
        for prefix, marker in prefixes:
            for res in self.res:
                if res[0].startswith(prefix):
                    if not data.has_key(prefix):
                        data[prefix] = {}
                    if not data[prefix].has_key(res[8]):
                        data[prefix][res[8]] = (prefix, marker, 0,0,0,0,0,0,0)
                    data[prefix][res[8]] = (prefix, marker,
                            data[prefix][res[8]][2] + res[1],
                            data[prefix][res[8]][3] + res[2],
                            data[prefix][res[8]][4] + res[3],
                            data[prefix][res[8]][5] + res[4],
                            data[prefix][res[8]][6] + res[5],
                            data[prefix][res[8]][7] + res[6],
                            data[prefix][res[8]][8] + res[7])

        for metric in ( (1, sloc, "SLOC", 'r', '-'),
                (2, ploc, "PLOC", 'b', '-'),
                (3, bloc, "BLOC", 'g', '-'),
                (4, cloc, "CLOC", 'y', '-'),
                (5, cyclomatic, "CYC", 'r', '-'),
                (6, fanin, "FANIN", 'r', '-'),
                (7, fanout, "FANOUT", 'y', '-')):
            for prefix in data.keys():
                timestamps = data[prefix].keys()
                timestamps.sort()
                timestamps_coords = [date2num(ts) for ts in timestamps]
                metric_values = [x[metric[0]+1] for x in
                        [data[prefix][ts] for ts in timestamps]]

                if metric[1]:
                    line, = plot_date(timestamps_coords, metric_values)
                    line.set_label("%s: %s" %(metric[2], prefix))
                    line.set_color(metric[3])
                    line.set_linestyle(metric[4])
                    line.set_marker(data[prefix][data[prefix].keys()[0]][1])

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        ax = gca()
        ax.yaxis.set_major_formatter(majorFormatter)
        show()

class BugFreqPerCommitFreq(Query):
    """
    Measures the number of bugs per SLOC in a specific project, during a
    specific time interval.
    """

    def run(self, project_id, start_time=datetime(1000, 1, 1),
            end_time=datetime(3000, 1, 1), freq_window=timedelta(days=1)):
        cf = CommitFrequency()
        bf = BugFrequency()

        cf.run(project_id, start_time, end_time, freq_window)
        bf.run(project_id, start_time, end_time, freq_window)
        
        self.res = []

        for i in range(0, len(cf.res)):
            # print cf.res[i][0], bf.res[i][1], cf.res[i][1]
            if cf.res[i][1] == 0:
                value = bf.res[i][1]
            else:
                value = float(bf.res[i][1]) / float(cf.res[i][1])
            self.res.append((cf.res[i][0], value))

        self.get_project_name(project_id)
        self.freq_window = freq_window

    def plot(self):
        clf()
        values = [y[1] for y in self.res]
        #timestamps = [date2num(x[0]) for x in self.res]
        timestamps = [x[0] for x in self.res]

        line, = plot_date(timestamps, values)
        line.set_label("Bug frequency per commit frequency per %d days" % \
                self.freq_window.days)
        line.set_marker('.')
        line.set_linestyle('-')

        xlabel("Timestamp")
        ylabel("Metric value")
        title(self.project_name)
        legend(loc='best', markerscale=1.0, shadow=True)
        # plot a horizontal line at y=1
        axhline(y=1, color='k', linestyle='--')
        v = axis('auto')
        v2 = axis('tight')
        axis((v2[0], v2[1], v[2], v[3]))
        show()

def add_or_zero(a, b):
    if a and b:
        return a + b
    elif a:
        return a
    elif b:
        return b
    else:
        return 0

def divide_or_one(a, b):
    if a and b and b > 0:
        return float(a) / float(b)
    else:
        return 1

def divide_or_zero(a, b):
    if a and b and b > 0:
        return float(a) / float(b)
    else:
        return 0

def a_or_b(a, b):
    if a:
        return a
    elif b:
        return b
    else:
        return None

if __name__ == '__main__':
    for QueryClass in (CommitsPerAuthor,
            CommitsPerAuthorHistogram,
            PostsPerAuthor,
            PostsPerAuthorHistogram,
            BugsPerAuthor,
            BugsPerAuthorHistogram):
        query = QueryClass()
        query.run(project_id = 3)
        query.plot()
        sleep(3)
    
    q = StaticModuleMetrics()
    q.run(3)
    q.plot(fanin=True, fanout=True, prefixes=(
        ("/source/gameengine", 'x'),
        ("/source/blender/blenlib", 'v'),
        ("/source/blender/blenkernel", 'o') ))
    sleep(3)
