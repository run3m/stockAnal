# Import necessary libraries
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

import messageClassifcations

# Sample dataset - replace with your own labeled data
corpus = messageClassifcations.fetch_basic_stocks_data + messageClassifcations.generate_new_report_data + messageClassifcations.old_reports_data + messageClassifcations.retry_basic_fetch_data + messageClassifcations.show_fields_data + messageClassifcations.start_conversation_data;
# Split the data into features (X) and labels (y)
X, y = zip(*corpus)

# Text preprocessing and feature extraction
count_vectorizer = CountVectorizer(stop_words='english')
tfidf_transformer = TfidfTransformer()
X_counts = count_vectorizer.fit_transform(X)
X_tfidf = tfidf_transformer.fit_transform(X_counts)

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X_tfidf, y, test_size=0.2, random_state=42)

# Create and train the Multinomial Naive Bayes classifier
clf = MultinomialNB()
clf.fit(X_train, y_train)

# Make predictions on the test data
y_pred = clf.predict(X_test)

# Evaluate the model
accuracy = accuracy_score(y_test, y_pred)
print(f"Accuracy: {accuracy:.2f}")

# Generate a classification report for more detailed evaluation
print(classification_report(y_test, y_pred))

# Now you can use the trained model to classify new sentences
new_sentences = ["Hey, i want to generate a report", "It is an old report"]
X_new_counts = count_vectorizer.transform(new_sentences)
X_new_tfidf = tfidf_transformer.transform(X_new_counts)
predictions = clf.predict(X_new_tfidf)

for sentence, prediction in zip(new_sentences, predictions):
    print(f"Sentence: '{sentence}' - Predicted Label: {prediction}")
