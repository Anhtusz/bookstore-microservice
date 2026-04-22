import csv
import json
import os
import random
from datetime import datetime, timedelta


NUM_USERS = 500
NUM_BOOKS = 200
MIN_RECORDS = 10000
RANDOM_SEED = 42
PASSWORD = "password123"

# The request says "8 behaviors" but only lists 7 values.
# Keep the exact listed behaviors so downstream encoding stays consistent.
ACTIONS = [
    "view",
    "click",
    "add_to_cart",
    "purchase",
    "remove_cart",
    "search",
    "review",
]

CATEGORY_DEFS = [
    {"name": "Detective", "description": "Mystery and crime fiction"},
    {"name": "Adventure", "description": "Adventure and exploration stories"},
    {"name": "Novel", "description": "Literary, contemporary, and classic novels"},
    {"name": "Science Fiction", "description": "Speculative and futuristic fiction"},
    {"name": "Fantasy", "description": "Fantasy and mythic storytelling"},
    {"name": "Self-Help", "description": "Personal growth and practical guidance"},
    {"name": "Biography", "description": "Biographies and memoirs"},
    {"name": "History", "description": "Historical nonfiction"},
    {"name": "Psychology", "description": "Psychology and human behavior"},
]

REAL_BOOKS = [
    ("Novel", "To Kill a Mockingbird", "Harper Lee"),
    ("Novel", "Pride and Prejudice", "Jane Austen"),
    ("Novel", "1984", "George Orwell"),
    ("Novel", "The Great Gatsby", "F. Scott Fitzgerald"),
    ("Novel", "Jane Eyre", "Charlotte Bronte"),
    ("Novel", "Wuthering Heights", "Emily Bronte"),
    ("Novel", "Little Women", "Louisa May Alcott"),
    ("Novel", "Beloved", "Toni Morrison"),
    ("Novel", "The Catcher in the Rye", "J. D. Salinger"),
    ("Novel", "The Kite Runner", "Khaled Hosseini"),
    ("Novel", "The Alchemist", "Paulo Coelho"),
    ("Novel", "Norwegian Wood", "Haruki Murakami"),
    ("Novel", "Atonement", "Ian McEwan"),
    ("Novel", "The Road", "Cormac McCarthy"),
    ("Novel", "White Teeth", "Zadie Smith"),
    ("Novel", "Never Let Me Go", "Kazuo Ishiguro"),
    ("Novel", "The Goldfinch", "Donna Tartt"),
    ("Novel", "Middlesex", "Jeffrey Eugenides"),
    ("Novel", "The Secret History", "Donna Tartt"),
    ("Novel", "The Color Purple", "Alice Walker"),
    ("Novel", "A Man Called Ove", "Fredrik Backman"),
    ("Novel", "Pachinko", "Min Jin Lee"),
    ("Science Fiction", "Dune", "Frank Herbert"),
    ("Science Fiction", "Foundation", "Isaac Asimov"),
    ("Science Fiction", "Neuromancer", "William Gibson"),
    ("Science Fiction", "Snow Crash", "Neal Stephenson"),
    ("Science Fiction", "Ender's Game", "Orson Scott Card"),
    ("Science Fiction", "The Left Hand of Darkness", "Ursula K. Le Guin"),
    ("Science Fiction", "Fahrenheit 451", "Ray Bradbury"),
    ("Science Fiction", "The Martian", "Andy Weir"),
    ("Science Fiction", "Ready Player One", "Ernest Cline"),
    ("Science Fiction", "Project Hail Mary", "Andy Weir"),
    ("Science Fiction", "Hyperion", "Dan Simmons"),
    ("Science Fiction", "Do Androids Dream of Electric Sheep?", "Philip K. Dick"),
    ("Science Fiction", "The Three-Body Problem", "Liu Cixin"),
    ("Science Fiction", "Children of Time", "Adrian Tchaikovsky"),
    ("Science Fiction", "The Time Machine", "H. G. Wells"),
    ("Science Fiction", "I, Robot", "Isaac Asimov"),
    ("Science Fiction", "Brave New World", "Aldous Huxley"),
    ("Science Fiction", "The War of the Worlds", "H. G. Wells"),
    ("Science Fiction", "The Hitchhiker's Guide to the Galaxy", "Douglas Adams"),
    ("Science Fiction", "Solaris", "Stanislaw Lem"),
    ("Fantasy", "The Hobbit", "J. R. R. Tolkien"),
    ("Fantasy", "The Fellowship of the Ring", "J. R. R. Tolkien"),
    ("Fantasy", "The Two Towers", "J. R. R. Tolkien"),
    ("Fantasy", "The Return of the King", "J. R. R. Tolkien"),
    ("Fantasy", "Harry Potter and the Sorcerer's Stone", "J. K. Rowling"),
    ("Fantasy", "Harry Potter and the Chamber of Secrets", "J. K. Rowling"),
    ("Fantasy", "Harry Potter and the Prisoner of Azkaban", "J. K. Rowling"),
    ("Fantasy", "Harry Potter and the Goblet of Fire", "J. K. Rowling"),
    ("Fantasy", "Harry Potter and the Order of the Phoenix", "J. K. Rowling"),
    ("Fantasy", "Harry Potter and the Half-Blood Prince", "J. K. Rowling"),
    ("Fantasy", "Harry Potter and the Deathly Hallows", "J. K. Rowling"),
    ("Fantasy", "A Game of Thrones", "George R. R. Martin"),
    ("Fantasy", "A Clash of Kings", "George R. R. Martin"),
    ("Fantasy", "The Name of the Wind", "Patrick Rothfuss"),
    ("Fantasy", "The Wise Man's Fear", "Patrick Rothfuss"),
    ("Fantasy", "Mistborn: The Final Empire", "Brandon Sanderson"),
    ("Fantasy", "The Way of Kings", "Brandon Sanderson"),
    ("Fantasy", "The Lies of Locke Lamora", "Scott Lynch"),
    ("Fantasy", "American Gods", "Neil Gaiman"),
    ("Fantasy", "Jonathan Strange & Mr Norrell", "Susanna Clarke"),
    ("Fantasy", "The Last Unicorn", "Peter S. Beagle"),
    ("Fantasy", "A Wizard of Earthsea", "Ursula K. Le Guin"),
    ("Fantasy", "The Blade Itself", "Joe Abercrombie"),
    ("Detective", "Murder on the Orient Express", "Agatha Christie"),
    ("Detective", "The Hound of the Baskervilles", "Arthur Conan Doyle"),
    ("Detective", "And Then There Were None", "Agatha Christie"),
    ("Detective", "Gone Girl", "Gillian Flynn"),
    ("Detective", "The Girl with the Dragon Tattoo", "Stieg Larsson"),
    ("Detective", "The Big Sleep", "Raymond Chandler"),
    ("Detective", "The Maltese Falcon", "Dashiell Hammett"),
    ("Detective", "In the Woods", "Tana French"),
    ("Detective", "The Da Vinci Code", "Dan Brown"),
    ("Detective", "Still Life", "Louise Penny"),
    ("Detective", "The Thursday Murder Club", "Richard Osman"),
    ("Detective", "The Silent Patient", "Alex Michaelides"),
    ("Detective", "Sharp Objects", "Gillian Flynn"),
    ("Detective", "Tinker Tailor Soldier Spy", "John le Carre"),
    ("Detective", "The Cuckoo's Calling", "Robert Galbraith"),
    ("Detective", "The Woman in White", "Wilkie Collins"),
    ("Detective", "The Moonstone", "Wilkie Collins"),
    ("Detective", "The Name of the Rose", "Umberto Eco"),
    ("Detective", "The ABC Murders", "Agatha Christie"),
    ("Detective", "Crooked House", "Agatha Christie"),
    ("Detective", "Rebecca", "Daphne du Maurier"),
    ("Detective", "The Postman Always Rings Twice", "James M. Cain"),
    ("Biography", "The Diary of a Young Girl", "Anne Frank"),
    ("Biography", "Long Walk to Freedom", "Nelson Mandela"),
    ("Biography", "Steve Jobs", "Walter Isaacson"),
    ("Biography", "Becoming", "Michelle Obama"),
    ("Biography", "Educated", "Tara Westover"),
    ("Biography", "The Autobiography of Malcolm X", "Malcolm X and Alex Haley"),
    ("Biography", "Einstein: His Life and Universe", "Walter Isaacson"),
    ("Biography", "Alexander Hamilton", "Ron Chernow"),
    ("Biography", "Open", "Andre Agassi"),
    ("Biography", "When Breath Becomes Air", "Paul Kalanithi"),
    ("Biography", "I Know Why the Caged Bird Sings", "Maya Angelou"),
    ("Biography", "Shoe Dog", "Phil Knight"),
    ("Biography", "Born a Crime", "Trevor Noah"),
    ("Biography", "Just as I Am", "Cicely Tyson"),
    ("Biography", "Bossypants", "Tina Fey"),
    ("Biography", "Unbroken", "Laura Hillenbrand"),
    ("Biography", "The Immortal Life of Henrietta Lacks", "Rebecca Skloot"),
    ("Biography", "Churchill: Walking with Destiny", "Andrew Roberts"),
    ("Biography", "Titan", "Ron Chernow"),
    ("Biography", "The Wright Brothers", "David McCullough"),
    ("Biography", "Catherine the Great", "Robert K. Massie"),
    ("Biography", "Wild", "Cheryl Strayed"),
    ("Self-Help", "Atomic Habits", "James Clear"),
    ("Self-Help", "The 7 Habits of Highly Effective People", "Stephen R. Covey"),
    ("Self-Help", "How to Win Friends and Influence People", "Dale Carnegie"),
    ("Self-Help", "Deep Work", "Cal Newport"),
    ("Self-Help", "Mindset", "Carol S. Dweck"),
    ("Self-Help", "Grit", "Angela Duckworth"),
    ("Self-Help", "The Power of Habit", "Charles Duhigg"),
    ("Self-Help", "Thinking in Bets", "Annie Duke"),
    ("Self-Help", "Essentialism", "Greg McKeown"),
    ("Self-Help", "The Subtle Art of Not Giving a F*ck", "Mark Manson"),
    ("Self-Help", "Tiny Habits", "BJ Fogg"),
    ("Self-Help", "Ikigai", "Hector Garcia and Francesc Miralles"),
    ("Self-Help", "Start with Why", "Simon Sinek"),
    ("Self-Help", "Can't Hurt Me", "David Goggins"),
    ("Self-Help", "Make Your Bed", "William H. McRaven"),
    ("Self-Help", "The Four Agreements", "Don Miguel Ruiz"),
    ("Self-Help", "Daring Greatly", "Brene Brown"),
    ("Self-Help", "The Gifts of Imperfection", "Brene Brown"),
    ("Self-Help", "Awaken the Giant Within", "Tony Robbins"),
    ("Self-Help", "Feel the Fear and Do It Anyway", "Susan Jeffers"),
    ("Self-Help", "The One Thing", "Gary Keller and Jay Papasan"),
    ("Self-Help", "You Are a Badass", "Jen Sincero"),
    ("History", "Sapiens", "Yuval Noah Harari"),
    ("History", "Guns, Germs, and Steel", "Jared Diamond"),
    ("History", "The Silk Roads", "Peter Frankopan"),
    ("History", "Team of Rivals", "Doris Kearns Goodwin"),
    ("History", "The Lessons of History", "Will Durant and Ariel Durant"),
    ("History", "SPQR", "Mary Beard"),
    ("History", "The Rise and Fall of the Third Reich", "William L. Shirer"),
    ("History", "The Crusades", "Thomas Asbridge"),
    ("History", "Postwar", "Tony Judt"),
    ("History", "The Splendid and the Vile", "Erik Larson"),
    ("History", "The Warmth of Other Suns", "Isabel Wilkerson"),
    ("History", "1776", "David McCullough"),
    ("History", "Destiny of the Republic", "Candice Millard"),
    ("History", "The Liberation Trilogy", "Rick Atkinson"),
    ("History", "A People's History of the United States", "Howard Zinn"),
    ("History", "The Pity of War", "Niall Ferguson"),
    ("History", "The Wright Brothers", "David McCullough"),
    ("History", "Paris 1919", "Margaret MacMillan"),
    ("History", "The Romanovs", "Simon Sebag Montefiore"),
    ("History", "The Black Count", "Tom Reiss"),
    ("History", "King Leopold's Ghost", "Adam Hochschild"),
    ("History", "Bloodlands", "Timothy Snyder"),
    ("Psychology", "Thinking, Fast and Slow", "Daniel Kahneman"),
    ("Psychology", "Influence", "Robert B. Cialdini"),
    ("Psychology", "Predictably Irrational", "Dan Ariely"),
    ("Psychology", "Emotional Intelligence", "Daniel Goleman"),
    ("Psychology", "Man's Search for Meaning", "Viktor E. Frankl"),
    ("Psychology", "The Body Keeps the Score", "Bessel van der Kolk"),
    ("Psychology", "Stumbling on Happiness", "Daniel Gilbert"),
    ("Psychology", "Behave", "Robert M. Sapolsky"),
    ("Psychology", "Flow", "Mihaly Csikszentmihalyi"),
    ("Psychology", "Quiet", "Susan Cain"),
    ("Psychology", "The Righteous Mind", "Jonathan Haidt"),
    ("Psychology", "The Man Who Mistook His Wife for a Hat", "Oliver Sacks"),
    ("Psychology", "Mistakes Were Made (But Not by Me)", "Carol Tavris and Elliot Aronson"),
    ("Psychology", "Attached", "Amir Levine and Rachel Heller"),
    ("Psychology", "Games People Play", "Eric Berne"),
    ("Psychology", "Blink", "Malcolm Gladwell"),
    ("Psychology", "Outliers", "Malcolm Gladwell"),
    ("Psychology", "Drive", "Daniel H. Pink"),
    ("Psychology", "Originals", "Adam Grant"),
    ("Psychology", "Thinking in Systems", "Donella H. Meadows"),
    ("Psychology", "The Social Animal", "David Brooks"),
    ("Psychology", "Reaching Down the Rabbit Hole", "Allan H. Ropper and Brian David Burrell"),
    ("Adventure", "Treasure Island", "Robert Louis Stevenson"),
    ("Adventure", "Around the World in Eighty Days", "Jules Verne"),
    ("Adventure", "The Call of the Wild", "Jack London"),
    ("Adventure", "Life of Pi", "Yann Martel"),
    ("Adventure", "The Lost World", "Arthur Conan Doyle"),
    ("Adventure", "King Solomon's Mines", "H. Rider Haggard"),
    ("Adventure", "Robinson Crusoe", "Daniel Defoe"),
    ("Adventure", "Journey to the Center of the Earth", "Jules Verne"),
    ("Adventure", "The Three Musketeers", "Alexandre Dumas"),
    ("Adventure", "Into Thin Air", "Jon Krakauer"),
    ("Adventure", "The Old Man and the Sea", "Ernest Hemingway"),
    ("Adventure", "Hatchet", "Gary Paulsen"),
    ("Adventure", "The Swiss Family Robinson", "Johann David Wyss"),
    ("Adventure", "The Odyssey", "Homer"),
    ("Adventure", "The Count of Monte Cristo", "Alexandre Dumas"),
    ("Adventure", "Gulliver's Travels", "Jonathan Swift"),
    ("Adventure", "The Adventures of Huckleberry Finn", "Mark Twain"),
    ("Adventure", "The Sea-Wolf", "Jack London"),
    ("Adventure", "The Lost City of Z", "David Grann"),
    ("Adventure", "Touching the Void", "Joe Simpson"),
    ("Adventure", "Kon-Tiki", "Thor Heyerdahl"),
    ("Adventure", "Endurance", "Alfred Lansing"),
    ("Adventure", "The River of Doubt", "Candice Millard"),
    ("Adventure", "Seven Years in Tibet", "Heinrich Harrer"),
    ("Adventure", "Skeletons on the Zahara", "Dean King"),
]

