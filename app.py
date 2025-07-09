from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os


app = FastAPI(
    title="College Management API",
    description="A basic RESTful API for managing students, courses, and enrollments with JWT authentication, for a student project.",
    version="1.0.0"
)

# JWT Configuration 
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-super-secret-jwt-key-for-fastapi")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# User for Authentication 
VALID_USERNAME = "admin"
VALID_PASSWORD = "password123" 


students_db = []
courses_db = []
enrollments_db = []
next_student_id = 1
next_course_id = 1
next_enrollment_id = 1

# Pydantic Models for Data Validation 

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

# Student Model
class Student(BaseModel):
    id: Optional[int] = None 
    major: str
    email: str 

# Course Model
class Course(BaseModel):
    id: Optional[int] = None 
    title: str
    code: str
    credits: int

# Enrollment Model
class Enrollment(BaseModel):
    id: Optional[int] = None 
    student_id: int
    course_id: int

# JWT Helper Functions 

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    if token_data.username != VALID_USERNAME:
        raise credentials_exception
    return token_data.username

# API Endpoints 

@app.get("/", summary="Home route")
async def home():
    return {"message": "Welcome to the College Management API!"}

@app.post("/token", response_model=Token, summary="Get JWT access token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username
    password = form_data.password

    if username != VALID_USERNAME or password != VALID_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

# Student Endpoints
@app.get("/students", response_model=List[Student], summary="Retrieve all students")
async def get_students(current_user: str = Depends(get_current_user)):
    return students_db

@app.post("/students", response_model=Student, status_code=status.HTTP_201_CREATED, summary="Add a new student")
async def add_student(student_data: Student, current_user: str = Depends(get_current_user)):
    global next_student_id
    new_student = student_data.dict()
    new_student["id"] = next_student_id
    students_db.append(new_student)
    next_student_id += 1
    return new_student

@app.get("/students/{student_id}", response_model=Student, summary="Retrieve a student by ID")
async def get_student(student_id: int, current_user: str = Depends(get_current_user)):
    for student in students_db:
        if student["id"] == student_id:
            return student
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

@app.put("/students/{student_id}", response_model=Student, summary="Update an existing student")
async def update_student(student_id: int, student_data: Student, current_user: str = Depends(get_current_user)):
    for idx, student in enumerate(students_db):
        if student["id"] == student_id:
            updated_data = student_data.dict(exclude_unset=True)
            if 'id' in updated_data:
                del updated_data['id'] 
            students_db[idx].update(updated_data)
            return students_db[idx]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")

@app.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a student")
async def delete_student(student_id: int, current_user: str = Depends(get_current_user)):
    global students_db
    initial_len = len(students_db)
    students_db = [s for s in students_db if s["id"] != student_id]
    if len(students_db) == initial_len:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Student not found")
    return

# Course Endpoints
@app.get("/courses", response_model=List[Course], summary="Retrieve all courses")
async def get_courses(current_user: str = Depends(get_current_user)):
    return courses_db

@app.post("/courses", response_model=Course, status_code=status.HTTP_201_CREATED, summary="Add a new course")
async def add_course(course_data: Course, current_user: str = Depends(get_current_user)):
    global next_course_id
    new_course = course_data.dict()
    new_course["id"] = next_course_id
    courses_db.append(new_course)
    next_course_id += 1
    return new_course

@app.get("/courses/{course_id}", response_model=Course, summary="Retrieve a course by ID")
async def get_course(course_id: int, current_user: str = Depends(get_current_user)):
    for course in courses_db:
        if course["id"] == course_id:
            return course
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

@app.put("/courses/{course_id}", response_model=Course, summary="Update an existing course")
async def update_course(course_id: int, course_data: Course, current_user: str = Depends(get_current_user)):
    for idx, course in enumerate(courses_db):
        if course["id"] == course_id:
            updated_data = course_data.dict(exclude_unset=True)
            if 'id' in updated_data:
                del updated_data['id']
            courses_db[idx].update(updated_data)
            return courses_db[idx]
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")

@app.delete("/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a course")
async def delete_course(course_id: int, current_user: str = Depends(get_current_user)):
    global courses_db
    initial_len = len(courses_db)
    courses_db = [c for c in courses_db if c["id"] != course_id]
    if len(courses_db) == initial_len:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Course not found")
    return

# Enrollment Endpoints
@app.get("/enrollments", response_model=List[Enrollment], summary="Retrieve all enrollments")
async def get_enrollments(current_user: str = Depends(get_current_user)):
    return enrollments_db

@app.post("/enrollments", response_model=Enrollment, status_code=status.HTTP_201_CREATED, summary="Add a new enrollment")
async def add_enrollment(enrollment_data: Enrollment, current_user: str = Depends(get_current_user)):
    global next_enrollment_id
    student_exists = any(s["id"] == enrollment_data.student_id for s in students_db)
    course_exists = any(c["id"] == enrollment_data.course_id for c in courses_db)

    if not student_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Student with ID {enrollment_data.student_id} not found")
    if not course_exists:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Course with ID {enrollment_data.course_id} not found")

    new_enrollment = enrollment_data.dict()
    new_enrollment["id"] = next_enrollment_id
    enrollments_db.append(new_enrollment)
    next_enrollment_id += 1
    return new_enrollment

@app.get("/enrollments/{enrollment_id}", response_model=Enrollment, summary="Retrieve an enrollment by ID")
async def get_enrollment(enrollment_id: int, current_user: str = Depends(get_current_user)):
    for enrollment in enrollments_db:
        if enrollment["id"] == enrollment_id:
            return enrollment
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")

@app.delete("/enrollments/{enrollment_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete an enrollment")
async def delete_enrollment(enrollment_id: int, current_user: str = Depends(get_current_user)):
    global enrollments_db
    initial_len = len(enrollments_db)
    enrollments_db = [e for e in enrollments_db if e["id"] != enrollment_id]
    if len(enrollments_db) == initial_len:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Enrollment not found")
    return

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)