"""Not a serious example.
Usage:
  phpbb ( read | work | reflection ) ...
  phpbb --version
Examples:
  phpbb read all
  phpbb reflection all
  phpbb work all
  phpbb read all work all reflection all
"""
from woof import woof
from docopt import docopt
import mysql.connector
from collections import defaultdict
from datetime import datetime, timedelta

sql_query = """
    SELECT phpbb_users.username, DATE(FROM_UNIXTIME(phpbb_posts.`post_time`)) AS date, COUNT(phpbb_posts.post_id) AS post_count
    FROM phpbb_posts, phpbb_topics, phpbb_users
    WHERE phpbb_topics.forum_id = phpbb_posts.forum_id
    AND phpbb_posts.topic_id = phpbb_topics.topic_id
    AND phpbb_users.user_id = phpbb_topics.topic_poster
    AND phpbb_posts.forum_id = %s
    AND phpbb_users.user_inactive_reason = 0
    AND phpbb_users.group_id = 2
    AND FROM_UNIXTIME(phpbb_posts.`post_time`) > DATE_SUB(now(), INTERVAL 1 WEEK)
    GROUP BY phpbb_users.username, DATE(FROM_UNIXTIME(phpbb_posts.`post_time`)); 
"""


def last_7_days():
    dates = []
    for i in range(0, 7):
        c_day = datetime.today() - timedelta(i)
        dates.append(c_day)
    return dates


def table_headers():
    heading_row = ["X"]
    for c_day in last_7_days():
        heading_row.append(f"{c_day.day}-{c_day.strftime('%B')[0:3]}")
    heading_row.extend(["Total Miss Days", "Total Posts"])
    return heading_row


def format_stats(user_data):
    table_body = []
    for key, value in user_data.items():
        user_row = [key]
        total_count = 0
        total_miss = 0
        for c_day in last_7_days():
            flag = True
            for i in value:
                if list(i.keys())[0] == f'{c_day.day}-{c_day.strftime("%B")[0:3]}':
                    flag = False
                    user_row.append(i[list(i.keys())[0]])
                    total_count = total_count + int(i[list(i.keys())[0]])
                    break
            if flag:
                total_miss = total_miss + 1
                user_row.append(0)
        user_row.append(total_miss)
        user_row.append(total_count)
        table_body.append(user_row)
    return table_body


def read_stats(stat="read"):
    global sql_query
    dataBase = mysql.connector.connect(
        host="hostIP",
        user="username",
        passwd="password",
        database="databasename",
    )
    user_data = defaultdict(list)
    cursor = dataBase.cursor()
    if stat == "read":
        sql_query_filled = sql_query % "4"
    elif stat == "reflection":
        sql_query_filled = """
                                select  phpbb_users .username ,  DATE(FROM_UNIXTIME(phpbb_posts.`post_time`)) AS date,COUNT(*) as session_count
                                from phpbb_posts,phpbb_users
                                WHERE  phpbb_posts.forum_id =3
                                and phpbb_posts.post_text NOT LIKE "%QUOTE author%"
                                and phpbb_users.user_id = phpbb_posts.poster_id
                                AND FROM_UNIXTIME(phpbb_posts.`post_time`) > DATE_SUB(now(), INTERVAL 1 WEEK)
                                GROUP BY phpbb_users.username ,DATE(FROM_UNIXTIME(phpbb_posts.`post_time`))
"""
    else:
        sql_query_filled = sql_query % "5"
    cursor.execute(sql_query_filled)
    for row in cursor:
        user_data[row[0]].append({f'{row[1].day}-{row[1].strftime("%B")[0:3]}': row[2]})
    return user_data


@woof("phpbb", html_template="phpbb/template.html")
def phpbb(*args):
    """Reading stats: phpbb read (option for week[1 to 52 or -1])
    Exercise/workout stats: phpbb work 
    Reflections stats: phpbb reflection """

    try:
        arguments = docopt(__doc__,argv=list(args),version="0.0.1")
    except:
        return {"Error, couldn't recognize command": __doc__}
    
    if arguments["read"] == True:
        print("read")
        user_stats = read_stats(stat="read")
    elif arguments["work"] == True:
        print("work")
        user_stats = read_stats(stat="work")
    elif arguments["reflection"] == True:
        print("reflection")
        user_stats = read_stats(stat="reflection")
    table_body = format_stats(user_stats)
    return {"table_header": table_headers(), "table_body": table_body}

