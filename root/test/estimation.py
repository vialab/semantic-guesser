# Proper way to run this script:
# python -m root.test.estimation
# from semantic-guesser/

"""
Tests the accuracy of the Laplace estimator for probabilities of words in passwords.
Uses the framework from Manning and Schütze (1999), section 6.2.2 (see Table 6.4),
for comparison of accuracy of estimators.

Divides the data into training and test. Trains the Laplace estimator using the
training data. Then compares the predicted frequencies of frequencies with the
empirical frequencies of frequencies in the test data.

"""

from root.database import PwdDb
from collections import defaultdict

def main():
    verb_dist = defaultdict(lambda:0)
    noun_dist = defaultdict(lambda:0)

    db = PwdDb(1)
    while db.hasNext():
        segments = db.nextPwd()


if __name__ == "__main__":
    main()