FIRST_NAMES = [
    "Liam", "Noah", "Emma", "Olivia", "Ava", "Sophia", "Mason", "Ethan", "Lucas", "Mia",
    "Isabella", "Amelia", "James", "Benjamin", "Charlotte", "Elijah", "Harper", "Evelyn",
    "Daniel", "Michael", "Abigail", "Emily", "Henry", "Sebastian", "Grace", "Ella", "Jack",
    "Scarlett", "Avery", "Leo", "Chloe", "Aria", "Samuel", "Madison", "Nora", "Camila",
]

LAST_NAMES = [
    "Nguyen", "Tran", "Le", "Pham", "Hoang", "Phan", "Vu", "Dang", "Bui", "Do",
    "Smith", "Johnson", "Brown", "Williams", "Jones", "Garcia", "Miller", "Davis",
    "Wilson", "Anderson", "Thomas", "Taylor", "Moore", "Martin", "Lee", "Clark",
]

STREETS = [
    "Nguyen Hue", "Le Loi", "Vo Van Tan", "Hai Ba Trung", "Pham Ngu Lao", "Pasteur",
    "Ly Thuong Kiet", "Tran Hung Dao", "Dien Bien Phu", "Pham Van Dong", "Oak", "Maple",
    "Cedar", "Pine", "Lakeview", "Sunset", "Hillcrest", "Riverside",
]

