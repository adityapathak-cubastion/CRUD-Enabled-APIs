### Aditya Pathak | Technology used: PostgreSQL (PgAdmin4), Python (Flask-SQLAlchemy), Postman API

### Importing Required Libraries

from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

### Setting up Flask app

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost:5432/Company'
db = SQLAlchemy(app)
app.app_context().push()

### Defining tables

class Employee(db.Model):
    __tablename__ = 'Employee'
    Fname = db.Column(db.String())
    Lname = db.Column(db.String())
    Ssn = db.Column(db.Integer(), primary_key = True)
    Bdate = db.Column(db.Date())
    Address = db.Column(db.String())
    Sex = db.Column(db.String())
    Salary = db.Column(db.Integer())
    Super_ssn = db.Column(db.Integer(), db.ForeignKey('Employee.Ssn'))
    Dno = db.Column(db.Integer(), db.ForeignKey('Department.Dnumber'))

    department = db.relationship('Department', back_populates = 'employees', foreign_keys = [Dno])
    projects = db.relationship('Project', secondary = 'Works_On', back_populates = 'employees')
    supervisor = db.relationship('Employee', remote_side = [Ssn], foreign_keys = [Super_ssn])

    def __init__(self, Fname, Lname, Ssn, Bdate, Address, Sex, Salary, Super_ssn, Dno):
        self.Fname = Fname
        self.Lname = Lname
        self.Ssn = Ssn
        self.Bdate = Bdate
        self.Address = Address
        self.Sex = Sex
        self.Salary = Salary
        self.Super_ssn = Super_ssn
        self.Dno = Dno

class Department(db.Model):
    __tablename__ = 'Department'
    Dname = db.Column(db.String())
    Dnumber = db.Column(db.Integer(), primary_key = True)
    Mgr_ssn = db.Column(db.Integer(), db.ForeignKey('Employee.Ssn'))
    Mgr_start_date = db.Column(db.Date())

    employees = db.relationship('Employee', back_populates = 'department', foreign_keys = [Employee.Dno])
    projects = db.relationship('Project', back_populates = 'department')
    manager = db.relationship('Employee', foreign_keys = [Mgr_ssn])

    def __init__(self, Dname, Dnumber, Mgr_ssn, Mgr_start_date):
        self.Dname = Dname
        self.Dnumber = Dnumber
        self.Mgr_ssn = Mgr_ssn
        self.Mgr_start_date = Mgr_start_date

class Dept_Locations(db.Model):
    __tablename__ = 'Dept_Locations'
    Dnumber = db.Column(db.Integer(), db.ForeignKey('Department.Dnumber'), primary_key = True)
    Dlocation = db.Column(db.String(), primary_key = True)

    def __init__(self, Dnumber, Dlocation):
        self.Dnumber = Dnumber
        self.Dlocation = Dlocation

class Project(db.Model):
    __tablename__ = 'Project'
    Pname = db.Column(db.String())
    Pnumber = db.Column(db.Integer(), primary_key = True)
    Plocation = db.Column(db.String())
    Dnum = db.Column(db.Integer(), db.ForeignKey('Department.Dnumber'))

    department = db.relationship('Department', back_populates = 'projects', foreign_keys = [Dnum])
    employees = db.relationship('Employee', secondary = 'Works_On', back_populates = 'projects')

    def __init__(self, Pname, Pnumber, Plocation, Dnum):
        self.Pname = Pname
        self.Pnumber = Pnumber
        self.Plocation = Plocation
        self.Dnum = Dnum

class Works_On(db.Model):
    __tablename__ = 'Works_On'
    Essn = db.Column(db.Integer(), db.ForeignKey('Employee.Ssn'), primary_key = True)
    Pno = db.Column(db.Integer(), db.ForeignKey('Project.Pnumber'), primary_key = True)
    Hours = db.Column(db.Integer())

    def __init__(self, Essn, Pno, Hours):
        self.Essn = Essn
        self.Pno = Pno
        self.Hours = Hours

class Dependent(db.Model):
    __tablename__ = 'Dependent'
    Essn = db.Column(db.Integer(), db.ForeignKey('Employee.Ssn'), primary_key = True)
    Dependent_name = db.Column(db.String(), primary_key = True)
    Sex = db.Column(db.String())
    Bdate = db.Column(db.Date())
    Relationship = db.Column(db.String())

    def __init__(self, Essn, Dependent_name, Sex, Bdate, Relationship):
        self.Essn = Essn
        self.Dependent_name = Dependent_name
        self.Sex = Sex
        self.Bdate = Bdate
        self.Relationship = Relationship

