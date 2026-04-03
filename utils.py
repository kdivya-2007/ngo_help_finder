import sqlite3
import math
def get_ngos_by_district(user_input):
    conn=sqlite3.connect("NGO.db")
    cursor=conn.cursor()
    cursor.execute("select * from NGO where district=?",(user_input,))
    rows=cursor.fetchall()
    conn.close()
    return rows
def haversine(lat1, lon1, lat2, lon2):
    R = 6371

    lat1 = math.radians(lat1)
    lon1 = math.radians(lon1)
    lat2 = math.radians(lat2)
    lon2 = math.radians(lon2)

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))

    return R * c