CITIES = [
    "Ho Chi Minh City", "Hanoi", "Da Nang", "Can Tho", "Nha Trang",
    "Austin", "Seattle", "San Jose", "Irvine", "Boston",
]

IMAGE_URLS = [
    "https://images.unsplash.com/photo-1512820790803-83ca734da794?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1495446815901-a7297e633e8d?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1521587760476-6c12a4b040da?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1516979187457-637abb4f9353?auto=format&fit=crop&w=900&q=80",
    "https://images.unsplash.com/photo-1519682337058-a94d519337bc?auto=format&fit=crop&w=900&q=80",
]


def build_users():
    users = []
    for user_id in range(1, NUM_USERS + 1):
        first = FIRST_NAMES[(user_id - 1) % len(FIRST_NAMES)]
        last = LAST_NAMES[((user_id - 1) * 3) % len(LAST_NAMES)]
        name = f"{first} {last}"
        username = f"{first.lower()}.{last.lower()}{user_id}"
        city = CITIES[(user_id - 1) % len(CITIES)]
        street = STREETS[((user_id - 1) * 5) % len(STREETS)]
        address = f"{100 + user_id} {street} St, {city}"
        users.append(
            {
                "id": user_id,
                "name": name,
                "username": username,
                "email": f"{username}@example.com",
                "address": address,
                "password": PASSWORD,
            }
        )
    return users


