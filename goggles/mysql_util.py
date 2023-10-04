from django.db import connections
cursor = connections['cust'].cursor() # Replace 'cust' to other defined databases if necessary.
cursor.execute("YOUR SQL QUERY HERE")
cursor.fetchall()


