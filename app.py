#Import Dependencies
from flask import Flask, jsonify
import sqlalchemy
import numpy as np
import pandas as pd
import datetime as dt 

from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy.sql.functions import session_user
from sqlalchemy.sql.selectable import subquery

#Set up the engine and base to run
engine = create_engine("sqlite:///Instructions/Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

#Create classes - Measurement and station
Measurement= Base.classes.measurement
Station = Base.classes.station

# Flask Setup
app = Flask(__name__)


#################################################
# Flask Routes
#################################################

@app.route("/")
def welcome():
    '''
    This is the Homepage
    '''
    return (
        f"<h1>Welcome to my climate app</h1><br/>" 
        f"<h3>Available routes</h3><br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/2014-05-01  - please enter a date between <strong>2010-01-01  and 2017-08-23</strong> in that format<br/>"
        f"/api/v1.0/2014-05-01/2015-04-30 - please enter a <strong>start date and end date</strong> between <strong>2010-01-01 and 2017-08-23</strong> in that format "
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    '''
    This gives the precipitation in json format for date and precipitation in the last year
    '''
    session = Session(engine)
    
    lastdate = session.query(func.max(Measurement.date)).\
                    scalar()
    dt_lastdate= dt.datetime.strptime(lastdate,"%Y-%m-%d").date()
    dt_startdate = dt_lastdate - dt.timedelta(days=365)
    startdate = dt_startdate.strftime("%Y-%m-%d")
    results = session.query(Measurement.date, Measurement.prcp).\
            filter(Measurement.date.between(startdate,lastdate)).\
            all()
    
    session.close()
    
    precip = []
    for date, prcp in results:
            precip_dict ={}
            precip_dict['date'] = date
            precip_dict['prcp'] = prcp
            precip.append(precip_dict)
    return jsonify(precip)



@app.route("/api/v1.0/stations")
def stations():
    '''
    This will give a list of stations available to review
    '''
    session = Session(engine)

    results = session.query(Station.name).all()

    session.close()

    # Convert list of tuples into normal list
    all_stations = list(np.ravel(results))
    return jsonify(all_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    '''
    This will give the temperatures and dates for the alstyear for the station
    with the most observations
    '''
    session = Session(engine)

    top_station = session.query(Measurement.station).\
                    group_by(Measurement.station).\
                    order_by(func.count(Measurement.station).desc()).\
                    subquery()

    lastdate = session.query(func.max(Measurement.date)).\
                    scalar()
    dt_lastdate= dt.datetime.strptime(lastdate,"%Y-%m-%d").date()
    dt_startdate = dt_lastdate - dt.timedelta(days=365)
    startdate = dt_startdate.strftime("%Y-%m-%d")
    
    results = session.query(Measurement.date, Measurement.tobs).\
                filter(Measurement.date.between(startdate,lastdate)).\
                filter(Measurement.station.in_(top_station)).\
                all()
    session.close()

    topStation = []
    for date, tobs in results:
            tobs_dict ={}
            tobs_dict['date'] = date
            tobs_dict['tobs'] = tobs
            topStation.append(tobs_dict)
    return jsonify(topStation)


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def rangestart(start,end=None):
    '''
    This will give the minimum, the average and maximum temperature based on a set of dates
    If only the start date is given, the end date will be the last date of the database.
    If the start and end date are given, it will 
    '''
    session=Session(engine)
    if end == None:
        enddate = session.query(func.max(Measurement.date)).\
                    scalar()
    else:
        enddate = str(end)
    startdate = str(start)
    results = session.query(func.min(Measurement.tobs).label('min_temp'),
                            func.avg(Measurement.tobs).label('avg_temp'),
                            func.max(Measurement.tobs).label('max_temp')).\
                filter(Measurement.date.between(startdate,enddate)).first()
    session.close()
    datapoints = list(np.ravel(results))
    return jsonify(datapoints)



if __name__ == "__main__":
    app.run(debug=False)
