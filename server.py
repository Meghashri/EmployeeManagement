#!/usr/bin/python3

from flask import Flask, request, jsonify, render_template, make_response
from flask_restful import Resource, Api
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine

# APP creation and configuration ---
app = Flask(__name__)
api = Api(app)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///emp.db'
db = SQLAlchemy(app)
#-------------------------


#-----------Model.py : contains DB table description (schema)----
class WorkCountry(db.Model):
    region = db.Column(db.String(80), primary_key=True)

    def __init__(self, country):
        self.region = country


class LineOfService(db.Model):
    los = db.Column(db.String(80), primary_key=True)

    def __init__(self, los):
        self.los = los


class Employee1(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), db.ForeignKey('work_country.region'))
    line_of_service = db.Column(db.String(80), db.ForeignKey('line_of_service.los'))

    def __init__(self, id, firstname, lastname, country, los):
        self.id = id
        self.first_name = firstname
        self.last_name = lastname
        self.country = country
        self.line_of_service = los

db.create_all()
#-------------------------------------------------------------


#----------app.py : contains api definition-------------
db_connect = create_engine('sqlite:///emp.db')


def get_paginated_list(results, url, start, limit):
    start = int(start)
    limit = int(limit)
    count = len(results)
    if count < start or limit < 0:
        abort(404)
    # make response
    obj = {}
    obj['start'] = start
    obj['limit'] = limit
    obj['count'] = count
    # make URLs
    # make previous url
    if start == 1:
        obj['previous'] = ''
    else:
        start_copy = max(1, start - limit)
        limit_copy = start - 1
        obj['previous'] = url + '?start=%d&limit=%d' % (start_copy, limit_copy)
    # make next url
    if start + limit > count:
        obj['next'] = ''
    else:
        start_copy = start + limit
        obj['next'] = url + '?start=%d&limit=%d' % (start_copy, limit)
    # finally extract result according to bounds
    obj['results'] = results[(start - 1):(start - 1 + limit)]
    return obj


class Employees(Resource):
    def get(self):
        conn = db_connect.connect()  # connect to database
        query = conn.execute("select * from employee1")  # This line performs query and returns json result
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]

        return jsonify(get_paginated_list(
            result,
            '/employees',
           start=request.args.get('start', 1),
           limit=request.args.get('limit', 2)
        ))

    def post(self):
        conn = db_connect.connect()

        #print(request.json)
        emp_id = request.json['id']
        emp_LastName = request.json['last_name']
        emp_FirstName = request.json['first_name']
        emp_Country = request.json['country']
        emp_Los = request.json['line_of_service']
        try:
            conn.execute("PRAGMA foreign_keys=ON;")
            query = conn.execute("insert into employee1(id,first_name,last_name,country,line_of_service) values('{0}','{1}','{2}','{3}', \
                             '{4}')".format(emp_id, emp_FirstName, emp_LastName, emp_Country, emp_Los))

        except:
            print("Database Error")
            return make_response(jsonify({"Database Error": "Couldn't create record"}),500)

        return {'status': 'success'}


class Employees_Id(Resource):
    def get(self, employee_id):
        conn = db_connect.connect()
        query = conn.execute("select * from employee1 where id =%d " % int(employee_id))
        result = {'data': [dict(zip(tuple(query.keys()), i)) for i in query.cursor]}
        if (len(result['data']) == 0):
            return not_found("Employee")
        else:
            return jsonify(result)

class Territory_search(Resource):
    def get(self, territory_name):
        conn = db_connect.connect()
        query = conn.execute("select * from employee1 where country = %s" % '"'+str(territory_name)+'"')
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        if (len(result) == 0):
            return not_found("No Pwc Employees found in this territory=%s" % str(territory_name))
        else:
            return jsonify(get_paginated_list(
            result,
            '/territory_employees/'+(territory_name),
           start=request.args.get('start', 1),
           limit=request.args.get('limit', 2)
        ))

class Lineofservice_search(Resource):
    def get(self, line_of_service):
        conn = db_connect.connect()
        query = conn.execute("select * from employee1 where line_of_service = %s" % '"'+str(line_of_service)+'"')
        result =  [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        print(len(result))
        if len(result) == 0:
            return not_found("No Pwc Employees found in this line-of-service=%s" % str(line_of_service))
        else:
            return jsonify(get_paginated_list(
                result,
                '/lineofservice_employees/' + (line_of_service),
                start=request.args.get('start', 1),
                limit=request.args.get('limit', 2)
            ))

class EmployeeLastname_search(Resource):
    def get(self, employee_lastname):
        conn = db_connect.connect()
        query = conn.execute("select * from employee1 where last_name = %s" % '"'+str(employee_lastname)+'"')
        result = [dict(zip(tuple(query.keys()), i)) for i in query.cursor]
        if (len(result) == 0):
            return not_found("No Employee found with lastname=%s" % (employee_lastname))
        else:
            return jsonify(get_paginated_list(
                result,
                '/employeelastname_search/' + (employee_lastname),
                start=request.args.get('start', 1),
                limit=request.args.get('limit', 2)
            ))
#------------------------------------------------------------


#-----------------Routes.py : contains routes to every API-----------------
api.add_resource(Employees, '/employees')# Route_1
api.add_resource(Employees_Id, '/employees_search/<employee_id>')# Route_3
api.add_resource(Territory_search, '/territory_employees/<territory_name>')
api.add_resource(Lineofservice_search, '/lineofservice_employees/<line_of_service>')
api.add_resource(EmployeeLastname_search, '/employeelastname_search/<employee_lastname>')
#-------------------------------------------------------------------

@app.route('/')
def welcome():
    return render_template('index.html')


@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({error: 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True, port=8081, host='0.0.0.0')


