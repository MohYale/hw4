# AI Prompts

This file is a log of the prompts used for Assignment 4. Each section is one problem: the problem number and title, the prompt used, and any follow-up prompts under that same heading.

---

## Problem 1 — Vibe coder prompts

### Prompt

I am starting assignment number 4. Please create an AI_prompts.md file. I want to log the prompts that I will use in this assignment. I want these prompts logged under the problem number and the title/heading associated with it. This is problem 1 with the heading: Vibe coder prompts. unzip data.zip in this folder.

---

## Problem 2 — Analyze the database

### Prompt

We are starting problem 2: Analyze the database. I want you to show me the first ten rows of the file data/campus.customs.db. I want to understand the contents of this database mainly catalogue, inventory and users.

### Follow-up

This prompt should be filed as a follow up under problem 2. I want you to create a harness for the agent that I will be using for this assignment; output/harness.md. I want you to have a line for each of the four tables that you showed me that also includes the table fields. I also want you to include one short line on why each field matters for the shop or the chatbot that we will be creating. Lets start with the catalogue table. This table is important because it shows the available products, its type and the price associated with it. The second table will be the inventory table. This table is important because it tells us the available sizes for each product and the quantity of each size that are available to purchase. The third table is users. This table contains the customers/users info including name, email and password. The fourth table is the chat_messages. This is important because it contains chat with the users.

---

## Problem 3 — Build the campus customs website

### Prompt

We will start problem 3: build the campus customs website. I want you to scaffold a react + vite + typescript  front end for the campus customs shop. I want you to put a navigation bar at the top of the website that links to the main pages: Home, products, about us, log in and create account. I want you to use the yalebulldogblue.com website as background to create the home page and the about us page. I want you to write it in a different manner; I do not want you to copy it directly from the website. On the product page, I want you to show images from the catalogue using the paths that are supplied. I want you to include basic product info; name, price, short description. If a user clicks on an item, I want you to open a single item page with large image of the product on one side, full product text on the other - description, price, sizes/stock if you have them). Clicking a card on products should take the shopper there. I also want you to add a chat interface in the bottom right of the site. I want yo to start a fastAPI app in backend/main.py just to serve products and images.

---

## Problem 4 — Create account and login

### Prompt

We will start problem 4: create account and login. I want you to build a normal create-account/login flow. This should include 1) create account: first name, last name, email, password and another field to confirm the password. 2) Log in: email and password. I want new accounds to go into the users table. I want you to store the passwords securely so that it cannot be hacked. You can salt them and then hash them. If you look at the initial campus_customs.db, it has a test user which has email, password and a hash function. The process for login will be as follows: 1) never un-hash a password. Only re-hash what the user typed and compare. 2) Read the salt out of the stored string - do not make a new one at login. 3) Hash the typed password with the same salt, then compare to the stored hash. I want the compare step does not exceed 3 seconds. 4) The signup and login must use the same hash settings; same function, same salt handling, same iteration count. if anything differ, even the correct password will not match. I want you to update the output/harness.md file to include what is stored for a user and how passwords are protected.

---

## Problem 5 — PydanticAI agent backend

### Prompt

We will do problem 5: PydanticAI agent backend. I want to build the shop chatbot as a pydanticai agent behind fastapi, plugged into your front-end chat widget. Put the API app in backend/main.py which we will run with uvicorn. I want the agent to have these 4 files: 1) backend/prompts/prompt.md - system prompt, 2) backend/agent.py - agent entry/wiring, 3) backend/tools.py - tools the agent can call, 4) backend/models.py - pydantic/pydanticai structured types. In main.py, expose a chat route so a message from the website returns a reply from the agent. I want the campus customs voice and safety basics into prompts.prompt.md. Update the models.py for chat replies/product cards as needed. In output/haress, I want you to note how the front end talks to FastAPI and how the agent is loaded (prompt file + model). I want you to make sure the backend runs from the backend/ folder liks this: uvicorn main:app --reload --port 8000

---

## Problem 6 — Tools: product info and stock

### Prompt

We will start problem 6: tools: product info and stock. I want to give the agent that we created tools that look up real information from campus_customs.db: product description, price, how many are in stock (by size when the customer asks). The agent must use the database - it should not invent or make up prices or quantities. If a size is out of stock, I want to say so clearly. I want you to expand prompts/prompt.md so the agent knows to call these tools for price and stock questions. Please update return types in models.py. In the output/harness.md, list each tool and explain which model fields you chose for lookup results and why.