### Defining APIs

@app.route('/')
def index():
    return render_template('index.html')

### For each department whose average employee salary is more than $30,000, retrieve the department name and the number of employees working for that department.

@app.route('/high_dept_salary', methods = ['GET'])
def high_dept_salary():
    try:
        res = db.session.query(Department.Dname, db.func.count(Employee.Ssn).label('num_employees')).join(Employee, Employee.Dno == Department.Dnumber).group_by(Department.Dname).having(db.func.avg(Employee.Salary) > 30000).all()
        
        highSalaryDepartments = [{
            "Department Name" : result.Dname,
            "Number of Employees" : result.num_employees
            } for result in res]

        return jsonify(highSalaryDepartments), 200
    except Exception as e:
        return jsonify({"Message" : "Error retrieving departments with salaries greater than $30,000.", "Error" : str(e)}), 500

### A view that has the department name, its manager's name, number of employees working in that department, and the number of projects controlled by that department (for each department).

@app.route('/dept_details', methods = ['GET'])
def dept_details():
    try:
        employeeCount = db.session.query(Employee.Dno, db.func.count(Employee.Ssn).label('num_employees')).group_by(Employee.Dno).subquery()

        res = db.session.query(Department.Dname, Employee.Fname.label('Manager_Fname'), Employee.Lname.label('Manager_Lname'), employeeCount.c.num_employees, db.func.count(Project.Pnumber).label('num_projects')).join(Employee, Department.Mgr_ssn == Employee.Ssn).outerjoin(Project, Project.Dnum == Department.Dnumber).outerjoin(employeeCount, Department.Dnumber == employeeCount.c.Dno).group_by(Department.Dname, Employee.Fname, Employee.Lname, employeeCount.c.num_employees).all()

        view = [{
            "Department Name": result.Dname,
            "Manager Name": f"{result.Manager_Fname} {result.Manager_Lname}",
            "Number of Employees": result.num_employees,
            "Number of Projects": result.num_projects
            } for result in res]
        
        return jsonify(view), 200
    except Exception as e:
        return jsonify({"Message": "Error retrieving department details.", "Error": str(e)}), 500

### A view that has the project name, controlling department name, number of employees working on the project, and the total hours per week they work on the project (for each project).

@app.route('/project_details', methods = ['GET'])
def project_details():
    try:
        res = db.session.query(Project.Pname, Department.Dname, db.func.count(Employee.Ssn).label('num_employees'), db.func.coalesce(db.func.sum(Works_On.Hours), 0).label('total_hours')).join(Department, Project.Dnum == Department.Dnumber).outerjoin(Works_On, Works_On.Pno == Project.Pnumber).outerjoin(Employee, Works_On.Essn == Employee.Ssn).group_by(Project.Pname, Department.Dname).all()

        view = [{
            "Project Name": result.Pname,
            "Controlling Department": result.Dname,
            "Number of Employees": result.num_employees,
            "Total Hours": result.total_hours
        } for result in res]
        
        return jsonify(view), 200
    except Exception as e:
        return jsonify({"Message": "Error retrieving project details.", "Error": str(e)}), 500

### A view that has the project name, controlling department name, number of employees, and total hours worked per week on the project for each project with more than one employee working on it.

@app.route('/projects_multiple_employees', methods = ['GET'])
def projects_multiple_employees():
    try:
        res = db.session.query(Project.Pname, Department.Dname, db.func.count(Employee.Ssn).label('num_employees'), db.func.sum(Works_On.Hours).label('total_hours')).join(Department, Project.Dnum == Department.Dnumber).outerjoin(Works_On, Works_On.Pno == Project.Pnumber).outerjoin(Employee, Works_On.Essn == Employee.Ssn).group_by(Project.Pname, Department.Dname).having(db.func.count(Employee.Ssn) > 1).all()

        view = [{
            "Project Name": result.Pname,
            "Controlling Department": result.Dname,
            "Number of Employees": result.num_employees,
            "Total Hours": result.total_hours
        } for result in res]
        
        return jsonify(view), 200
    except Exception as e:
        return jsonify({"Message": "Error retrieving projects with multiple employees.", "Error": str(e)}), 500

### A view that has the employee name, employee salary, department that the employee works in, department manager name, manager salary, and average salary for the department.

