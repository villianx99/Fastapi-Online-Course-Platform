from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional

app = FastAPI(title="LearnHub Online Courses API")

# ---------------- DATA ----------------

courses = [
    {"id": 1, "title": "Python for Beginners", "instructor": "Rahul Sharma", "category": "Data Science", "level": "Beginner", "price": 499, "seats_left": 10},
    {"id": 2, "title": "Web Development Bootcamp", "instructor": "Ankit Verma", "category": "Web Dev", "level": "Intermediate", "price": 999, "seats_left": 5},
    {"id": 3, "title": "UI/UX Design Basics", "instructor": "Neha Singh", "category": "Design", "level": "Beginner", "price": 299, "seats_left": 8},
    {"id": 4, "title": "Docker & DevOps", "instructor": "Amit Patel", "category": "DevOps", "level": "Advanced", "price": 1299, "seats_left": 3},
    {"id": 5, "title": "Machine Learning", "instructor": "Priya Nair", "category": "Data Science", "level": "Advanced", "price": 1499, "seats_left": 6},
    {"id": 6, "title": "JavaScript Essentials", "instructor": "Karan Mehta", "category": "Web Dev", "level": "Beginner", "price": 399, "seats_left": 7},
]

enrollments = []
enrollment_counter = 1

wishlist=[]

# ---------------- MODELS ----------------

class EnrollRequest(BaseModel):
    student_name: str = Field(..., min_length=2)
    course_id: int = Field(..., gt=0)
    email: str = Field(..., min_length=5)
    payment_method: str = "card"
    coupon_code: str = ""
    gift_enrollment: bool = False
    recipient_name: str = ""

class NewCourse(BaseModel):
    title: str = Field(..., min_length=2)
    instructor: str = Field(..., min_length=2)
    category: str = Field(..., min_length=2)
    level: str = Field(..., min_length=2)
    price: int = Field(..., ge=0)
    seats_left: int = Field(..., gt=0)

def find_course(course_id: int):
    for course in courses:
        if course["id"] == course_id:
            return course
    return None
def calculate_enrollment_fee(price, seats_left, coupon_code):

    discount_details = []

    #  Early Bird (10%)
    if seats_left > 5:
        discount = price * 0.10
        price -= discount
        discount_details.append("10% Early Bird Applied")

    #  Coupons
    if coupon_code == "STUDENT20":
        discount = price * 0.20
        price -= discount
        discount_details.append("20% Student Discount Applied")

    elif coupon_code == "FLAT500":
        price -= 500
        discount_details.append("₹500 Flat Discount Applied")

    #  Negative price avoid
    if price < 0:
        price = 0

    return int(price), discount_details

def filter_courses_logic(category=None, level=None, max_price=None, has_seats=None):

    result = courses

    if category is not None:
        result = [c for c in result if c["category"].lower() == category.lower()]

    if level is not None:
        result = [c for c in result if c["level"].lower() == level.lower()]

    if max_price is not None:
        result = [c for c in result if c["price"] <= max_price]

    if has_seats is not None:
        if has_seats:
            result = [c for c in result if c["seats_left"] > 0]
        else:
            result = [c for c in result if c["seats_left"] == 0]

    return result

# ---------------- BASIC ROUTES ----------------

@app.get("/")
def root():
    return {"message": "Welcome to LearnHub Online Courses"}

# ---------------- COURSES ----------------

@app.get("/courses")
def get_courses():
    total_seats = sum(course["seats_left"] for course in courses)

    return {
        "total_courses": len(courses),
        "total_seats_available": total_seats,
        "courses": courses
    }

@app.get("/courses/summary")
def courses_summary():

    total_courses = len(courses)

    free_courses = len([c for c in courses if c["price"] == 0])

    most_expensive = max(courses, key=lambda c: c["price"])

    total_seats = sum(c["seats_left"] for c in courses)

    category_count = {}
    for c in courses:
        category = c["category"]
        category_count[category] = category_count.get(category, 0) + 1

    return {
        "total_courses": total_courses,
        "free_courses": free_courses,
        "most_expensive": most_expensive,
        "total_seats_available": total_seats,
        "category_count": category_count
    }
@app.get("/courses/filter")
def filter_courses(
    category: Optional[str] = None,
    level: Optional[str] = None,
    max_price: Optional[int] = None,
    has_seats: Optional[bool] = None
):

    filtered = filter_courses_logic(category, level, max_price, has_seats)

    return {
        "filters": {
            "category": category,
            "level": level,
            "max_price": max_price,
            "has_seats": has_seats
        },
        "total_found": len(filtered),
        "courses": filtered
    }