---

## Problem 7 — Chat search that updates the page

### Prompt

We will start problem 7: chat search that updates the page. I want to add a new feature to the site. When a customer asks about a type of item, I want the website to dynamically to show the matching items as product cards (image, name, price and short info). For instances, if a user state what long sleeved T shirts do you have, I want you to show the available selection. This should be an API contract: the agent should return a structured product matches and then the front end renders them on the website. After the dynamic product cards are loaded, I want you to make sure the same single-item page behaviour that we build in problem 3 to work: each product card should still open that detail view (large image+ fill info_ when clicked. I want you to update prompts/prompt.md and output/harness.md so it is clear how search results reach the page.

---

## Problem 8 — Customer memory

### Prompt

We will start problem 8: Customer memory. When a shopper is logged in, save their chat history in the database in an appropriate table and reload it when they log in again. Our agent should know the person who is chatting (name, email). I want this added to the tools.py so that our agent can recall this tool in the future. I want you to review the campus customs page again and put enough context so that if someone is on the product page and asks "do you have this in pink", the agent should know which item they mean. I want guests of the website also to be able to chat but only keep history for a logged in users. I want you to document in output/harness.md how the user chat history if stored, what customer fields the agent sees and how page context is passed.

---

## Problem 9 — Usability improvements

### Prompt

Now we will be doing problem 9: usability improvements. My aim is to do two front end improvements and two back end improvement. For the front end, If a user forgets their password in the login page, I want you to give them an option to recover their password. We can send them an email with their password. I also want you to save the users size when they login, so that if they are of medium size, they would only see the available products in medium etc. For the backend improvement, I want the users to receive an email when the product is shipped. I also want you to do a real time inventory update by size and color so that customers never buy stock that is sold out. I want you to write these requests in output/usability.md as you build. For each improvement, I want you to say what you added and why it help a cumpus customs shopper.

---

## Problem 10 — Style the website

### Prompt

We will start problem 10: Style the website. This is a yale univeristy product website. I want you to add picture from Yale university to the website. The harkness tower, the cross campus, Evans hall, the main campus, the medical school, payne whitney gym. Add pictures of the univeristy to this website. I also want Handsome dan to appear on the webpage walking around the screen as customers shop using the website. I want you to write these requests in output/design.md and include the changes that I requested. I want to write that the importance of this is because it makes the website aesthetically pleasing, it will bring memories for the graduate customer and will remind the currently matriculating customer about the exclusivity of Yale univeristy.

---

## Problem 11 — Site testing (app check)

### Prompt

We will start problem 11: Site testing (app check). I want to test the live site. I want you to document it in output/app_check.html. I want you to create three clear screen shots with short caption so that i can submit with my assignement. Screenshot 1: Chat checking the inventory level of an item (honest stock/price from the database), Screenshot 2: The dynamic search-results cards appearing after a category question (e.g. hoodies), screenshot 3: one of the usability features you added in problem 9. I want you to make the HTML easy to grade: heading for each check, screenshot, one or two sentences on what the screenshot proves. I want you to put the screenshot images files in output/app_check_images/ and link them from app_check.html with relative paths; for example app_check_images/inventory.png

---

## Problem 12 — Audit trail, safety, finish harness

### Prompt

We will start problem 12: audit trail, safety, finish harness. I want you to keep an append only output/audit_trail.json of agent-loop activity (time, toold name, short args/result, stop reason). Do not wipe it between runs. I want you to add to the prompts/prompt.md these rule: 1) I want you to stop the task if you spend 90 seconds trying. 2) Do not do anything illegal. I want you to add this request to the output/harness.md so that it is clear how the system work: 1) model fields in mdoel.py and why I chose them, 2) tools and abilities, 3) safety rules, and 4) specs (loop limits, result caps, models, how to run front +back).

---

## Publish the work

### Prompt

I want you to create a folder in the work folder called hw4. I want our coding to be put in the Hw4 folder and I want it to be pushed to a public github repository. Show me that URL. I want the graders to be able to open the repo and clone my work so that they can grade me.

### Follow-up

I want you to create a folder in the work folder called hw4. I want our coding to be put in the Hw4 folder and I want it to be pushed to a public github repository. Show me that URL. I want the graders to be able to open the repo and clone my work so that they can grade me.  I want you to use the github app on my computer. Do not go to the github website

### Follow-up

I am signed in. push it