@app.route('/employee_manager_details', methods = ['GET'])
def employee_manager_details():
    try:
        managerSubquery = db.session.query(Department.Dnumber.label('Dept_No'), Employee.Fname.label('Manager_Fname'), Employee.Lname.label('Manager_Lname'), Employee.Salary.label('Manager_Salary')).join(Employee, Department.Mgr_ssn == Employee.Ssn).subquery()

        res = db.session.query(Employee.Fname.label('Employee_Fname'), Employee.Lname.label('Employee_Lname'), Employee.Salary.label('Employee_Salary'), Department.Dname, managerSubquery.c.Manager_Fname, managerSubquery.c.Manager_Lname, managerSubquery.c.Manager_Salary, db.func.avg(Employee.Salary).over(partition_by = Employee.Dno).label('Avg_Salary')).join(Department, Employee.Dno == Department.Dnumber).join(managerSubquery, Employee.Dno == managerSubquery.c.Dept_No).all()

        view = [{
            "Employee Name": f"{result.Employee_Fname} {result.Employee_Lname}",
            "Employee Salary": result.Employee_Salary,
            "Department": result.Dname,
            "Manager Name": f"{result.Manager_Fname} {result.Manager_Lname}",
            "Manager Salary": result.Manager_Salary,
            "Average Salary": int(result.Avg_Salary)
        } for result in res]
        
        return jsonify(view), 200
    except Exception as e:
        return jsonify({"Message": "Error retrieving employee and manager details.", "Error": str(e)}), 500

### CRUD APIs for each table

# For Employee table

