import sys
sys.path.append('.')
from models.user import create_user
from models.product import add_new_stock

try:
    create_user('Biller', 1, 'testuser', 'pass', 'Biller')
    print("Failed: RBAC did not trigger")
except PermissionError:
    print("RBAC Create User OK")

try:
    add_new_stock(1, 1, 1, 'A', '2020-01-01', 0, -10)
    print("Failed: Product validation did not trigger")
except ValueError as e:
    print("Product Validation OK:", str(e))