@app.post("/courses", status_code=201)
def add_course(course: NewCourse):

    #  Duplicate title check
    for c in courses:
        if c["title"].lower() == course.title.lower():
            raise HTTPException(
                status_code=400,
                detail="Course with this title already exists"
            )

    #  New ID generate
    new_id = len(courses) + 1

    new_course = {
        "id": new_id,
        "title": course.title,
        "instructor": course.instructor,
        "category": course.category,
        "level": course.level,
        "price": course.price,
        "seats_left": course.seats_left
    }

    courses.append(new_course)

    return {
        "message": "Course added successfully",
        "course": new_course
    }

@app.get("/courses/search")
def search_courses(keyword: str):

    matched = [
        c for c in courses
        if keyword.lower() in c["title"].lower()
        or keyword.lower() in c["instructor"].lower()
        or keyword.lower() in c["category"].lower()
    ]

    if not matched:
        return {
            "message": f"No courses found for '{keyword}'"
        }

    return {
        "keyword": keyword,
        "total_found": len(matched),
        "courses": matched
    }

@app.get("/courses/sort")
def sort_courses(sort_by: str = "price", order: str = "asc"):

    #  Validation
    if sort_by not in ["price", "title", "seats_left"]:
        return {"error": "sort_by must be price, title, or seats_left"}

    if order not in ["asc", "desc"]:
        return {"error": "order must be asc or desc"}

    reverse = True if order == "desc" else False

    sorted_courses = sorted(
        courses,
        key=lambda c: c[sort_by],
        reverse=reverse
    )

    return {
        "sort_by": sort_by,
        "order": order,
        "total": len(sorted_courses),
        "courses": sorted_courses
    }

@app.get("/courses/page")
def paginate_courses(page: int = 1, limit: int = 3):

    total = len(courses)

    start = (page - 1) * limit
    end = start + limit

    paginated = courses[start:end]

    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit": limit,
        "total_courses": total,
        "total_pages": total_pages,
        "courses": paginated
    }

@app.get("/courses/browse")
def browse_courses(
    keyword: Optional[str] = None,
    category: Optional[str] = None,
    level: Optional[str] = None,
    max_price: Optional[int] = None,
    sort_by: str = "price",
    order: str = "asc",
    page: int = 1,
    limit: int = 3
):

    result = courses

    #  Step 1: keyword search
    if keyword:
        result = [
            c for c in result
            if keyword.lower() in c["title"].lower()
            or keyword.lower() in c["instructor"].lower()
            or keyword.lower() in c["category"].lower()
        ]

    #  Step 2: filters
    if category:
        result = [c for c in result if c["category"].lower() == category.lower()]

    if level:
        result = [c for c in result if c["level"].lower() == level.lower()]

    if max_price is not None:
        result = [c for c in result if c["price"] <= max_price]

    #  Step 3: sorting
    if sort_by not in ["price", "title", "seats_left"]:
        return {"error": "Invalid sort_by"}

    reverse = True if order == "desc" else False

    result = sorted(result, key=lambda c: c[sort_by], reverse=reverse)

    #  Step 4: pagination
    total = len(result)

    start = (page - 1) * limit
    end = start + limit

    paginated = result[start:end]

    total_pages = (total + limit - 1) // limit

    return {
        "filters": {
            "keyword": keyword,
            "category": category,
            "level": level,
            "max_price": max_price
        },
        "sort": {
            "sort_by": sort_by,
            "order": order
        },
        "pagination": {
            "page": page,
            "limit": limit,
            "total_found": total,
            "total_pages": total_pages
        },
        "courses": paginated
    }

@app.get("/courses/{course_id}")
def get_course(course_id: int):

    for course in courses:
        if course["id"] == course_id:
            return course

    raise HTTPException(status_code=404, detail="Course not found")

@app.put("/courses/{course_id}")
def update_course(
    course_id: int,
    price: Optional[int] = None,
    seats_left: Optional[int] = None
):

    for course in courses:

        if course["id"] == course_id:

            #  Only update if value given
            if price is not None:
                course["price"] = price

            if seats_left is not None:
                course["seats_left"] = seats_left

            return {
                "message": "Course updated successfully",
                "course": course
            }

    #  Not found
    raise HTTPException(
        status_code=404,
        detail="Course not found"
    )

@app.delete("/courses/{course_id}")
def delete_course(course_id: int):

    #  Step 1: check course exists
    course = next((c for c in courses if c["id"] == course_id), None)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    #  Step 2: check enrollments
    for e in enrollments:
        if e["course_title"] == course["title"]:
            raise HTTPException(
                status_code=400,
                detail="Cannot delete course with enrolled students"
            )

    #  Step 3: delete
    courses.remove(course)

    return {
        "message": f"Course '{course['title']}' deleted successfully"
    }

# ---------------- ENROLLMENTS ----------------

@app.get("/enrollments")
def get_enrollments():
    return {
        "total_enrollments": len(enrollments),
        "enrollments": enrollments
    }