@app.route('/add_employee', methods = ['POST']) # Create functionality
def add_employee():
    if request.method == 'POST':
        data = request.get_json()
        Fname = data.get('Fname')
        Lname = data.get('Lname')
        Ssn = data.get('Ssn')
        Bdate = datetime.strptime(data.get('Bdate'), '%Y-%m-%d').date()
        Address = data.get('Address')
        Sex = data.get('Sex')
        Salary = data.get('Salary')
        Super_ssn = data.get('Super_ssn')
        Dno = data.get('Dno')

        employee = Employee(Fname, Lname, Ssn, Bdate, Address, Sex, Salary, Super_ssn, Dno)
        
        try:
            db.session.add(employee)
            db.session.commit()
            return jsonify({
                "Message": "Employee record added successfully!",
                "Employee": {
                    "First Name": Fname,
                    "Last Name": Lname,
                    "SSN": Ssn,
                    "Birthday": Bdate.strftime('%Y-%m-%d'),
                    "Address": Address,
                    "Sex": Sex,
                    "Salary": Salary,
                    "Super SSN": Super_ssn,
                    "Department Number": Dno
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'Message' : 'Error adding row.', 'Error' : str(e)}), 500

@app.route('/get_employee', methods = ['GET']) # Read functionality
def get_employee():
    # if request.method == 'GET': # Printing details of ALL employees/Printing all records
        #employees = Employee.query.all()
        # for employee in employees:
        #     print(employee.Fname, employee.Lname, ...................) # Can be extended to include all the records of the table
        # return jsonify({"message": "Employee names displayed!"}), 200
    if request.method == 'GET':    
        key = request.args.get('key')
        value = request.args.get('value')

        if not key or not value:
            return jsonify({"Error": "Both key and value are required."}), 400
        elif not hasattr(Employee, key):
                return jsonify({"Error": "Invalid key provided."}), 400
        
        try:
            if key in ['Ssn', 'Salary', 'Super_ssn', 'Dno']:
                value = int(value)
            elif key == "Bdate":
                value = datetime.strptime(value, '%Y-%m-%d').date()
            
            x = getattr(Employee, key)
            employee = db.session.query(Employee).filter(x == value).first()
            if employee:
                return jsonify({
                    "Message" : "Retrieved employee records!",
                    "Employee" : {
                        "First Name": employee.Fname,
                        "Last Name": employee.Lname,
                        "SSN": employee.Ssn,
                        "Birthday": employee.Bdate.strftime('%Y-%m-%d'),
                        "Address": employee.Address,
                        "Sex": employee.Sex,
                        "Salary": employee.Salary,
                        "Super SSN": employee.Super_ssn,
                        "Department Number": employee.Dno
                    }
                }), 200
            else:
                return jsonify({"Error": "Employee not found."}), 404
        except AttributeError:
            return jsonify({"Error": "Attribute Error!"}), 400
        except Exception as e:
            return jsonify({"Message": "Error fetching employee.", "Error": str(e)}), 500

@app.route('/update_employee/<int:Ssn>', methods = ['PUT']) # Update functionality
def update_employee(Ssn):
    if request.method == 'PUT':
        data = request.get_json()

        try:
            employee = db.session.query(Employee).filter(Employee.Ssn == Ssn).first()
            if not employee:
                return jsonify({"Error": "Employee not found."}), 404
            
            employee.Fname = data.get('Fname', employee.Fname)
            employee.Lname = data.get('Lname', employee.Lname)
            employee.Ssn = data.get('Ssn', employee.Ssn)
            employee.Bdate = datetime.strptime(data.get('Bdate'), '%Y-%m-%d').date() if data.get('Bdate') else employee.Bdate
            employee.Address = data.get('Address', employee.Address)
            employee.Sex = data.get('Sex', employee.Sex)
            employee.Salary = data.get('Salary', employee.Salary)
            employee.Super_ssn = data.get('Super_ssn', employee.Super_ssn)
            employee.Dno = data.get('Dno', employee.Dno)
            
            db.session.commit()
            
            return jsonify({"Message": "Employee record updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error updating employee.", "Error": str(e)}), 500

@app.route('/delete_employee/<int:Ssn>', methods = ['DELETE']) # Delete functionality
def delete_employee(Ssn):
    if request.method == 'DELETE':
        try:
            employee = db.session.query(Employee).filter(Employee.Ssn == Ssn).first()
            if not employee:
                return jsonify({"Error": "Employee not found."}), 404
            
            db.session.delete(employee)
            db.session.commit()
            
            return jsonify({"Message": "Employee record deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error deleting employee.", "Error": str(e)}), 500

# For Department table

@app.route('/add_department', methods = ['POST']) # Create functionality
def add_department():
    if request.method == 'POST':
        data = request.get_json()
        Dname = data.get('Dname')
        Dnumber = data.get('Dnumber')
        Mgr_ssn = data.get('Mgr_ssn')
        Mgr_start_date = datetime.strptime(data.get('Mgr_start_date'), '%Y-%m-%d').date()

        department = Department(Dname, Dnumber, Mgr_ssn, Mgr_start_date)
        
        try:
            db.session.add(department)
            db.session.commit()
            return jsonify({
                "Message": "Department record added successfully!",
                "Department": {
                    "Department Name": Dname,
                    "Department Number": Dnumber,
                    "Manager SSN": Mgr_ssn,
                    "Manager Start Date": Mgr_start_date.strftime('%Y-%m-%d')
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'Message' : 'Error adding row!', 'Error' : str(e)}), 500
        
@app.route('/get_department', methods = ['GET']) # Read functionality
def get_department():
    if request.method == 'GET':    
        key = request.args.get('key')
        value = request.args.get('value')

        if not key or not value:
            return jsonify({"Error": "Both key and value are required."}), 400
        elif not hasattr(Department, key):
            return jsonify({"Error": "Invalid key provided."}), 400
        
        try:
            if key in ['Dnumber', 'Mgr_ssn']:
                value = int(value)
            elif key == "Mgr_start_date":
                value = datetime.strptime(value, '%Y-%m-%d').date()
            
            x = getattr(Department, key)
            department = db.session.query(Department).filter(x == value).first()
            if department:
                return jsonify({
                    "Message" : "Retrieved department records!",
                    "Department" : {
                        "Department Name": department.Dname,
                        "Department Number": department.Dnumber,
                        "Manager SSN": department.Mgr_ssn,
                        "Manager Start Date": department.Mgr_start_date.strftime('%Y-%m-%d')
                    }
                }), 200
            else:
                return jsonify({"Error": "Department not found."}), 404
        except AttributeError:
            return jsonify({"Error": "Attribute Error!"}), 400
        except Exception as e:
            return jsonify({"Message": "Error fetching department.", "Error": str(e)}), 500

@app.route('/update_department/<int:Dnumber>', methods = ['PUT']) # Update functionality
def update_department(Dnumber):
    if request.method == 'PUT':
        data = request.get_json()

        try:
            department = db.session.query(Department).filter(Department.Dnumber == Dnumber).first()
            if not department:
                return jsonify({"Error": "Department not found."}), 404
            
            department.Dname = data.get('Dname', department.Dname)
            department.Dnumber = data.get('Dnumber', department.Dnumber)
            department.Mgr_start_date = datetime.strptime(data.get('Mgr_start_date'), '%Y-%m-%d').date() if data.get('Mgr_start_date') else department.Mgr_start_date
            department.Mgr_ssn = data.get('Mgr_ssn', department.Mgr_ssn)
            
            db.session.commit()
            
            return jsonify({"Message": "Department record updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error updating department.", "Error": str(e)}), 500

@app.route('/delete_department/<int:Dnumber>', methods = ['DELETE']) # Delete functionality
def delete_department(Dnumber):
    if request.method == 'DELETE':
        try:
            department = db.session.query(Department).filter(Department.Dnumber == Dnumber).first()
            if not department:
                return jsonify({"Error": "Department not found."}), 404
            
            db.session.delete(department)
            db.session.commit()
            
            return jsonify({"Message": "Department record deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error deleting department.", "Error": str(e)}), 500

# For Dept_Locations table

@app.route('/add_dept_location', methods = ['POST']) # Create functionality
def add_dept_location():
    if request.method == 'POST':
        data = request.get_json()
        Dnumber = data.get('Dnumber')
        Dlocation = data.get('Dlocation')

        dept_location = Dept_Locations(Dnumber, Dlocation)
        
        try:
            db.session.add(dept_location)
            db.session.commit()
            return jsonify({
                "Message": "Department location added successfully!",
                "Department Location": {
                    "Department Number": Dnumber,
                    "Department Location": Dlocation
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'Message' : 'Error adding row!', 'Error' : str(e)}), 500

@app.route('/get_dept_location', methods = ['GET']) # Read functionality
def get_dept_location():
    if request.method == 'GET':    
        key = request.args.get('key')
        value = request.args.get('value')

        if not key or not value:
            return jsonify({"Error": "Both key and value are required."}), 400
        elif not hasattr(Dept_Locations, key):
            return jsonify({"Error": "Invalid key provided."}), 400
        
        try:
            if key == "Dnumber":
                value = int(value)
            
            x = getattr(Dept_Locations, key)
            dept_location = db.session.query(Dept_Locations).filter(x == value).first()
            if dept_location:
                return jsonify({
                    "Message" : "Retrieved department location's records!",
                    "Department Location" : {
                        "Department Number": dept_location.Dnumber,
                        "Department Location": dept_location.Dlocation
                    }
                }), 200
            else:
                return jsonify({"Error": "Department location not found."}), 404
        except AttributeError:
            return jsonify({"Error": "Attribute Error!"}), 400
        except Exception as e:
            return jsonify({"Message": "Error fetching department location.", "Error": str(e)}), 500

@app.route('/update_dept_location', methods = ['PUT']) # Update functionality
def update_dept_location():
    if request.method == 'PUT':
        Dnumber = request.args.get('Dnumber')
        Dlocation = request.args.get('Dlocation')
        data = request.get_json()
        new_Dlocation = data.get('Dlocation')
        new_Dnumber = data.get('Dnumber')

        if not Dnumber and not Dlocation:
            return jsonify({"Error": "Either Department Number or Department Location is required."}), 400

        try:
            if Dnumber: # if Dnumber is provided
                dept_location = db.session.query(Dept_Locations).filter(Dept_Locations.Dnumber == int(Dnumber)).first()
                if not dept_location:
                    return jsonify({"Error": "Department location not found."}), 404
                dept_location.Dlocation = new_Dlocation if new_Dlocation else dept_location.Dlocation
                dept_location.Dnumber = new_Dnumber if new_Dnumber else dept_location.Dnumber

            else: # if Dlocation is provided
                dept_location = db.session.query(Dept_Locations).filter(Dept_Locations.Dlocation == Dlocation).first()
                if not dept_location:
                    return jsonify({"Error": "Department location not found."}), 404
                dept_location.Dlocation = new_Dlocation if new_Dlocation else dept_location.Dlocation
                dept_location.Dnumber = new_Dnumber if new_Dnumber else dept_location.Dnumber

            db.session.commit()
            return jsonify({"Message": "Department location updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error updating department location.", "Error": str(e)}), 500

@app.route('/delete_dept_location/', methods = ['DELETE']) # Delete functionality
def delete_dept_location():
    if request.method == 'DELETE':
        Dnumber = request.args.get('Dnumber')
        Dlocation = request.args.get('Dlocation')
        
        try:
            if Dnumber: # if Dnumber is provided
                department = db.session.query(Dept_Locations).filter(Dept_Locations.Dnumber == Dnumber).first()
                if not department:
                    return jsonify({"Error": "Department not found."}), 404
            
            elif Dlocation: # if Dlocation is provided
                department = db.session.query(Dept_Locations).filter(Dept_Locations.Dlocation == Dlocation).first()
                if not department:
                    return jsonify({"Error": "Department not found."}), 404
                
            db.session.delete(department)
            db.session.commit()
            
            return jsonify({"Message": "Department record deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error deleting department.", "Error": str(e)}), 500

# For Project table

@app.route('/add_project', methods = ['POST']) # Create functionality
def add_project():
    if request.method == 'POST':
        data = request.get_json()
        Pname = data.get('Pname')
        Pnumber = data.get('Pnumber')
        Plocation = data.get('Plocation')
        Dnum = data.get('Dnum')

        project = Project(Pname, Pnumber, Plocation, Dnum)
        
        try:
            db.session.add(project)
            db.session.commit()
            return jsonify({
                "Message": "Project record added successfully!",
                "Project": {
                    "Project Name": Pname,
                    "Project Number": Pnumber,
                    "Project Location": Plocation,
                    "Department Number": Dnum
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'Message' : 'Error adding row!', 'Error' : str(e)}), 500

@app.route('/get_project', methods = ['GET']) # Read functionality
def get_project():
    if request.method == 'GET':    
        key = request.args.get('key')
        value = request.args.get('value')

        if not key or not value:
            return jsonify({"Error": "Both key and value are required."}), 400
        elif not hasattr(Project, key):
            return jsonify({"Error": "Invalid key provided."}), 400
        
        try:
            if key in ['Pnumber', 'Dnum']:
                value = int(value)
            
            x = getattr(Project, key)
            project = db.session.query(Project).filter(x == value).first()
            if project:
                return jsonify({
                    "Message" : "Retrieved project records!",
                    "Project" : {
                        "Project Name": project.Pname,
                        "Project Number": project.Pnumber,
                        "Project Location": project.Plocation,
                        "Department Number": project.Dnum
                    }
                }), 200
            else:
                return jsonify({"Error": "Project not found."}), 404
        except AttributeError:
            return jsonify({"Error": "Attribute Error!"}), 400
        except Exception as e:
            return jsonify({"Message": "Error fetching project.", "Error": str(e)}), 500

@app.route('/update_project/<int:Pnumber>', methods = ['PUT']) # Update functionality
def update_project(Pnumber):
    if request.method == 'PUT':
        data = request.get_json()

        try:
            project = db.session.query(Project).filter(Project.Pnumber == Pnumber).first()
            if not project:
                return jsonify({"Message": "Project not found."}), 404
            
            project.Pname = data.get('Pname', project.Pname)
            project.Pnumber = data.get('Pnumber', project.Pnumber)
            project.Plocation = data.get('Plocation', project.Plocation)
            project.Dnum = data.get('Dnum', project.Dnum)
            
            db.session.commit()
            
            return jsonify({"Message": "Project record updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error updating project.", "error": str(e)}), 500

@app.route('/delete_project/<int:Pnumber>', methods = ['DELETE']) # Delete functionality
def delete_project(Pnumber):
    if request.method == 'DELETE':
        try:
            project = db.session.query(Project).filter(Project.Pnumber == Pnumber).first()
            if not project:
                return jsonify({"Error": "Project not found."}), 404
            
            db.session.delete(project)
            db.session.commit()
            
            return jsonify({"Message": "Project record deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error deleting Project.", "Error": str(e)}), 500

# For Works_On table

@app.route('/add_works_on', methods = ['POST']) # Create functionality
def add_works_on():
    if request.method == 'POST':
        data = request.get_json()
        Essn = data.get('Essn')
        Pno = data.get('Pno')
        Hours = data.get('Hours')

        works_on = Works_On(Essn, Pno, Hours)
        
        try:
            db.session.add(works_on)
            db.session.commit()
            return jsonify({
                "Message": "'Working on' record added successfully!",
                "Working On": {
                    "Employee SSN": Essn,
                    "Project Number": Pno,
                    "Hours": Hours
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'Message' : 'Error adding row!', 'Error' : str(e)}), 500

@app.route('/get_works_on', methods = ['GET']) # Read functionality
def get_works_on():
    if request.method == 'GET':    
        key = request.args.get('key')
        value = request.args.get('value')

        if not key or not value:
            return jsonify({"Error": "Both key and value are required."}), 400
        elif not hasattr(Works_On, key):
            return jsonify({"Error": "Invalid key provided."}), 400
        
        try:
            value = int(value) # Since Works_On table has only integer columns - Essn, Pno, Hours
            
            x = getattr(Works_On, key)
            works_on = db.session.query(Works_On).filter(x == value).first()
            if works_on:
                return jsonify({
                    "Message" : "Retrieved 'working on' records!",
                    "Working On" : {
                        "Employee SSN": works_on.Essn,
                        "Project Number": works_on.Pno,
                        "Hours" : works_on.Hours
                    }
                }), 200
            else:
                return jsonify({"Error": "'Working on' record not found."}), 404
        except AttributeError:
            return jsonify({"Error": "Attribute Error!"}), 400
        except Exception as e:
            return jsonify({"Message": "Error fetching 'working on' record.", "Error": str(e)}), 500

@app.route('/update_works_on', methods = ['PUT']) # Update functionality
def update_works_on():
    if request.method == 'PUT':
        Essn = request.args.get('Essn')
        Pno = request.args.get('Pno')
        data = request.get_json()
        new_Essn = data.get('Essn')
        new_Pno = data.get('Pno')
        new_Hours = data.get('Hours')

        if not Essn and not Pno:
            return jsonify({"Error": "Either Employee SSN or Project Number is required."}), 400

        try:
            if Essn: # if Essn is provide
                works_on = db.session.query(Works_On).filter(Works_On.Essn == int(Essn)).first()
                if not works_on:
                    return jsonify({"Error": "'Working on' record not found."}), 404
                works_on.Essn = new_Essn if new_Essn else works_on.Essn
                works_on.Pno = new_Pno if new_Pno else works_on.Pno
                works_on.Hours = new_Hours if new_Hours else works_on.Hours

            else: # if Pno is provided
                works_on = db.session.query(Works_On).filter(Works_On.Pno == int(Pno)).first()
                if not works_on:
                    return jsonify({"Error": "'Working on' record not found."}), 404
                works_on.Essn = new_Essn if new_Essn else works_on.Essn
                works_on.Pno = new_Pno if new_Pno else works_on.Pno
                works_on.Hours = new_Hours if new_Hours else works_on.Hours

            db.session.commit()
            return jsonify({"Message": "'Working on' record updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error updating 'working on' record.", "Error": str(e)}), 500

@app.route('/delete_works_on/', methods = ['DELETE']) # Delete functionality
def delete_works_on():
    if request.method == 'DELETE':
        Essn = request.args.get('Essn')
        Pno = request.args.get('Pno')
        
        try:
            if Essn: # if Essn is provided
                works_on = db.session.query(Works_On).filter(Works_On.Essn == int(Essn)).first()
                if not works_on:
                    return jsonify({"Error": "'Working on' record not found."}), 404
            
            elif Pno: # if Pno is provided
                works_on = db.session.query(Works_On).filter(Works_On.Pno == int(Pno)).first()
                if not works_on:
                    return jsonify({"Error": "'Working on' record not found."}), 404
                
            db.session.delete(works_on)
            db.session.commit()
            
            return jsonify({"Message": "'Working on' record record deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error deleting 'working on' record.", "Error": str(e)}), 500

# For Dependent table

@app.route('/add_dependent', methods = ['POST']) # Create functionality
def add_dependent():
    if request.method == 'POST':
        data = request.get_json()
        Essn = data.get('Essn')
        Dependent_name = data.get('Dependent_name')
        Sex = data.get('Sex')
        Bdate = datetime.strptime(data.get('Bdate'), '%Y-%m-%d').date()
        Relationship = data.get('Relationship')

        dependent = Dependent(Essn, Dependent_name, Sex, Bdate, Relationship)
        
        try:
            db.session.add(dependent)
            db.session.commit()
            return jsonify({
                "Message": "Dependent record added successfully!",
                "Dependent": {
                    "Employee SSN": Essn,
                    "Name of Dependent": Dependent_name,
                    "Sex": Sex,
                    "Birthday": Bdate.strftime('%Y-%m-%d'),
                    "Relationship": Relationship
                }
            }), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'Message' : 'Error adding row!', 'Error' : str(e)}), 500

@app.route('/get_dependent', methods = ['GET']) # Read functionality
def get_dependent():
    if request.method == 'GET':    
        key = request.args.get('key')
        value = request.args.get('value')

        if not key or not value:
            return jsonify({"Error": "Both key and value are required."}), 400
        elif not hasattr(Dependent, key):
            return jsonify({"Error": "Invalid key provided."}), 400
        
        try:
            if key == 'Essn':
                value = int(value)
            elif key == 'Bdate':
                value = datetime.strptime(value, '%Y-%m-%d').date()
            
            x = getattr(Dependent, key)
            dependent = db.session.query(Dependent).filter(x == value).first()
            if dependent:
                return jsonify({
                    "Message" : "Retrieved dependent records!",
                    "Dependent" : {
                        "Employee SSN": dependent.Essn,
                        "Name of dependent": dependent.Dependent_name,
                        "Sex" : dependent.Sex,
                        "Birthday": dependent.Bdate.strftime('%Y-%m-%d'),
                        "Relationship": dependent.Relationship
                    }
                }), 200
            else:
                return jsonify({"Error": "Dependent record not found."}), 404
        except AttributeError:
            return jsonify({"Error": "Attribute Error!"}), 400
        except Exception as e:
            return jsonify({"Message": "Error fetching dependent record.", "Error": str(e)}), 500

@app.route('/update_dependent', methods = ['PUT']) # Update functionality
def update_dependent():
    if request.method == 'PUT':
        Essn = request.args.get('Essn')
        Dependent_name = request.args.get('Dependent_name')
        data = request.get_json()

        if not Essn and not Dependent_name:
            return jsonify({"Error": "Either Employee SSN or Name of Dependent is required."}), 400

        try:
            if Essn: # if Essn is provided
                dependent = db.session.query(Dependent).filter(Dependent.Essn == int(Essn)).first()
                if not dependent:
                    return jsonify({"Error": "Dependent not found."}), 404
                
                dependent.Essn = data.get('Essn', dependent.Essn)
                dependent.Dependent_name = data.get('Dependent_name', dependent.Dependent_name)
                dependent.Sex = data.get('Sex', dependent.Sex)
                dependent.Bdate = datetime.strptime(data.get('Bdate'), '%Y-%m-%d').date() if data.get('Bdate') else dependent.Bdate
                dependent.Relationship = data.get('Relationship', dependent.Relationship)

            else: # if Dependent_name is provided
                dependent = db.session.query(Dependent).filter(Dependent.Dependent_name == Dependent_name).first()
                if not dependent:
                    return jsonify({"Error": "Dependent not found."}), 404
                
                dependent.Essn = data.get('Essn', dependent.Essn)
                dependent.Dependent_name = data.get('Dependent_name', dependent.Dependent_name)
                dependent.Sex = data.get('Sex', dependent.Sex)
                dependent.Bdate = datetime.strptime(data.get('Bdate'), '%Y-%m-%d').date() if data.get('Bdate') else dependent.Bdate
                dependent.Relationship = data.get('Relationship', dependent.Relationship)

            db.session.commit()
            return jsonify({"Message": "Dependent updated successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error updating dependent.", "Error": str(e)}), 500

@app.route('/delete_dependent/', methods = ['DELETE']) # Delete functionality
def delete_dependent():
    if request.method == 'DELETE':
        Essn = request.args.get('Essn')
        Dependent_name = request.args.get('Dependent_name')
        
        try:
            if Essn:
                dependent = db.session.query(Dependent).filter(Dependent.Essn == int(Essn)).first()
                if not dependent:
                    return jsonify({"Error": "Dependent record not found."}), 404
            
            elif Dependent_name:
                dependent = db.session.query(Dependent).filter(Dependent.Dependent_name == Dependent_name).first()
                if not dependent:
                    return jsonify({"Error": "Dependent record not found."}), 404
                
            db.session.delete(dependent)
            db.session.commit()
            
            return jsonify({"Message": "Dependent record record deleted successfully!"}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({"Message": "Error deleting dependent record.", "Error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug = True)

### (FOR FRONTEND - FORM SUBMISSION)
# def submit():
    # if request.method == 'POST':
    #     fname = request.form['fname']
    #     lname = request.form['lname']
    #     Ssn = request.form['Ssn']
    #     Bdate = request.form['Bdate']
    #     Address = request.form['Address']
    #     Sex = request.form['Sex']
    #     Salary = request.form['Salary']
    #     Super_ssn = request.form['Super_ssn']
    #     Dno = request.form['Dno']

    #     employee = Employee(fname, lname, Ssn, Bdate, Address, Sex, Salary, Super_ssn, Dno)
            
    #     try:
    #         db.session.add(employee)
    #         db.session.commit()
    #         return 'Employee record added successfully!'
    #     except:
    #         return 'Error adding row!'
