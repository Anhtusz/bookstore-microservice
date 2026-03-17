"""
Seed script: Add 50 real books to the bookstore microservice.
"""
import requests

BASE = "http://localhost:8000/api"
STAFF_BOOKS = f"{BASE}/staff/manage-books/"
CATALOG_ITEMS = f"{BASE}/catalog/items/"
CATEGORIES_URL = f"{BASE}/catalog/categories/"

CATEGORY_DEFS = [
    {"name": "Detective",       "description": "Mystery & Crime fiction"},
    {"name": "Adventure",       "description": "Adventure & Action stories"},
    {"name": "Novel",           "description": "Contemporary & Classic novels"},
    {"name": "Science Fiction", "description": "Sci-Fi & Speculative fiction"},
    {"name": "Fantasy",         "description": "Fantasy & Mythology"},
    {"name": "Self-Help",       "description": "Personal development & Growth"},
    {"name": "Biography",       "description": "Biographies & Memoirs"},
    {"name": "History",         "description": "Historical non-fiction"},
    {"name": "Psychology",      "description": "Psychology & Behavior"},
]

existing_cats = {c["name"]: c["id"] for c in requests.get(CATEGORIES_URL).json()}
print("Existing categories:", existing_cats)

for cat in CATEGORY_DEFS:
    if cat["name"] not in existing_cats:
        r = requests.post(CATEGORIES_URL, json=cat)
        if r.status_code == 201:
            existing_cats[cat["name"]] = r.json()["id"]
            print(f"  Created category: {cat['name']} => id={existing_cats[cat['name']]}")

C = existing_cats