@app.post("/enrollments")
def enroll(data: EnrollRequest):

    global enrollment_counter

    #  Step 1: Course find
    course = find_course(data.course_id)

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    
    #  Gift validation
    if data.gift_enrollment and not data.recipient_name:
      raise HTTPException(
        status_code=400,
        detail="Recipient name required for gift enrollment"
    )

    #  Step 2: Seats check
    if course["seats_left"] <= 0:
        raise HTTPException(status_code=400, detail="No seats available")

    #  Step 3: Calculate fee
    final_fee, discounts = calculate_enrollment_fee(
        course["price"],
        course["seats_left"],
        data.coupon_code
    )

    #  Step 4: Reduce seat
    course["seats_left"] -= 1

    #  Step 5: Create enrollment
    enrollment = {
        "enrollment_id": enrollment_counter,
        "student_name": data.student_name,
        "course_title": course["title"],
        "instructor": course["instructor"],
        "original_price": course["price"],
        "discounts_applied": discounts,
        "final_fee": final_fee,
        "gift": data.gift_enrollment,
        "recipient_name": data.recipient_name if data.gift_enrollment else None
    }

    enrollments.append(enrollment)
    enrollment_counter += 1

    return enrollment

@app.get("/enrollments/search")
def search_enrollments(student_name: str):

    matched = [
        e for e in enrollments
        if student_name.lower() in e["student_name"].lower()
    ]

    if not matched:
        return {"message": f"No enrollments found for '{student_name}'"}

    return {
        "student_name": student_name,
        "total_found": len(matched),
        "enrollments": matched
    }


@app.get("/enrollments/sort")
def sort_enrollments(order: str = "asc"):

    if order not in ["asc", "desc"]:
       return {"error": "Invalid order"}

    reverse = True if order == "desc" else False

    sorted_data = sorted(
        enrollments,
        key=lambda e: e["final_fee"],
        reverse=reverse
    )

    return {
        "order": order,
        "enrollments": sorted_data
    }


@app.get("/enrollments/page")
def paginate_enrollments(page: int = 1, limit: int = 3):

    total = len(enrollments)

    start = (page - 1) * limit
    end = start + limit

    paginated = enrollments[start:end]

    total_pages = (total + limit - 1) // limit

    return {
        "page": page,
        "limit":limit,
        "total_pages": total_pages,
        "enrollments": paginated
    }

@app.post("/wishlist/add")
def add_to_wishlist(student_name: str, course_id: int):

    #  Course exist check
    course = find_course(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    #  Duplicate check
    for item in wishlist:
        if item["student_name"] == student_name and item["course_id"] == course_id:
            raise HTTPException(
                status_code=400,
                detail="Course already in wishlist"
            )

    #  Add to wishlist
    wishlist.append({
        "student_name": student_name,
        "course_id": course_id,
        "course_title": course["title"],
        "price": course["price"]
    })

    return {
        "message": "Added to wishlist",
        "wishlist_count": len(wishlist)
    }

@app.delete("/wishlist/remove/{course_id}")
def remove_from_wishlist(course_id: int, student_name: str):

    for i, item in enumerate(wishlist):
        if item["course_id"] == course_id and item["student_name"] == student_name:
            wishlist.pop(i)

            return {
                "message": "Removed from wishlist"
            }

    raise HTTPException(status_code=404, detail="Item not found in wishlist")

@app.get("/wishlist")
def view_wishlist():

    total_value = sum(item["price"] for item in wishlist)

    return {
        "total_items": len(wishlist),
        "total_value": total_value,
        "wishlist": wishlist
    }

@app.post("/wishlist/enroll-all")
def enroll_all(student_name: str, payment_method: str):

    global enrollment_counter

    student_items = [item for item in wishlist if item["student_name"] == student_name]

    if not student_items:
        return {"message": "No wishlist items found"}

    enrolled = []
    total_fee = 0

    for item in student_items:

        course = find_course(item["course_id"])

        if not course or course["seats_left"] <= 0:
            continue

        final_fee, discounts = calculate_enrollment_fee(
            course["price"],
            course["seats_left"],
            ""
        )

        course["seats_left"] -= 1

        enrollment = {
            "enrollment_id": enrollment_counter,
            "student_name": student_name,
            "course_title": course["title"],
            "instructor": course["instructor"],
            "final_fee": final_fee
        }

        enrollments.append(enrollment)
        enrolled.append(enrollment)

        enrollment_counter += 1
        total_fee += final_fee

    # remove enrolled items from wishlist
    wishlist[:] = [item for item in wishlist if item["student_name"] != student_name]

    return {
        "total_enrolled": len(enrolled),
        "grand_total": total_fee,
        "enrollments": enrolled
    }