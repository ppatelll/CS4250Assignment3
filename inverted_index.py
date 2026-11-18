#-------------------------------------------------------------------------
# AUTHOR: Parth Patel
# FILENAME: inverted_index.py
# SPECIFICATION: Handles the documents and keeps the inverted index updated in MongoDB.
# FOR: CS 4250 - Assignment #3
# TIME SPENT: 2.5 hrs
#-------------------------------------------------------------------------

# Importing Python libraries
from pymongo import MongoClient
import string
from collections import Counter

# Connecting to MongoDB
client = MongoClient("mongodb://localhost:27017/")

# Accessing the database and collections
db = client["assignment3"]
documents = db["documents"]
inverted_index = db["inverted_index"]
documents.delete_many({})
inverted_index.delete_many({})

#-------------------------------------------------------------------------
# FUNCTION: getTermFrequencies
# SPECIFICATION: receives a text and returns the frequency of each term
#-------------------------------------------------------------------------
def getTermFrequencies(text):

    # Converting text to lowercase
    text = text.lower()

    # Removing punctuation
    text =text.translate(str.maketrans("", "", string.punctuation))

    # Splitting the text into terms
    words = text.split()

    # Returning the term frequencies
    return dict(Counter(words))


#-------------------------------------------------------------------------
# FUNCTION: addPosting
# SPECIFICATION: adds a posting to an existing term or creates a new term
#-------------------------------------------------------------------------
def addPosting(term, docId, tf):
    # Searching for the term in the inverted index
    temp = inverted_index.find_one({"term": term})

    # Creating a new term if it does not exist
    if temp== None:
        inverted_index.insert_one({"term": term, "postings": [{"docId": docId, "tf": tf}]})

    # Adding a posting if the term already exists
    else:
        inverted_index.update_one({"term": term},{"$push": {"postings": {"docId": docId, "tf": tf}}})


#-------------------------------------------------------------------------
# FUNCTION: removePosting
# SPECIFICATION: removes a document posting from a term and deletes the
#                term if its postings list becomes empty
#-------------------------------------------------------------------------
def removePosting(term, docId):

    # Removing the posting from the term
    inverted_index.update_one({"term": term}, {"$pull": {"postings":{"docId":docId}}})

    # Retrieving the term after removing the posting
    temp = inverted_index.find_one({"term":term})

    # Deleting the term if its postings list is empty
    if temp !=None:
        if len(temp["postings"]) == 0:
            inverted_index.delete_one({"term": term})


#-------------------------------------------------------------------------
# FUNCTION: insertDocument
# SPECIFICATION: inserts a document and updates the inverted index
#-------------------------------------------------------------------------
def insertDocument(document):
    # Inserting the document into the documents collection
    documents.insert_one(document)

    # Obtaining the term frequencies
    words =getTermFrequencies(document["text"])

    # Updating the inverted index
    for x in words:
        addPosting(x, document["_id"], words[x])


#-------------------------------------------------------------------------
# FUNCTION: updateDocument
# SPECIFICATION: updates a document and makes the corresponding changes
#                to the inverted index
#-------------------------------------------------------------------------
def updateDocument(docId, newText):
    # Retrieving the current document
    temp = documents.find_one({"_id":docId})
    if temp== None:
        return

    # Obtaining the old and new term frequencies
    old = getTermFrequencies(temp["text"])
    new =getTermFrequencies(newText)

    # Processing terms that existed in the old document
    for x in old:
        if x not in new:
            removePosting(x, docId)
        elif old[x]!= new[x]:
            inverted_index.update_one({"term": x,"postings.docId": docId},{"$set": {"postings.$.tf": new[x]}})

    # Processing terms that occur only in the new document
    for x in new:
        if x not in old:
            addPosting(x, docId, new[x])

    # Updating the document text
    documents.update_one({"_id": docId},{"$set": {"text": newText}})

#-------------------------------------------------------------------------
# FUNCTION: deleteDocument
# SPECIFICATION: deletes a document and removes all of its postings from
#                the inverted index
#-------------------------------------------------------------------------
def deleteDocument(docId):

    # Retrieving the document before deleting it
    temp = documents.find_one({"_id": docId})
    if temp == None:
        return

    # Obtaining the terms contained in the document
    words= getTermFrequencies(temp["text"])

    # Removing the document from every corresponding posting list
    for x in words:
        removePosting(x, docId)

    # Deleting the document
    documents.delete_one({"_id": docId})


#-------------------------------------------------------------------------
# Executing the sequence of operations
#-------------------------------------------------------------------------

# Operation 1: document 1 is obtained
document1 = {
    "_id": 1,
    "text": "Summer rain is common in Florida."
}
insertDocument(document1)

# Operation 2: document 2 is obtained
document2 = {
    "_id": 2,
    "text": "Summer is hot in Arizona."
}
insertDocument(document2)

# Operation 3: document 1 is updated
updateDocument(
    1,
    "Summer rain is hot rain in Florida."
)

# Operation 4: document 3 is obtained
document3 = {
    "_id": 3,
    "text": "Hot summer rain in California."
}
insertDocument(document3)

# Operation 5: document 2 is deleted
deleteDocument(2)

# Operation 6: print the content of the documents and inverted_index collections
print("Documents")
for x in documents.find().sort("_id", 1):
    print(x)
print("\nInverted")
for x in inverted_index.find().sort("term",1):
    x.pop("_id", None)
    x["postings"].sort(key= lambda y: y["docId"])
    print(x)
client.close()