BOOKS = [
    {"title": "To Kill a Mockingbird", "author": "Harper Lee", "price": 12.99, "stock": 30, "description": "The unforgettable novel of a childhood in a sleepy Southern town and the crisis of conscience that rocked it. Lawyer Atticus Finch defends a Black man unjustly accused of raping a white woman in the 1930s Deep South.", "image_url": "https://covers.openlibrary.org/b/id/8810494-L.jpg", "category": C.get("Novel")},
    {"title": "1984", "author": "George Orwell", "price": 10.99, "stock": 45, "description": "A dystopian novel about a totalitarian society ruled by Big Brother, mass surveillance, and psychological manipulation. Winston Smith rebelliously seeks truth and love in a world where history is rewritten daily.", "image_url": "https://covers.openlibrary.org/b/id/8575708-L.jpg", "category": C.get("Novel")},
    {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald", "price": 9.99, "stock": 28, "description": "The story of the mysteriously wealthy Jay Gatsby and his love for the beautiful Daisy Buchanan, set against the backdrop of lavish parties in 1920s Long Island.", "image_url": "https://covers.openlibrary.org/b/id/8432593-L.jpg", "category": C.get("Novel")},
    {"title": "Pride and Prejudice", "author": "Jane Austen", "price": 8.99, "stock": 50, "description": "Elizabeth Bennet navigates issues of manners, education, and marriage in early 19th-century England, while sparring with the proud Mr. Darcy.", "image_url": "https://covers.openlibrary.org/b/id/8479576-L.jpg", "category": C.get("Novel")},
    {"title": "The Catcher in the Rye", "author": "J.D. Salinger", "price": 11.99, "stock": 22, "description": "Holden Caulfield narrates his turbulent days in New York City after being expelled from prep school, railing against phoniness and searching for authentic human connection.", "image_url": "https://covers.openlibrary.org/b/id/8231432-L.jpg", "category": C.get("Novel")},
    {"title": "Brave New World", "author": "Aldous Huxley", "price": 10.49, "stock": 35, "description": "Set in a futuristic World State where citizens are genetically engineered, the novel explores a society of superficial happiness achieved through conditioning and the drug Soma.", "image_url": "https://covers.openlibrary.org/b/id/8406786-L.jpg", "category": C.get("Novel")},
    {"title": "Of Mice and Men", "author": "John Steinbeck", "price": 9.49, "stock": 20, "description": "A tale about the bond between two traveling workers, George and Lennie, during the Great Depression, exploring friendship, isolation, and the impossible American Dream.", "image_url": "https://covers.openlibrary.org/b/id/8225315-L.jpg", "category": C.get("Novel")},
    {"title": "The Alchemist", "author": "Paulo Coelho", "price": 13.99, "stock": 60, "description": "A philosophical novel following Santiago, a young Andalusian shepherd, on his journey to Egypt in pursuit of his Personal Legend and the world's greatest treasure.", "image_url": "https://covers.openlibrary.org/b/id/8294385-L.jpg", "category": C.get("Novel")},
    {"title": "Jane Eyre", "author": "Charlotte Brontë", "price": 9.99, "stock": 25, "description": "Jane Eyre's journey from orphaned child to governess at Thornfield Hall, where she falls in love with the brooding Mr. Rochester—but his dark secret threatens everything.", "image_url": "https://covers.openlibrary.org/b/id/8231942-L.jpg", "category": C.get("Novel")},
    {"title": "Wuthering Heights", "author": "Emily Brontë", "price": 9.49, "stock": 18, "description": "The wild, passionate love story between Catherine Earnshaw and the foundling Heathcliff on the Yorkshire moors — a gothic tale of obsession, revenge, and the supernatural.", "image_url": "https://covers.openlibrary.org/b/id/8228941-L.jpg", "category": C.get("Novel")},
    {"title": "The Hound of the Baskervilles", "author": "Arthur Conan Doyle", "price": 10.99, "stock": 40, "description": "Sherlock Holmes and Dr. Watson investigate the legend of a demonic hound said to haunt the Baskerville family on the Dartmoor moors.", "image_url": "https://covers.openlibrary.org/b/id/8360214-L.jpg", "category": C.get("Detective")},
    {"title": "Murder on the Orient Express", "author": "Agatha Christie", "price": 12.49, "stock": 35, "description": "Hercule Poirot investigates the murder of an American tycoon on the luxurious Orient Express, where every passenger is a suspect.", "image_url": "https://covers.openlibrary.org/b/id/8285259-L.jpg", "category": C.get("Detective")},
    {"title": "Gone Girl", "author": "Gillian Flynn", "price": 14.99, "stock": 30, "description": "On their fifth wedding anniversary, Amy Dunne disappears, leaving her husband Nick as the prime suspect. A chilling psychological thriller of marriage, lies, and obsession.", "image_url": "https://covers.openlibrary.org/b/id/8235164-L.jpg", "category": C.get("Detective")},
    {"title": "The Girl with the Dragon Tattoo", "author": "Stieg Larsson", "price": 15.99, "stock": 25, "description": "Journalist Mikael Blomkvist and hacker Lisbeth Salander investigate the 40-year-old disappearance of the Vanger family's niece in this riveting Swedish thriller.", "image_url": "https://covers.openlibrary.org/b/id/8406876-L.jpg", "category": C.get("Detective")},
    {"title": "In the Woods", "author": "Tana French", "price": 13.49, "stock": 20, "description": "Dublin detective Rob Ryan investigates a murder near the same woods where he had a traumatic childhood experience, blurring the lines between past and present.", "image_url": "https://covers.openlibrary.org/b/id/7895947-L.jpg", "category": C.get("Detective")},
    {"title": "Dune", "author": "Frank Herbert", "price": 17.99, "stock": 40, "description": "Young Paul Atreides inherits the desert planet Arrakis, the only source of the universe's most precious resource—spice—and must navigate treacherous politics and prophecy.", "image_url": "https://covers.openlibrary.org/b/id/8226791-L.jpg", "category": C.get("Science Fiction")},
    {"title": "The Hitchhiker's Guide to the Galaxy", "author": "Douglas Adams", "price": 11.99, "stock": 45, "description": "Seconds before Earth is demolished for a hyperspace bypass, Arthur Dent is whisked away by his alien friend Ford Prefect on a hilarious journey across the universe.", "image_url": "https://covers.openlibrary.org/b/id/8406862-L.jpg", "category": C.get("Science Fiction")},
    {"title": "Ender's Game", "author": "Orson Scott Card", "price": 13.99, "stock": 30, "description": "Gifted child Andrew Ender Wiggin is trained in combat simulations to become Earth's military genius against an alien invasion—but nothing is what it seems.", "image_url": "https://covers.openlibrary.org/b/id/8113090-L.jpg", "category": C.get("Science Fiction")},
    {"title": "Neuromancer", "author": "William Gibson", "price": 12.49, "stock": 20, "description": "The seminal cyberpunk novel: washed-up computer hacker Henry Case is hired for one last job—to pull off the ultimate heist in a world dominated by AI and corporations.", "image_url": "https://covers.openlibrary.org/b/id/8368664-L.jpg", "category": C.get("Science Fiction")},
    {"title": "The Martian", "author": "Andy Weir", "price": 14.99, "stock": 35, "description": "Astronaut Mark Watney is stranded alone on Mars after a dust storm. Using science and wit, he must survive until a rescue mission can reach him—years away.", "image_url": "https://covers.openlibrary.org/b/id/8231042-L.jpg", "category": C.get("Science Fiction")},
    {"title": "The Hobbit", "author": "J.R.R. Tolkien", "price": 14.99, "stock": 50, "description": "Bilbo Baggins, a comfort-loving hobbit, is swept into an epic quest with Gandalf and a company of dwarves to reclaim the Lonely Mountain from the dragon Smaug.", "image_url": "https://covers.openlibrary.org/b/id/8406680-L.jpg", "category": C.get("Fantasy")},
    {"title": "The Name of the Wind", "author": "Patrick Rothfuss", "price": 16.99, "stock": 30, "description": "Kvothe, the legendary wizard-hero, narrates his own life story: from his tragic childhood to his days at a magical university and his hunt for the Chandrian.", "image_url": "https://covers.openlibrary.org/b/id/8406674-L.jpg", "category": C.get("Fantasy")},
    {"title": "Harry Potter and the Sorcerer's Stone", "author": "J.K. Rowling", "price": 13.99, "stock": 80, "description": "Orphan Harry Potter discovers on his 11th birthday that he is a wizard and is accepted to Hogwarts School of Witchcraft and Wizardry, where he uncovers his destiny.", "image_url": "https://covers.openlibrary.org/b/id/10110415-L.jpg", "category": C.get("Fantasy")},
    {"title": "A Game of Thrones", "author": "George R.R. Martin", "price": 18.99, "stock": 40, "description": "Seven noble families fight for the Iron Throne of Westeros in a brutal struggle for power, while an ancient evil stirs beyond the Wall in the North.", "image_url": "https://covers.openlibrary.org/b/id/9255566-L.jpg", "category": C.get("Fantasy")},
    {"title": "The Lion, the Witch and the Wardrobe", "author": "C.S. Lewis", "price": 11.99, "stock": 45, "description": "Four siblings step through a magical wardrobe into Narnia—a land frozen in eternal winter by the White Witch—where they join the lion Aslan in a battle for freedom.", "image_url": "https://covers.openlibrary.org/b/id/8406860-L.jpg", "category": C.get("Fantasy")},
    {"title": "Atomic Habits", "author": "James Clear", "price": 16.99, "stock": 70, "description": "A proven framework for building good habits and breaking bad ones, showing how tiny 1% improvements compound into remarkable results over time.", "image_url": "https://covers.openlibrary.org/b/id/10368083-L.jpg", "category": C.get("Self-Help")},
    {"title": "The 7 Habits of Highly Effective People", "author": "Stephen R. Covey", "price": 15.99, "stock": 55, "description": "A holistic, principle-centered approach to personal and professional effectiveness, teaching that true success comes from aligning your actions to timeless principles.", "image_url": "https://covers.openlibrary.org/b/id/8366398-L.jpg", "category": C.get("Self-Help")},
    {"title": "How to Win Friends and Influence People", "author": "Dale Carnegie", "price": 13.99, "stock": 60, "description": "Timeless principles for improving human relations and influencing others positively—how to make people like you, win them to your way of thinking, and change behavior.", "image_url": "https://covers.openlibrary.org/b/id/8406946-L.jpg", "category": C.get("Self-Help")},
    {"title": "Thinking, Fast and Slow", "author": "Daniel Kahneman", "price": 17.49, "stock": 40, "description": "Nobel laureate Daniel Kahneman explores the two systems that drive the way we think: the fast, intuitive System 1, and the slower, more deliberate System 2.", "image_url": "https://covers.openlibrary.org/b/id/8406844-L.jpg", "category": C.get("Self-Help")},
    {"title": "The Power of Now", "author": "Eckhart Tolle", "price": 14.49, "stock": 35, "description": "A guide to spiritual enlightenment, teaching that true peace and happiness come from embracing the present moment and freeing yourself from the grip of the ego.", "image_url": "https://covers.openlibrary.org/b/id/8406740-L.jpg", "category": C.get("Self-Help")},
    {"title": "Meditations", "author": "Marcus Aurelius", "price": 10.99, "stock": 45, "description": "Personal reflections of the Roman Emperor Marcus Aurelius, offering a Stoic guide to virtue, self-discipline, and living in harmony with nature.", "image_url": "https://covers.openlibrary.org/b/id/8406824-L.jpg", "category": C.get("Self-Help")},
    {"title": "The Diary of a Young Girl", "author": "Anne Frank", "price": 11.99, "stock": 40, "description": "Anne Frank's intimate diary, written while in hiding during the Nazi occupation of the Netherlands, is a powerful human document of hope, fear, and adolescence.", "image_url": "https://covers.openlibrary.org/b/id/8406898-L.jpg", "category": C.get("Biography")},
    {"title": "Long Walk to Freedom", "author": "Nelson Mandela", "price": 16.99, "stock": 25, "description": "Nelson Mandela's autobiography, from his childhood in rural Transkei to his 27 years in prison and finally his presidency of a democratic South Africa.", "image_url": "https://covers.openlibrary.org/b/id/2401882-L.jpg", "category": C.get("Biography")},
    {"title": "Steve Jobs", "author": "Walter Isaacson", "price": 18.99, "stock": 30, "description": "The biography of Apple's co-founder, based on over 40 interviews with Jobs plus hundreds of interviews with family, friends, and rivals. A riveting portrait of a creative genius.", "image_url": "https://covers.openlibrary.org/b/id/7279416-L.jpg", "category": C.get("Biography")},
    {"title": "The Story of My Experiments with Truth", "author": "Mahatma Gandhi", "price": 12.99, "stock": 20, "description": "Mahatma Gandhi's autobiography, covering his life from childhood through 1921, detailing his spiritual development and the formation of his philosophy of nonviolent resistance.", "image_url": "https://covers.openlibrary.org/b/id/8406736-L.jpg", "category": C.get("Biography")},
    {"title": "I Am Malala", "author": "Malala Yousafzai", "price": 13.99, "stock": 30, "description": "The story of the Pakistani girl who stood up for girls' education and was shot by the Taliban at age 15, surviving to become a global advocate for children's rights.", "image_url": "https://covers.openlibrary.org/b/id/8406960-L.jpg", "category": C.get("Biography")},
    {"title": "Sapiens: A Brief History of Humankind", "author": "Yuval Noah Harari", "price": 19.99, "stock": 50, "description": "A bold survey of human history spanning 70,000 years, from the Cognitive Revolution to the present day, exploring how biology and history defined us.", "image_url": "https://covers.openlibrary.org/b/id/8406700-L.jpg", "category": C.get("History")},
    {"title": "Guns, Germs, and Steel", "author": "Jared Diamond", "price": 17.99, "stock": 30, "description": "A Pulitzer Prize-winning explanation of why Western civilizations came to dominate the world—not through racial superiority, but through geography, disease, and food production.", "image_url": "https://covers.openlibrary.org/b/id/8406838-L.jpg", "category": C.get("History")},
    {"title": "The Art of War", "author": "Sun Tzu", "price": 8.99, "stock": 70, "description": "An ancient Chinese military treatise written circa 5th century BC, offering timeless wisdom on strategy, tactics, and winning conflicts that is still studied by military and business leaders.", "image_url": "https://covers.openlibrary.org/b/id/8406882-L.jpg", "category": C.get("History")},
    {"title": "A People's History of the United States", "author": "Howard Zinn", "price": 16.99, "stock": 22, "description": "A landmark work of revisionist history tracing the United States from the perspective of workers, slaves, women, Native Americans, and all those left out of conventional histories.", "image_url": "https://covers.openlibrary.org/b/id/8406906-L.jpg", "category": C.get("History")},
    {"title": "The Silk Roads", "author": "Peter Frankopan", "price": 18.99, "stock": 20, "description": "A new history of the world that recenters civilization on the routes connecting East and West, revealing how empires from Persia to China shaped the modern globe.", "image_url": "https://covers.openlibrary.org/b/id/8406756-L.jpg", "category": C.get("History")},
    {"title": "Man's Search for Meaning", "author": "Viktor E. Frankl", "price": 12.99, "stock": 55, "description": "Psychiatrist Viktor Frankl describes his experiences in Nazi death camps and argues that meaning — not pleasure — is the primary human motivational force.", "image_url": "https://covers.openlibrary.org/b/id/8406728-L.jpg", "category": C.get("Psychology")},
    {"title": "The Interpretation of Dreams", "author": "Sigmund Freud", "price": 14.99, "stock": 18, "description": "Freud's masterwork, introducing the unconscious mind through dream analysis. He argues that dreams are wish fulfillments shaped by repressed desires and childhood experiences.", "image_url": "https://covers.openlibrary.org/b/id/8406896-L.jpg", "category": C.get("Psychology")},
    {"title": "Influence: The Psychology of Persuasion", "author": "Robert B. Cialdini", "price": 15.99, "stock": 40, "description": "Dr. Cialdini explains the six universal principles of influence—reciprocity, commitment, social proof, authority, liking, and scarcity—and how to use them ethically.", "image_url": "https://covers.openlibrary.org/b/id/8406918-L.jpg", "category": C.get("Psychology")},
    {"title": "The Power of Habit", "author": "Charles Duhigg", "price": 15.49, "stock": 38, "description": "Drawing on scientific discoveries, Duhigg explains why habits exist, how they work in the brain, and how to harness them to transform your life, business, and society.", "image_url": "https://covers.openlibrary.org/b/id/8406830-L.jpg", "category": C.get("Psychology")},
    {"title": "Flow: The Psychology of Optimal Experience", "author": "Mihaly Csikszentmihalyi", "price": 14.99, "stock": 25, "description": "Psychologist Csikszentmihalyi's theory of flow — the state of complete immersion in a challenging activity — as the key to genuine happiness and a fulfilled life.", "image_url": "https://covers.openlibrary.org/b/id/8406828-L.jpg", "category": C.get("Psychology")},
    {"title": "Into the Wild", "author": "Jon Krakauer", "price": 13.99, "stock": 30, "description": "The true story of Christopher McCandless, who abandoned his privileged life after college to hitchhike to Alaska and live alone in the wilderness — with tragic consequences.", "image_url": "https://covers.openlibrary.org/b/id/8406726-L.jpg", "category": C.get("Adventure")},
    {"title": "Around the World in 80 Days", "author": "Jules Verne", "price": 9.99, "stock": 35, "description": "Victorian gentleman Phileas Fogg accepts a £20,000 wager to circumnavigate the globe in just 80 days with his valet Passepartout, encountering dangers at every turn.", "image_url": "https://covers.openlibrary.org/b/id/8406670-L.jpg", "category": C.get("Adventure")},
    {"title": "The Old Man and the Sea", "author": "Ernest Hemingway", "price": 10.99, "stock": 28, "description": "An aging Cuban fisherman struggles alone in the Gulf Stream to catch a giant marlin, testing the limits of human endurance and indomitable spirit.", "image_url": "https://covers.openlibrary.org/b/id/8406688-L.jpg", "category": C.get("Adventure")},
    {"title": "Life of Pi", "author": "Yann Martel", "price": 13.49, "stock": 32, "description": "Sixteen-year-old Pi Patel survives a shipwreck and finds himself stranded on a lifeboat in the Pacific Ocean with a Bengal tiger for 227 days.", "image_url": "https://covers.openlibrary.org/b/id/8406692-L.jpg", "category": C.get("Adventure")},
    {"title": "The Kite Runner", "author": "Khaled Hosseini", "price": 13.99, "stock": 35, "description": "The story of Amir, a wealthy boy from Kabul, and his servant Hassan — a tale of friendship, betrayal, guilt, and redemption set against the turbulent history of Afghanistan.", "image_url": "https://covers.openlibrary.org/b/id/8406694-L.jpg", "category": C.get("Novel")},
    {"title": "One Hundred Years of Solitude", "author": "Gabriel García Márquez", "price": 14.99, "stock": 28, "description": "The epic magical realist saga of the Buendía family across seven generations in the mythical town of Macondo, exploring time, memory, and the cycles of human history.", "image_url": "https://covers.openlibrary.org/b/id/8406702-L.jpg", "category": C.get("Novel")},
]

print(f"\n--- Creating {len(BOOKS)} books ---")
success = 0
errors = []

for book in BOOKS:
    category_id = book.pop("category", None)
    try:
        r = requests.post(STAFF_BOOKS, json=book)
        if r.status_code not in (200, 201):
            errors.append(f"BOOK FAIL '{book['title']}': {r.status_code}")
            continue

        book_id = r.json().get("id")

        if book_id and category_id:
            cat_r = requests.put(f"{CATALOG_ITEMS}{book_id}/", json={
                "book_id": book_id,
                "category": category_id,
                "keywords": f"{book['title']} {book['author']}"
            })
            if cat_r.status_code not in (200, 201):
                errors.append(f"CATALOG FAIL '{book['title']}': {cat_r.status_code}")

        success += 1
        print(f"  [{success:02d}/{len(BOOKS)}] {book['title']}")
    except Exception as e:
        errors.append(f"EXCEPTION '{book['title']}': {e}")

print(f"\n Done: {success}/{len(BOOKS)} books created")
if errors:
    print("\n ERRORS:")
    for e in errors:
        print(" ", e)
