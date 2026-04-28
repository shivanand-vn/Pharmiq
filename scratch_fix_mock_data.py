import sys
sys.path.append(r'f:\Pharmiq')
from db.connection import execute_query

def fix_mock_data():
    execute_query("UPDATE medicines SET name='Amoxicillin 500mg' WHERE name='Low Stock Med'")
    execute_query("UPDATE medicines SET name='Paracetamol 650mg' WHERE name='Expiring Med'")
    print("Mock data names updated successfully.")

if __name__ == '__main__':
    fix_mock_data()
