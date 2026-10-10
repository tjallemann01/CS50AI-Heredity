import csv
import itertools
import sys

PROBS = {

    # Unconditional probabilities for having gene
    "gene": {
        2: 0.01,
        1: 0.03,
        0: 0.96
    },

    "trait": {

        # Probability of trait given two copies of gene
        2: {
            True: 0.65,
            False: 0.35
        },

        # Probability of trait given one copy of gene
        1: {
            True: 0.56,
            False: 0.44
        },

        # Probability of trait given no gene
        0: {
            True: 0.01,
            False: 0.99
        }
    },

    # Mutation probability
    "mutation": 0.01
}


def main():

    # Check for proper usage
    if len(sys.argv) != 2:
        sys.exit("Usage: python heredity.py data.csv")
    people = load_data(sys.argv[1])

    # Keep track of gene and trait probabilities for each person
    probabilities = {
        person: {
            "gene": {
                2: 0,
                1: 0,
                0: 0
            },
            "trait": {
                True: 0,
                False: 0
            }
        }
        for person in people
    }

    # Loop over all sets of people who might have the trait
    names = set(people)
    for have_trait in powerset(names):

        # Check if current set of people violates known information
        fails_evidence = any(
            (people[person]["trait"] is not None and
             people[person]["trait"] != (person in have_trait))
            for person in names
        )
        if fails_evidence:
            continue

        # Loop over all sets of people who might have the gene
        for one_gene in powerset(names):
            for two_genes in powerset(names - one_gene):

                # Update probabilities with new joint probability
                p = joint_probability(people, one_gene, two_genes, have_trait)
                update(probabilities, one_gene, two_genes, have_trait, p)

    # Ensure probabilities sum to 1
    normalize(probabilities)

    # Print results
    for person in people:
        print(f"{person}:")
        for field in probabilities[person]:
            print(f"  {field.capitalize()}:")
            for value in probabilities[person][field]:
                p = probabilities[person][field][value]
                print(f"    {value}: {p:.4f}")


def load_data(filename):
    """
    Load gene and trait data from a file into a dictionary.
    File assumed to be a CSV containing fields name, mother, father, trait.
    mother, father must both be blank, or both be valid names in the CSV.
    trait should be 0 or 1 if trait is known, blank otherwise.
    """
    data = dict()
    with open(filename) as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row["name"]
            data[name] = {
                "name": name,
                "mother": row["mother"] or None,
                "father": row["father"] or None,
                "trait": (True if row["trait"] == "1" else
                          False if row["trait"] == "0" else None)
            }
    return data


def powerset(s):
    """
    Return a list of all possible subsets of set s.
    """
    s = list(s)
    return [
        set(s) for s in itertools.chain.from_iterable(
            itertools.combinations(s, r) for r in range(len(s) + 1)
        )
    ]


def joint_probability(people, one_gene, two_genes, have_trait):
    """
    Compute and return a joint probability.
    """

    probability = 1

    def gene_count(person):
        if person in two_genes:
            return 2
        if person in one_gene:
            return 1
        return 0

    def pass_probability(person):
        """
        Probability that a parent passes the gene,
        accounting for mutation.
        """
        genes = gene_count(person)
        mutation = PROBS["mutation"]

        if genes == 2:
            return 1 - mutation
        if genes == 1:
            return 0.5
        return mutation

    for person in people:

        genes = gene_count(person)
        has_trait = person in have_trait

        mother = people[person]["mother"]
        father = people[person]["father"]

        # Case 1: No parental information available
        if mother is None and father is None:
            gene_probability = PROBS["gene"][genes]

        # Case 2: Gene inheritance from parents
        else:
            from_mother = pass_probability(mother)
            from_father = pass_probability(father)

            if genes == 2:
                gene_probability = (
                    from_mother * from_father
                )

            elif genes == 1:
                gene_probability = (
                    from_mother * (1 - from_father)
                    + (1 - from_mother) * from_father
                )

            else:
                gene_probability = (
                    (1 - from_mother) * (1 - from_father)
                )

        # Probability of exhibiting the trait
        trait_probability = PROBS["trait"][genes][has_trait]

        # Accumulate joint probability
        probability *= gene_probability * trait_probability

    return probability


def update(probabilities, one_gene, two_genes, have_trait, p):
    """
    Add to `probabilities` a new joint probability `p`.
    """

    for person in probabilities:

        # Determine the number of gene copies
        if person in two_genes:
            genes = 2
        elif person in one_gene:
            genes = 1
        else:
            genes = 0

        # Determine whether the person has the trait
        has_trait = person in have_trait

        # Accumulate probability for gene distribution
        probabilities[person]["gene"][genes] += p

        # Accumulate probability for trait distribution
        probabilities[person]["trait"][has_trait] += p


def normalize(probabilities):
    """
    Update `probabilities` such that each probability
    distribution is normalized.
    """

    for person in probabilities:

        # Normalize gene and trait distributions separately
        for category in ["gene", "trait"]:

            distribution = probabilities[person][category]

            # Calculate the sum of probabilities
            total = sum(distribution.values())

            # Normalize each probability
            if total > 0:
                for value in distribution:
                    distribution[value] /= total


if __name__ == "__main__":
    main()
