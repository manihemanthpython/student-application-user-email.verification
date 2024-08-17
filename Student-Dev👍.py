import tkinter as tk
from tkinter import messagebox
import mysql.connector
from mysql.connector import Error
from contextlib import closing
import bcrypt
import re
from PIL import ImageTk
from tkinter import Label
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
'----------------------------------------------------------------------------------------------------------'
              # Function to connect to the database
'----------------------------------------------------------------------------------------------------------'
def connect_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="srss_db",
        auth_plugin='mysql_native_password'
    )
    cursor =mysql.cursor(buffered=True)
 
'--------------------------------------------------------------------------------'
 # Passwode Valided 
    
def is_valid_password(password):
    has_upper = False
    has_lower = False
    
    if len(password) < 8:
        return False
    if not re.search(r'[a-zA-Z]', password):
        return False
    if not re.search(r'[0-9]', password):
        return False
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False
    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        if has_lower and has_upper:
            break
    if not (has_upper and has_lower):
        return False

    return True

'-----------------------------------------------------------------------------'
# Email verification generater
'*****************************************************************************'
def generate_verification_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

# Email sender Admin .
def send_verification_email(email, code):
    sender_email = "manibodapati5@gmail.com"   # Adimn Email ID
    sender_password = "jixn tmib lfyp thlt"    # this password we can setup in your goolge 2 step verification click APP password.
    
    subject = " User Registertion Email Verification"
    body = f"Your Verification Code Is :{code}"
    
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_bytes()
        server.sendmail(sender_email, email, text)
        server.quit()
        print("Verification email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
        
    
'-----------------------------------------------------------------------------------------------------------'
     # Function to register a new user
'-----------------------------------------------------------------------------------------------------------'  
pending_registrations = {}
def is_email_in_employee_table(Email_Id,role):
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM Employee_details WHERE Email_Id = %s and role = %s", (Email_Id,role))
    employee = cursor.fetchone()
    conn.close()
    return employee is not None

def register_user(username, password, email, designation, role):
    if not is_valid_password(password):
        messagebox.showerror("Error","Password must be at least 8 characters long, contain an alphabet, a numeric digit, and a special character.")
        return
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    try:
        verification_code = generate_verification_code()
        # Store user data in a temporary dictionary with the username as the key
        pending_registrations[username] = {
            'password': password,
            'email': email,
            'designation': designation,
            'role': role,
            'verification_code': verification_code
        }
        send_verification_email(email, verification_code)
        
        log_user_activity(username, "Registration", "Registered a new user")
        messagebox.showinfo("Success", "Registration successful  Please check your email for the verification code!")
        
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error registering user: {e}")

"-------------------------------------------------------------------------------------"
#  verification window  and  you email get a code  that valied or invalied check here. 
"-----------------------------------------------------------------------------------"       
def show_verification_form(username):
    verification_window = tk.Toplevel(root)
    verification_window.geometry('500x300')
    verification_window.resizable(False, False)
    verification_window.configure(bg='coral')
    verification_window.title("Email Verification")
    
    tk.Label(verification_window,text="Enter Verification Code").pack()
    verification_code_entry = tk.Entry(verification_window)
    verification_code_entry.pack()
      
    def verify():
        verification_code = verification_code_entry.get()
        if verify_code(username, verification_code):
            save_registration(username)
            messagebox.showinfo("Success", "Email verified and registration save Successfully.")
            verification_window.destroy()
        else:
            messagebox.showerror("Error", "Invaild verification code. Registation Faild.")
            pending_registrations.pop(username, None)    # Remove pending registation data
        
    tk.Button(verification_window, text="Verify",bg='lightgreen', command=verify).pack(pady=10)
"---------------------------------------------------------------------------------"
#  Function verification code checking
"-------------------------------------------------------------------------------------"    
def verify_code(username, code):
    user_data = pending_registrations.get(username)
    if user_data and user_data['verification_code'] ==code:
        return True
    return False
"-----------------------------------------------------------------------------------------"
# Function user registration save or not to depend upon on code verification
"------------------------------------------------------------------------------------------"
def save_registration(username):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        # Retrieve user data from the pending_registration dictionary
        user_data = pending_registrations.get(username)
        if user_data:
            sql = ("INSERT INTO users (username, password, email, designation, role)"
                   "VALUES(%s, %s, %s, %s, %s)")
            cursor.execute(sql, (username, user_data['password'], user_data['email'], user_data['designation'], user_data['role']))
            conn.commit()
            
            cursor.close()
            conn.close()
            
            # Remove the user from panding registration after Successful save
            pending_registrations.pop(username, None)
        else:
            messagebox.showerror("Error", "user data not found.")
            
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error varifying code: {e}")
                    

'----------------------------------------------------------------------------------------------------------'
    # Function to User Acitivity history
'***********************************************************************************************************'
def log_user_activity(username, activity_type, activity_details):
    try:
        conn = connect_db()
        cursor = conn.cursor()
         
        sql = "INSERT INTO activity_log (username, activity_type, activity_details) VALUES (%s, %s, %s)"
        cursor.execute(sql, (username, activity_type, activity_details))
        conn.commit()
        
        cursor.close()
        conn.close()
         
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error logging login attempt: {e}")
'**********************************-----------------------------------------************************************'       
 # Function to authenticate user login  
'----------------------------------*****************************************------------------------------------'     
def login_user(username, password, role):
    if not is_valid_password(password):
        messagebox.showerror("Error","Please check your password.")
        return
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        sql = "SELECT * FROM users WHERE username = %s  AND role = %s"
        cursor.execute(sql, (username, role))
        user = cursor.fetchone()
        
        if user:
            log_user_activity(username, "Login", "Login Successful")
            #return user
        else:
            log_user_activity(username, "Login", "Login Failed")    
        cursor.close()
        conn.close()
        
        return user
    
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")
        return None
'--------------------------------------------***************************************------------------------------------------'
 # Function to reset user password 
 
'******************************************************************************************************************************'  
def reset_password(username, new_password, designation):
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        print("Executing SQL for password reset")
        print(f"Username: {username}")
        print(f"New Password: {new_password}")
        print(f"Designation: {designation}")
        
        sql = "UPDATE users SET password = %s WHERE username = %s AND designation = %s"
        cursor.execute(sql, (new_password, username, designation))
        conn.commit()
        
        # Check if any rows were affected
        if  cursor.rowcount == 0:
            messagebox.showerror("Error", "No user found with the given details.")
        else:
            messagebox.showinfo("Success", "Password reset successful!")

        log_user_activity(username, "Reset password", "User Reset New password  Successful")
          
        cursor.close()
        conn.close()
           
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error resetting password: {e}")
'--------------------------------------------------------------------------------------------------'       
  # Function to register student details  
  
'/////////////////////////////////////////////////////////////////////////////////////////////////'  
  
def register_student_details():
    if users_role in ['Admin']:
        student_id = student_id_entry.get()
        full_name = Full_name_entry.get()
        age = Age_entry.get()
        gender = Gender_entry.get()
        group_name = Group_Name_entry.get()
        ph_no = Ph_no_entry.get()
        location = Location_entry.get()
        parent_name = Parent_Name_entry.get()
        parent_phno = Parent_Phno_entry.get()
        clg_branch_id = Clg_Branch_ID_entry.get()
        fees = Fees_entry.get()
    
    if not all([student_id, full_name, age, gender, group_name, ph_no, location, parent_name, parent_phno, clg_branch_id, fees]):
        messagebox.showerror("Error", "Please enter all fields")
        return
    
    try:
        age = int(age)
    except ValueError:
        messagebox.showerror("Error", "Age must be a number")
        return
    
    if not re.match(r'^\d{10}$', ph_no):
        messagebox.showerror("Error", "Phone number must be a 10-digit number")
        return
    if not re.match(r'^\d{10}$', parent_phno):
        messagebox.showerror("Error", "Parent phone number must be a 10-digit number")
        return
    
    try:
        fees = float(fees)
    except ValueError:
        messagebox.showerror("Error", "Fees must be a number")
        return
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        insert_query = ("INSERT INTO student_information "
                        "(student_id, full_name, age, gender, group_name, ph_no, location, parent_name, parent_phno, clg_branch_id, fees) "
                        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
        cursor.execute(insert_query, (student_id, full_name, age, gender, group_name, ph_no, location, parent_name, parent_phno, clg_branch_id, fees))
        conn.commit()
        log_user_activity(users_role, "Student Registration", f"Registered student{full_name} with ID {student_id}")
        cursor.close()
        conn.close()
        
        clear_entries()
        
        messagebox.showinfo("Success", "Student details saved successfully")
        
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")

'------------------------------------------------------------------------------------------------------------------------'
# Function to register student update details.

'-------------------------------------------------------------------------------------------------------------------------'  
def Update_Student_details():
    if users_role in ['Admin']:
        student_id = student_id_update.get()
        age = Age_update_entry.get()
        group_name = Group_Name_update_entry.get()
        ph_no = Ph_no_update_entry.get()
        location = Location_update_entry.get()
        parent_phno = Parent_Phno_update_entry.get()
        clg_branch_id = Clg_Branch_ID_update_entry.get()
        fees = Fees_update_entry.get()
        
    if not student_id:
        messagebox.showerror("Error", "Student ID is mandatory")
        return
    
    update_fields = []
    update_values = []
    
    if age:
        try:
            age = int(age)
            update_fields.append("age = %s")
            update_values.append(age)
        except ValueError:
            messagebox.showerror("Error", "Age must be a number")
            return
    if group_name:
        update_fields.append("group_name = %s")
        update_values.append(group_name)
    if ph_no:
        if re.match(r'^\d{10}$', ph_no):
            update_fields.append("ph_no = %s")
            update_values.append(ph_no)
        else:
            messagebox.showerror("Error", "Phone number must be a 10-digit number")
            return
    if location:
        update_fields.append("location = %s")
        update_values.append(location)
    if parent_phno:
        if re.match(r'^\d{10}$', parent_phno):
            update_fields.append("parent_phno = %s")
            update_values.append(parent_phno)
        else:
            messagebox.showerror("Error", "Parent phone number must be a 10-digit number")
            return
    if clg_branch_id:
        update_fields.append("clg_branch_id = %s")
        update_values.append(clg_branch_id)
    if fees:
        try:
            fees = float(fees)
            update_fields.append("fees = %s")
            update_values.append(fees)
        except ValueError:
            messagebox.showerror("Error", "Fees must be a numbers")
            return
    if not update_fields:
        messagebox.showerror("Error", "No fields to update.")
        return
    update_values.append(student_id)
    update_query = f"UPDATE student_information SET {', '.join(update_fields)} WHERE student_id = %s"
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        cursor.execute(update_query, tuple(update_values))
        conn.commit()
        
        if cursor.rowcount == 0:
            messagebox.showerror("Error", "No student found with the given ID.")
        else:
            messagebox.showinfo("Success", "Student details updated successfully")
        log_user_activity(users_role, "Student update", f"Updated student {student_id} details")
        cursor.close()
        conn.close()
        
        clear_entries()

    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")
        
def add_employee_details():
    if users_role in ['Admin']:
        employee_id = employee_id_entry.get()
        full_name = full_name_entry.get()
        age = age_entry.get()
        gender = gender_entry.get()
        department = department_entry.get()
        Email_Id = Email_Id_entry.get()
        phone_number = phone_number_entry.get()
        address = address_entry.get()
        role = role_entry.get()
        salary = salary_entry.get()

    # Validate mandatory fields
        if not all([employee_id, full_name, age, gender, department, Email_Id, phone_number, address, role, salary]):
            messagebox.showerror("Error", "Please enter all fields")
            return

    # Validate age
        try:
            age = int(age)
        except ValueError:
            messagebox.showerror("Error", "Age must be a number")
            return

    # Validate phone number
        if not  re.match(r'^\d{10}$',(phone_number)):
            messagebox.showerror("Error", "Phone number must be a 10-digit number")
            return

    # Validate salary
        try:
            salary = float(salary)
        except ValueError:
            messagebox.showerror("Error", "Salary must be a number")
            return

    # Insert into database
        try:
            conn = connect_db()
            cursor = conn.cursor()

            insert_query = ("INSERT INTO employee_details "
                            "(employee_id, full_name, age, gender, department, Email_Id, phone_number, address, role, salary) "
                            "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)")
            cursor.execute(insert_query, (employee_id, full_name, age, gender, department, Email_Id, phone_number, address, role, salary))
            conn.commit()

            log_user_activity(users_role, "Employee Registration", f"Registered employee {full_name} with ID {employee_id}")
            cursor.close()
            conn.close()

            clear_entries()
            messagebox.showinfo("Success", "Employee details saved successfully")

        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error connecting to MySQL: {e}")

def update_employee_details():
    if users_role in ['Admin']:
        employee_id = employee_id_update_entry.get()
        age = age_update_entry.get()
        department = department_update_entry.get()
        Email_Id = Email_Id_update_entry.get()
        phone_number = phone_number_update_entry.get()
        address = address_update_entry.get()
        role = role_update_entry.get()
        salary = salary_update_entry.get()

        if not employee_id:
            messagebox.showerror("Error", "Employee ID is mandatory")
            return

        update_fields = []
        update_values = []

        if age:
            try:
                age = int(age)
                update_fields.append("age = %s")
                update_values.append(age)
            except ValueError:
                messagebox.showerror("Error", "Age must be a number")
                return

        if department:
            update_fields.append("department = %s")
            update_values.append(department)
    
        if Email_Id:
            update_fields.append("Email_Id = %s")
            update_values.append(Email_Id)
        
        if phone_number:
            if re.match(r'^\d{10}$', phone_number):
                update_fields.append("phone_number = %s")
                update_values.append(phone_number)
            else:
                messagebox.showerror("Error", "Phone number must be a 10-digit number")
                return
        
        if address:
            update_fields.append("address = %s")
            update_values.append(address)
        
        if role:
            update_fields.append("role = %s")
            update_values.append(role)
        
        if salary:
            try:
                salary = float(salary)
                update_fields.append("salary = %s")
                update_values.append(salary)
            except ValueError:
                messagebox.showerror("Error", "Salary must be a number")
                return

        if not update_fields:
            messagebox.showerror("Error", "No fields to update")
            return

        update_values.append(employee_id)
        update_query = f"UPDATE employee_details SET {', '.join(update_fields)} WHERE employee_id = %s"

        try:
            conn = connect_db()
            cursor = conn.cursor()
            cursor.execute(update_query, tuple(update_values))
            conn.commit()

            if cursor.rowcount == 0:
                messagebox.showerror("Error", "No employee found with the given ID.")
            else:
                messagebox.showinfo("Success", "Employee details updated successfully")
        
            log_user_activity(users_role, "Employee Update", f"Updated employee {employee_id} details")
            cursor.close()
            conn.close()

            clear_entries()

        except mysql.connector.Error as e:
            messagebox.showerror("Error", f"Error connecting to MySQL: {e}")

'-----------------------------------------------------------------------------------------------------------------------------'
# Function to view student details
'-----------------------------------------------------------------------------------------------------------------------------'       
def view_student():
    student_id = student_id_view.get()
        
    if student_id == '':
        messagebox.showerror("Error", "Please enter Student ID")
        return
    
    try:
        conn = connect_db()
        cursor = conn.cursor()
        

        select_query = "SELECT * FROM student_information WHERE student_id = %s"
        cursor.execute(select_query, (student_id,))
        student = cursor.fetchone()
        
        if student:
            details = (f"Student ID: {student[0]}\n"
                       f"Full Name: {student[1]}\n"
                       f"Age: {student[2]}\n"
                       f"Gender: {student[3]}\n"
                       f"Group Name: {student[4]}\n"
                       f"Location: {student[6]}\n"
                       f"Parent Name: {student[7]}\n"
                      f"College Branch ID: {student[9]}\n")
            
            # Conditionally add sensitive information based on the user's role
            if users_role in ['HOD', 'principal', 'vice principal', 'president', 'Admin','hod','Principal','Vice Principal','President','ADMIN']:
                details += (f"\nPhone Number: {student[5]}\n"
                            f"Parent Phone Number: {student[8]}\n"
                            f"Fees: {student[10]}")
                
            messagebox.showinfo("Student Details", details)
        else:
            messagebox.showerror("Error", "No Student found with the given ID")
        log_user_activity(users_role, "View details", f"Student ID {student_id} details")
        
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")
    finally:
        cursor.close()
        conn.close()

def view_all_students():
    if users_role != 'Admin':
        messagebox.showerror("Access Denied", "You do not have permission to view all student details.")
        return

    try:
        conn = connect_db()
        cursor = conn.cursor()
        
        select_query = "SELECT * FROM student_information"
        cursor.execute(select_query)
        students = cursor.fetchall() 
        all_students_window = tk.Toplevel(root)
        all_students_window.geometry('1630x900')
        all_students_window.resizable(False,False)
        all_students_window.configure(bg='light green')
        all_students_window.title("All Students")
        
        if students:
            for idx, student in enumerate(students):
                details = (f"Student ID: {student[0]},  Full Name: {student[1]},  Age: {student[2]}, "
                           f" Gender: {student[3]},  Group Name: {student[4]},  Phone Number: {student[5]}, "
                           f" Location: {student[6]},  Parent Name: {student[7]},  Parent Phone Number: {student[8]}, "
                           f" College Branch ID: {student[9]},  Fees: {student[10]}")
                tk.Label(all_students_window, text=details).pack()
        else:
            tk.Label(all_students_window, text="No student records found.").pack()
        log_user_activity(users_role, "Student details", f"View All details")
        
        cursor.close()
        conn.close()
        
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")
'-----------------------------------------------------------------------------------------------------------------' 
  # Function to clear all entry fields
'-----------------------------------------------------------------------------------------------------------------'      
def clear_entries():
    student_id_entry.delete(0, tk.END)
    Full_name_entry.delete(0, tk.END)
    Age_entry.delete(0, tk.END)
    Gender_entry.delete(0, tk.END)
    Group_Name_entry.delete(0, tk.END)
    Ph_no_entry.delete(0, tk.END)
    Location_entry.delete(0, tk.END)
    Parent_Name_entry.delete(0, tk.END)
    Parent_Phno_entry.delete(0, tk.END)
    Clg_Branch_ID_entry.delete(0, tk.END)
    Fees_entry.delete(0, tk.END)
    student_id_update.delete(0, tk.END)
    Age_update_entry.delete(0, tk.END)
    Group_Name_update_entry.delete(0, tk.END)
    Ph_no_update_entry.delete(0, tk.END)
    Location_update_entry.delete(0, tk.END)
    Parent_Phno_update_entry.delete(0, tk.END)
    Clg_Branch_ID_update_entry.delete(0, tk.END)
    Fees_update_entry.delete(0, tk.END)
    student_id_view.delete(0, tk.END)

def clear_entries():
    employee_id_entry.delete(0, tk.END)
    full_name_entry.delete(0, tk.END)
    age_entry.delete(0, tk.END)
    gender_entry.delete(0, tk.END)
    department_entry.delete(0, tk.END)
    Email_Id_entry.delete(0, tk.END)
    phone_number_entry.delete(0, tk.END)
    address_entry.delete(0, tk.END)
    role_entry.delete(0, tk.END)
    salary_entry.delete(0, tk.END)
    employee_id_update_entry.delete(0, tk.END)
    age_update_entry.delete(0, tk.END)
    department_update_entry.delete(0, tk.END)
    Email_Id_update_entry.delete(0, tk.END)
    phone_number_update_entry.delete(0, tk.END)
    address_update_entry.delete(0, tk.END)
    role_update_entry.delete(0, tk.END)
    salary_update_entry.delete(0, tk.END)
    
    
'---------------------------------------------------*-*------------------------------------------------------------------'
# Function to log User history 
"/-------------------------------------------------*--*------------------------------------------------------------------/"
def view_activity_log():
    try:
        conn = connect_db()
        cursor = conn.cursor()
         
        sql = "SELECT username, activity_type, activity_details, activity_time FROM activity_log ORDER BY activity_time DESC "
        cursor.execute(sql)
        history = cursor.fetchall()
        
        history_window = tk.Toplevel(root)
        history_window.geometry('500x400')
        history_window.title("Login History")
         
        if history:
            for idx, (username, activity_type, activity_details, activity_time) in enumerate(history):
                tk.Label(history_window,text=f"User: {username}, Activity_type: {activity_type} Activity_details: {activity_details}, Time: {activity_time}").pack()
                 
        else:
            tk.Label(history_window, text="NO login History found.").pack()
        log_user_activity(username, "Activity History", f"See users log History")     
        cursor.close()
        conn.close()
         
    except mysql.connector.Error as e:
        messagebox.showerror("Error", f"Error connecting to MySQL: {e}")  

"/-------------------------------------------------*-*------------------------------------------------------------------------/"
    # Function to show the user registration form
'-------------------------------------------------*--*-----------------------------------------------------------------------'
def show_user_registration_form():
    register_window = tk.Toplevel(root)
    register_window.geometry('1530x900')
    register_window.resizable(False,False)
    register_window.configure(bg='lightgreen')
    register_window.title("User Registration")
    
    tk.Label(register_window, text="Username").pack(padx=10,pady=10)
    username_entry = tk.Entry(register_window)
    username_entry.pack()
    
    tk.Label(register_window, text="Password").pack(padx=10,pady=10)
    password_entry = tk.Entry(register_window, show='*')
    password_entry.pack()
    
    tk.Label(register_window, text="Email").pack(padx=10,pady=10)
    email_entry = tk.Entry(register_window)
    email_entry.pack()
    
    tk.Label(register_window, text="Role").pack(pady=10)
    roles = ["HOD", "Principal", "Vice Principal", "Admin", "SL", "JL"]
    role_var = tk.StringVar(register_window)
    role_var.set("Select Role")  # Set default value
    role_menu = tk.OptionMenu(register_window, role_var, *roles)
    role_menu.pack()
    
    tk.Label(register_window, text="Phone_No").pack(pady=10)
    Phone_No_entry = tk.Entry(register_window)
    Phone_No_entry.pack()
    
    def register():
        username = username_entry.get()
        password = password_entry.get()
        email = email_entry.get()
        role = role_var.get() if role_var.get() != "Select Role" else ""
        Phone_No = Phone_No_entry.get()
        
        if username and password and email and role and Phone_No:
            if is_email_in_employee_table(email,role):
                register_user(username, password, email, role, Phone_No)
                register_window.destroy()
                show_verification_form(username)
            else:
                messagebox.showerror("Error", "Email not found in Employee records.")
        else:
            messagebox.showerror("Error", "Please fill in all fields.")
            
    tk.Button(register_window, text="Register",bg='green', command=register).pack(padx=10,pady=10)

"------------------------------------*-*---------------------------------------------------------"
# Function to show the password reset form
"--------------------------------------*--*-------------------------------------------------------"
def show_reset_password_form():
    reset_password_window = tk.Toplevel(root)
    reset_password_window.geometry('1530x900')
    reset_password_window.resizable(False,False)
    reset_password_window.configure(bg='coral')
    reset_password_window.title("Reset Password")

    tk.Label(reset_password_window, text="Username",bg='orange').pack(padx=10,pady=10)
    username_entry = tk.Entry(reset_password_window)
    username_entry.pack()

    tk.Label(reset_password_window, text="New Password",bg='orange').pack(padx=10,pady=10)
    new_password_entry = tk.Entry(reset_password_window, show='*')
    new_password_entry.pack()

    tk.Label(reset_password_window, text="Role (optional)").pack(pady=10)
    roles = ["HOD", "Principal", "Vice Principal", "Admin", "SL", "JL"]
    role_var = tk.StringVar(reset_password_window)
    role_var.set("Select Role")  # Set default value
    role_menu = tk.OptionMenu(reset_password_window, role_var, *roles)
    role_menu.pack()

    def reset():
        username = username_entry.get()
        new_password = new_password_entry.get()
        role = role_var.get() if role_var.get() != "Select Role" else ""

        if username and new_password and role:
            reset_password(username, new_password, role)
            reset_password_window.destroy()
        else:
            messagebox.showerror("Error", "Please fill in all fields.")

    tk.Button(reset_password_window, text="Reset Password",bg='yellow', command=reset).pack(padx=12,pady=10)
"--------------------------------------------*-*----------------------------------------------------------"
# Function to show login form
"-------------------------------------------*---*---------------------------------------------------------"
def show_login_form():
    login_window = tk.Toplevel(root)
    login_window.geometry('1530x900')
    login_window.resizable(False,False)
    login_window.configure(bg='orange')
    login_window.title("User Login")
    
    tk.Label(login_window, text="Username",bg='light green').pack(padx=10,pady=10)
    username_entry = tk.Entry(login_window)
    username_entry.pack()
    
    
    tk.Label(login_window, text="Password",bg='light pink').pack(padx=10,pady=10)
    password_entry = tk.Entry(login_window, show='*')
    password_entry.pack()
    
    
    tk.Label(login_window, text="Role (optional)").pack(pady=10)
    roles = ["HOD", "Principal", "Vice Principal", "Admin", "SL", "JL"]
    role_var = tk.StringVar(login_window)
    role_var.set("Select Role")  # Set default value
    role_menu = tk.OptionMenu(login_window, role_var, *roles)
    role_menu.pack()
    
    
    def login():
        username = username_entry.get()
        password = password_entry.get() 
        role = role_var.get() if role_var.get() != "Select Role" else ""
        
        if username and password and role:
            user = login_user(username, password, role)
            if user:
                global users_role
                users_role = user[5]
                login_window.destroy()
                open_student_info_application()
                for char in password:
                    if char.isupper():
                        has_upper = True
                    elif char.islower():
                        has_lower = True
                    if has_lower and has_upper:
                        print("Password has both lower and upper case letters.")
                    else:
                        print("Password does not meet the requirements.")
            elif username == {username}:
                messagebox.showerror("Login Failed", "Invalid username.")
            elif password == {password}:
                messagebox.showerror("Login Failed", "Invalid password")
            else:
                messagebox.showerror("Login Failed", "Invalid Username ro password or Role")
        else:
            messagebox.showerror("Error", "Please fill in all fields.")
    tk.Button(login_window, text="Login",bg='light green', command=login).pack(padx=10,pady=10)
"---------------------------------------------*-*----------------------------------------------------------------------"
# Function to open the student information application
"--------------------------------------------*--*----------------------------------------------------------------------"
def open_student_info_application():
    student_window = tk.Tk()
    student_window.geometry('1530x900')
    #student_window.resizable(False,False)
    student_window.configure(bg='light green')
    student_window.title("Student Information Management")
    "**********************************************************************************************************************************"
     # Adjust visibility of certain fields based on role "Admin" only.
    "-----------------------------------------------------------------------------------------------------------------------------------"
    if users_role in ['Admin']:
        tk.Label(student_window, text="Student Registration", bg='light blue', font=('Arial', 16)).grid(row=0, column=0, columnspan=4, pady=10)
        tk.Label(student_window, text="Student ID:",bg='orange').grid(row=1, column=0, padx=15, pady=5)
        global student_id_entry
        student_id_entry = tk.Entry(student_window)
        student_id_entry.grid(row=1, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Full Name:",bg='orange').grid(row=2, column=0, padx=10, pady=5)
        global Full_name_entry
        Full_name_entry = tk.Entry(student_window)
        Full_name_entry.grid(row=2, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Age:",bg='orange').grid(row=3, column=0, padx=10, pady=5)
        global Age_entry
        Age_entry = tk.Entry(student_window)
        Age_entry.grid(row=3, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Gender:",bg='orange').grid(row=4, column=0, padx=10, pady=5)
        global Gender_entry
        Gender_entry = tk.Entry(student_window)
        Gender_entry.grid(row=4, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Group Name:",bg='orange').grid(row=5, column=0, padx=10, pady=5)
        global Group_Name_entry
        Group_Name_entry = tk.Entry(student_window)
        Group_Name_entry.grid(row=5, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Location:",bg='orange').grid(row=6, column=0, padx=10, pady=5)
        global Location_entry
        Location_entry = tk.Entry(student_window)
        Location_entry.grid(row=6, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Parent Name:",bg='orange').grid(row=7, column=0, padx=10, pady=5)
        global Parent_Name_entry
        Parent_Name_entry = tk.Entry(student_window)
        Parent_Name_entry.grid(row=7, column=1, padx=15, pady=5)

        tk.Label(student_window, text="College Branch ID:",bg='orange').grid(row=8, column=0, padx=10, pady=5)
        global Clg_Branch_ID_entry
        Clg_Branch_ID_entry = tk.Entry(student_window)
        Clg_Branch_ID_entry.grid(row=8, column=1, padx=15, pady=5)

        tk.Label(student_window, text="Student Phone Number:",bg='orange').grid(row=9, column=0, padx=15, pady=5)
        global Ph_no_entry
        Ph_no_entry = tk.Entry(student_window)
        Ph_no_entry.grid(row=9, column=1, padx=15, pady=5)
            
        tk.Label(student_window, text="Parent Phone Number:",bg='orange').grid(row=10, column=0, padx=10, pady=5)
        global Parent_Phno_entry
        Parent_Phno_entry = tk.Entry(student_window)
        Parent_Phno_entry.grid(row=10, column=1, padx=15, pady=5)
            
        tk.Label(student_window, text="Fees:",bg='orange').grid(row=11, column=0, padx=10, pady=5)
        global Fees_entry
        Fees_entry = tk.Entry(student_window)
        Fees_entry.grid(row=11, column=1, padx=15, pady=5)

        tk.Button(student_window, text="Register",bg='green', command=register_student_details).grid(row=12, column=1, columnspan=2, pady=10)
        
        tk.Label(student_window, text="Update Student Details", bg='light blue', font=('Arial', 16)).grid(row=0, column=10, columnspan=4, pady=10)
        
        tk.Label(student_window, text="Student ID:", bg='orange').grid(row=1, column=11, padx=15, pady=5)
        global student_id_update
        student_id_update = tk.Entry(student_window)
        student_id_update.grid(row=1, column=12, padx=15, pady=5)
        
        tk.Label(student_window, text="Age:", bg='orange').grid(row=2, column=11, padx=10, pady=5)
        global Age_update_entry
        Age_update_entry = tk.Entry(student_window)
        Age_update_entry.grid(row=2, column=12, padx=15, pady=5)

        tk.Label(student_window, text="Group Name:", bg='orange').grid(row=3, column=11, padx=10, pady=5)
        global Group_Name_update_entry
        Group_Name_update_entry = tk.Entry(student_window)
        Group_Name_update_entry.grid(row=3, column=12, padx=15, pady=5)

        tk.Label(student_window, text="Phone Number:", bg='orange').grid(row=4, column=11, padx=15, pady=5)
        global Ph_no_update_entry
        Ph_no_update_entry = tk.Entry(student_window)
        Ph_no_update_entry.grid(row=4, column=12, padx=15, pady=5)

        tk.Label(student_window, text="Location:", bg='orange').grid(row=5, column=11, padx=10, pady=5)
        global Location_update_entry
        Location_update_entry = tk.Entry(student_window)
        Location_update_entry.grid(row=5, column=12, padx=15, pady=5)

        tk.Label(student_window, text="Parent Phone Number:", bg='orange').grid(row=6, column=11, padx=10, pady=5)
        global Parent_Phno_update_entry
        Parent_Phno_update_entry = tk.Entry(student_window)
        Parent_Phno_update_entry.grid(row=6, column=12, padx=15, pady=5)

        tk.Label(student_window, text="College Branch ID:", bg='orange').grid(row=7, column=11, padx=10, pady=5)
        global Clg_Branch_ID_update_entry
        Clg_Branch_ID_update_entry = tk.Entry(student_window)
        Clg_Branch_ID_update_entry.grid(row=7, column=12, padx=15, pady=5)
        
        tk.Label(student_window, text="Fees:", bg='orange').grid(row=8, column=11, padx=10, pady=5)
        global Fees_update_entry
        Fees_update_entry = tk.Entry(student_window)
        Fees_update_entry.grid(row=8, column=12, padx=15, pady=5)

        tk.Button(student_window, text="Update Details", bg='green', command=Update_Student_details).grid(row=9, column=11, columnspan=2, pady=10)
        
        tk.Label(student_window, text="View Login History", bg='light blue', font=('Arial', 16)).grid(row=15, column=11, columnspan=4, pady=10)
        tk.Button(student_window, text="View Login History", bg='yellow', command=view_activity_log).grid(row=17, column=12, padx=15, pady=10)
        
        tk.Label(student_window, text="View All Student Details", bg='light blue', font=('Arial', 16)).grid(row=20, column=0, columnspan=4, pady=10)
        tk.Button(student_window, text="View All Students", bg='yellow', command=view_all_students).grid(row=21, column=0, columnspan=4, pady=10)
        
        tk.Label(student_window, text="Employee Management System", bg='light blue', font=('Arial', 16)).grid(row=0, column=14, columnspan=4, pady=10)
        
        tk.Label(student_window, text="Employee ID").grid(row=1, column=13, padx=10, pady=5)
        global employee_id_entry
        employee_id_entry = tk.Entry(student_window)
        employee_id_entry.grid(row=1, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Full Name").grid(row=2, column=13, padx=10, pady=5)
        global full_name_entry
        full_name_entry = tk.Entry(student_window)
        full_name_entry.grid(row=2, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Age").grid(row=3, column=13, padx=10, pady=5)
        global age_entry
        age_entry = tk.Entry(student_window)
        age_entry.grid(row=3, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Gender").grid(row=4, column=13, padx=10, pady=5)
        global gender_entry
        gender_entry = tk.Entry(student_window)
        gender_entry.grid(row=4, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Department").grid(row=5, column=13, padx=10, pady=5)
        global department_entry
        department_entry = tk.Entry(student_window)
        department_entry.grid(row=5, column=14, padx=15, pady=5)
        
        tk.Label(student_window, text="Email_Id").grid(row=6, column=13, padx=10, pady=5)
        global Email_Id_entry
        Email_Id_entry = tk.Entry(student_window)
        Email_Id_entry.grid(row=6, column=14, padx=15, pady=5)


        tk.Label(student_window, text="Phone Number").grid(row=7, column=13, padx=10, pady=5)
        global phone_number_entry
        phone_number_entry = tk.Entry(student_window)
        phone_number_entry.grid(row=7, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Address").grid(row=8, column=13, padx=10, pady=5)
        global address_entry
        address_entry = tk.Entry(student_window)
        address_entry.grid(row=8, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Role").grid(row=9, column=13, padx=10, pady=5)
        global role_entry
        role_entry = tk.Entry(student_window)
        role_entry.grid(row=9, column=14, padx=15, pady=5)

        tk.Label(student_window, text="Salary").grid(row=10, column=13, padx=10, pady=5)
        global salary_entry
        salary_entry = tk.Entry(student_window)
        salary_entry.grid(row=10, column=14, padx=15, pady=5)
        
        tk.Button(student_window,text='ADD Employee', bg='green', command=add_employee_details).grid(row=11, column=14, padx=10, pady=5)
        
        tk.Label(student_window, text="Employee Details Update", bg='light blue', font=('Arial', 16)).grid(row=0, column=25, columnspan=4, pady=10)
        
        tk.Label(student_window, text="Employee ID").grid(row=1, column=13, padx=10, pady=5)
        global employee_id_update_entry
        employee_id_update_entry = tk.Entry(student_window)
        employee_id_update_entry.grid(row=1, column=16, padx=15, pady=5)


        tk.Label(student_window, text="Age").grid(row=3, column=13, padx=10, pady=5)
        global age_update_entry
        age_update_entry = tk.Entry(student_window)
        age_update_entry.grid(row=3, column=16, padx=15, pady=5)

        tk.Label(student_window, text="Department").grid(row=5, column=13, padx=10, pady=5)
        global department_update_entry
        department_update_entry = tk.Entry(student_window)
        department_update_entry.grid(row=5, column=16, padx=15, pady=5)
        
        tk.Label(student_window, text="Email_Id").grid(row=6, column=13, padx=10, pady=5)
        global Email_Id_update_entry
        Email_Id_update_entry = tk.Entry(student_window)
        Email_Id_update_entry.grid(row=6, column=16, padx=15, pady=5)

        tk.Label(student_window, text="Phone Number").grid(row=7, column=13, padx=10, pady=5)
        global phone_number_update_entry
        phone_number_update_entry = tk.Entry(student_window)
        phone_number_update_entry.grid(row=7, column=16, padx=15, pady=5)

        tk.Label(student_window, text="Address").grid(row=8, column=13, padx=10, pady=5)
        global address_update_entry
        address_update_entry = tk.Entry(student_window)
        address_update_entry.grid(row=8, column=16, padx=15, pady=5)

        tk.Label(student_window, text="Role").grid(row=9, column=13, padx=10, pady=5)
        global role_update_entry
        role_update_entry = tk.Entry(student_window)
        role_update_entry.grid(row=9, column=16, padx=15, pady=5)

        tk.Label(student_window, text="Salary").grid(row=10, column=13, padx=10, pady=5)
        global salary_update_entry
        salary_update_entry = tk.Entry(student_window)
        salary_update_entry.grid(row=10, column=16, padx=15, pady=5)
        
        tk.Button(student_window,text='Update Details', bg='green', command=update_employee_details).grid(row=11, column=16, padx=10, pady=5)


    tk.Label(student_window, text="View Student Details", bg='light blue', font=('Arial', 16)).grid(row=15, column=1, columnspan=4, pady=10)
    
    tk.Label(student_window, text="Enter Student ID:").grid(row=17, column=0, padx=15, pady=5)
    global student_id_view
    student_id_view = tk.Entry(student_window)
    student_id_view.grid(row=17, column=1, padx=14, pady=9)

    tk.Button(student_window, text="View Details",bg='green', command=view_student).grid(row=18, column=1, columnspan=2, pady=10)
     
        
"********************************************************************************************************************************"
# Main application window
"--------------------------------------------------------------------------------------------------------------------------------"
root = tk.Tk()
root.geometry('1530x900')
root.resizable(False,False)
backgroundImage=ImageTk.PhotoImage(file=r'C:\Users\manib\OneDrive\Desktop\VS CODE PROJECTS\bg.JPG')
bgLabel= Label(root,image=backgroundImage)
bgLabel.place(x=0,y=0)
#root.configure(bg='light green')
root.title("Main Application")

"-----------------------------------------*-*--------------------------------------------------------------------------"
# Buttons to access different functionalities
"----------------------------------------*--*--------------------------------------------------------------------------"
tk.Button(root, text="Login",bg='green', command=show_login_form).pack(pady=80)
tk.Button(root, text="Register New User",bg='orange', command=show_user_registration_form).pack(pady=50)
tk.Button(root, text="Reset Password",bg='red', command=show_reset_password_form).pack(pady=5)

root.mainloop()