def build_books():
    books = []
    for book_id, (category_name, title, author) in enumerate(REAL_BOOKS[:NUM_BOOKS], start=1):
        price = round(7.99 + (book_id % 17) * 1.35 + (book_id % 5) * 0.2, 2)
        stock = 12 + (book_id * 7) % 89
        description = (
            f"{title} by {author} is a real {category_name.lower()} title included in the "
            f"seed dataset for recommender training and behavior simulation."
        )
        books.append(
            {
                "id": book_id,
                "title": title,
                "author": author,
                "description": description,
                "price": price,
                "stock": stock,
                "image_url": IMAGE_URLS[book_id % len(IMAGE_URLS)],
                "category_name": category_name,
            }
        )
    return books


def _append_event(records, user_id, product_id, action, event_time):
    records.append(
        {
            "user_id": user_id,
            "product_id": product_id,
            "action": action,
            "timestamp": event_time.isoformat(),
        }
    )


def build_behavior_records(users, books):
    records = []
    base_time = datetime(2025, 1, 1, 8, 0, 0)
    books_by_category = {}
    for book in books:
        books_by_category.setdefault(book["category_name"], []).append(book)

    for user in users:
        preferred_categories = random.sample(list(books_by_category.keys()), k=3)
        user_clock = base_time + timedelta(hours=random.randint(0, 240))
        sessions = random.randint(6, 10)

        for _ in range(sessions):
            session_category = random.choice(preferred_categories)
            session_books = random.sample(books_by_category[session_category], k=random.randint(1, 3))
            user_clock += timedelta(hours=random.randint(12, 72), minutes=random.randint(0, 59))

            if random.random() < 0.75:
                _append_event(records, user["id"], session_books[0]["id"], "search", user_clock)
                user_clock += timedelta(minutes=random.randint(1, 3))

            for book in session_books:
                _append_event(records, user["id"], book["id"], "view", user_clock)
                user_clock += timedelta(minutes=random.randint(1, 4))

                if random.random() < 0.85:
                    _append_event(records, user["id"], book["id"], "click", user_clock)
                    user_clock += timedelta(minutes=random.randint(1, 3))

                if random.random() < 0.45:
                    _append_event(records, user["id"], book["id"], "add_to_cart", user_clock)
                    user_clock += timedelta(minutes=random.randint(1, 2))

                    if random.random() < 0.25:
                        _append_event(records, user["id"], book["id"], "remove_cart", user_clock)
                        user_clock += timedelta(minutes=random.randint(1, 2))
                    else:
                        _append_event(records, user["id"], book["id"], "purchase", user_clock)
                        user_clock += timedelta(minutes=random.randint(2, 12))

                        if random.random() < 0.55:
                            review_time = user_clock + timedelta(days=random.randint(1, 14))
                            _append_event(records, user["id"], book["id"], "review", review_time)

    records.sort(key=lambda item: (item["user_id"], item["timestamp"], item["product_id"], item["action"]))
    return records


