import mysql.connector

def get_db_connection():
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="Jalebi.362",   # add your MySQL password here if you have one
        database="fair_assessment_system"
    )
    return connection
