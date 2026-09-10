# ==========================================
# LAB 1 - EXERCISE 2
# STUDENT MANAGEMENT SYSTEM
# Object-Oriented Programming
# ==========================================

# ------------------------------------------
# Part 1 & Part 2: Create Student class and methods
# ------------------------------------------
class Student:
    def __init__(self, student_id, name, age, major, gpa):
        self.student_id = student_id
        self.name = name
        self.age = age
        self.major = major
        self.gpa = gpa

    def calculate_grade(self):
        if self.gpa >= 3.60:
            return "Excellent"
        elif self.gpa >= 3.20:
            return "Very Good"
        elif self.gpa >= 2.50:
            return "Good"
        elif self.gpa >= 2.00:
            return "Average"
        else:
            return "Poor"

    def update_gpa(self, new_gpa):
        self.gpa = new_gpa

    def is_honor_student(self):
        return self.gpa >= 3.60

    def display_information(self):
        classification = self.calculate_grade()
        # Định dạng in ra màn hình. Sinh viên thường không có Research Topic nên để N/A
        print(f"{self.student_id:<10}{self.name:<20}{self.major:<12}{self.gpa:<8.2f}{classification:<15}{'N/A':<25}")


# ------------------------------------------
# Part 3: Create GraduateStudent class
# ------------------------------------------
class GraduateStudent(Student):
    def __init__(self, student_id, name, age, major, gpa, research_topic, advisor):
        # Kế thừa các thuộc tính cơ bản từ lớp cha (Student)
        super().__init__(student_id, name, age, major, gpa)
        self.research_topic = research_topic
        self.advisor = advisor

    def display_research_information(self):
        print(f"Research Topic: {self.research_topic} | Advisor: {self.advisor}")

    # Ghi đè (override) lại hàm display_information để hiển thị thêm cột Research Topic
    def display_information(self):
        classification = self.calculate_grade()
        print(f"{self.student_id:<10}{self.name:<20}{self.major:<12}{self.gpa:<8.2f}{classification:<15}{self.research_topic:<25}")

# ==========================================
# MAIN PROGRAM
# ==========================================
if __name__ == "__main__":
    
    # ------------------------------------------
    # Part 4: Create objects
    # ------------------------------------------
    # Khởi tạo 3 đối tượng Student
    s1 = Student("1001", "Alice", 20, "CE", 3.85)
    s2 = Student("1002", "Bob", 21, "EE", 2.75)
    s3 = Student("1003", "John", 20, "IT", 3.45)

    # Khởi tạo 2 đối tượng GraduateStudent
    gs1 = GraduateStudent("2001", "David", 24, "CE", 3.90, "IC Design", "Dr. Smith")
    gs2 = GraduateStudent("2002", "Eva", 23, "CS", 3.50, "AI in Healthcare", "Dr. Brown")

    # Lưu toàn bộ vào một list
    all_students = [s1, s2, s3, gs1, gs2]

    # ------------------------------------------
    # Part 5: Display Information
    # ------------------------------------------
    print("\n" + "-" * 90)
    print(f"{'ID':<10}{'Name':<20}{'Major':<12}{'GPA':<8}{'Classification':<15}{'Research Topic':<25}")
    print("-" * 90)

    # Duyệt qua list và in thông tin
    for student in all_students:
        student.display_information()
    
    print("-" * 90)