def render_seed_script(users, books, workspace_root):
    seed_script_path = os.path.join(workspace_root, "seed_book.py")
    category_defs_json = json.dumps(CATEGORY_DEFS, indent=4, ensure_ascii=False)
    users_json = json.dumps(users, indent=4, ensure_ascii=False)
    books_json = json.dumps(books, indent=4, ensure_ascii=False)

    script = f'''"""
Seed script generated by recommender-ai-service/utils/data_generator.py.
Creates catalog categories, users, and books from the latest generated dataset.
"""
import copy
import requests

BASE = "http://localhost:8000/api"
STAFF_BOOKS = f"{{BASE}}/staff/manage-books/"
CATALOG_ITEMS = f"{{BASE}}/catalog/items/"
CATEGORIES_URL = f"{{BASE}}/catalog/categories/"
CUSTOMERS_URL = f"{{BASE}}/customer/customers/"

CATEGORY_DEFS = {category_defs_json}
USERS = {users_json}
BOOKS = {books_json}


def ensure_categories():
    existing_cats = {{c["name"]: c["id"] for c in requests.get(CATEGORIES_URL).json()}}
    for cat in CATEGORY_DEFS:
        if cat["name"] not in existing_cats:
            response = requests.post(CATEGORIES_URL, json=cat)
            if response.status_code in (200, 201):
                existing_cats[cat["name"]] = response.json()["id"]
    return existing_cats


def create_users():
    success = 0
    for user in USERS:
        payload = {{
            "name": user["name"],
            "email": user["email"],
            "address": user["address"],
            "password": user["password"],
        }}
        try:
            response = requests.post(CUSTOMERS_URL, json=payload)
            if response.status_code in (200, 201):
                success += 1
        except Exception:
            pass
    print(f"Users created: {{success}}/{{len(USERS)}}")


def create_books(existing_cats):
    success = 0
    errors = []
    for book in BOOKS:
        payload = copy.deepcopy(book)
        category_name = payload.pop("category_name", "Novel")
        payload.pop("id", None)
        category_id = existing_cats.get(category_name)

        try:
            response = requests.post(STAFF_BOOKS, json=payload)
            if response.status_code not in (200, 201):
                errors.append(f"BOOK FAIL '{{book['title']}}': {{response.status_code}}")
                continue

            book_id = response.json().get("id")
            if book_id and category_id:
                catalog_payload = {{
                    "book_id": book_id,
                    "category": category_id,
                    "keywords": f"{{book['title']}} {{book['author']}} {{category_name}}",
                }}
                catalog_response = requests.put(f"{{CATALOG_ITEMS}}{{book_id}}/", json=catalog_payload)
                if catalog_response.status_code not in (200, 201):
                    errors.append(f"CATALOG FAIL '{{book['title']}}': {{catalog_response.status_code}}")

            success += 1
        except Exception as exc:
            errors.append(f"EXCEPTION '{{book['title']}}': {{exc}}")

    print(f"Books created: {{success}}/{{len(BOOKS)}}")
    if errors:
        print("Sample errors:")
        for error in errors[:10]:
            print(" ", error)


def main():
    categories = ensure_categories()
    create_users()
    create_books(categories)


if __name__ == "__main__":
    main()
'''

    with open(seed_script_path, "w", encoding="utf-8") as seed_file:
        seed_file.write(script)


def write_json(path, payload):
    with open(path, "w", encoding="utf-8") as output_file:
        json.dump(payload, output_file, indent=4, ensure_ascii=False)


def write_csv(path, records):
    with open(path, "w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=["user_id", "product_id", "action", "timestamp"])
        writer.writeheader()
        writer.writerows(records)


def generate_data():
    random.seed(RANDOM_SEED)

    service_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    workspace_root = os.path.dirname(service_root)
    data_dir = os.path.join(service_root, "data")
    os.makedirs(data_dir, exist_ok=True)

    csv_path = os.path.join(data_dir, "data_user500.csv")
    users_path = os.path.join(data_dir, "users.json")
    books_path = os.path.join(data_dir, "books.json")

    users = build_users()
    books = build_books()
    records = build_behavior_records(users, books)

    if len(records) < MIN_RECORDS:
        raise ValueError(f"Generated only {len(records)} records, expected at least {MIN_RECORDS}.")

    write_csv(csv_path, records)
    write_json(users_path, users)
    write_json(books_path, books)
    render_seed_script(users, books, workspace_root)

    print(f"Generated {len(users)} users")
    print(f"Generated {len(books)} books")
    print(f"Generated {len(records)} behavior records")
    print(f"CSV saved to {csv_path}")


if __name__ == "__main__":
    generate_data()
