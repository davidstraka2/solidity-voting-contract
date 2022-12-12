# !! IMPORTANT !!
# If coverage report is empty, see another IMPORTANT comment in the contract
# implementation and follow the instructions given.

# !! IMPORTANT !!
# The functions `getSubjects`, and `getSubject` didn't show up in my coverage
# report at all and therefore I was unable to ensure that they are adequately
# covered (that said I do assume that they are 100% covered). (see also
# https://github.com/eth-brownie/brownie/issues/1536 or my comment on Discord
# https://discord.com/channels/867746290678104064/1031550364966735912/1043134492811989032)

# !! IMPORTANT !!
# If you're getting the following error:
# `AttributeError: 'NoneType' object has no attribute '_with_attr'`
# make sure you're running Brownie version >= 1.18.1.
# (see https://stackoverflow.com/a/71908026,
# https://github.com/eth-brownie/brownie/issues/1434#issuecomment-1044962178,
# https://stackoverflow.com/a/71995811)

# Note on coverage:
# Functions `votePositive` and `voteNegative` don't have exactly 100% coverage,
# but as far as I can tell, all code branches that can be reached are covered,
# and uncovered code branches likely include those that can only be reached with
# invalid contract state.

import brownie
import pytest


@pytest.fixture(scope="module", autouse=True)
def add_accounts(accounts):
    for i in range(0, 20):
        accounts.add()

@pytest.fixture(scope="module", autouse=True)
def d21(D21, accounts):
    contract = D21.deploy({"from": accounts[0]})
    yield contract

@pytest.fixture(autouse=True)
def isolation(fn_isolation):
    pass

def test_get_init_subjects(d21):
    subjects = d21.getSubjects()
    assert len(subjects) == 0

def test_get_invalid_subject(d21, accounts):
    subject = d21.getSubject(accounts[1])
    assert len(subject[0]) == 0
    assert subject[1] == 0

def test_add_and_get_subject(d21):
    d21.addSubject("a")
    subjects = d21.getSubjects()
    assert len(subjects) == 1
    subject = d21.getSubject(subjects[0])
    assert subject[0] == "a"
    assert subject[1] == 0

def test_add_and_get_multiple_subjects(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    subjects = d21.getSubjects()
    assert len(subjects) == 3
    [subjectAAddr, subjectBAddr, subjectCAddr] = subjects
    subjectA = d21.getSubject(subjectAAddr)
    subjectB = d21.getSubject(subjectBAddr)
    subjectC = d21.getSubject(subjectCAddr)
    assert subjectA[0] == "a"
    assert subjectB[0] == "b"
    assert subjectC[0] == "c"

def test_add_already_added_subject(d21):
    d21.addSubject("a")
    with brownie.reverts("typed error: 0x2f2eb0c9"):
        d21.addSubject("a")

def test_add_voter(d21, accounts):
    d21.addVoter(accounts[10], {"from": accounts[0]})

def test_add_voter_as_non_owner(d21, accounts):
    with brownie.reverts("dev: OnlyOwner"):
        d21.addVoter(accounts[10], {"from": accounts[1]})

def test_add_already_added_voter(d21, accounts):
    d21.addVoter(accounts[10], {"from": accounts[0]})
    with brownie.reverts("typed error: 0x7c722b56"):
        d21.addVoter(accounts[10], {"from": accounts[0]})

def test_vote_positive_first(d21, accounts):
    d21.addSubject("a")
    subjectAddr = d21.getSubjects()[0]
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAddr, {"from": accounts[10]})
    subject = d21.getSubject(subjectAddr)
    assert subject[1] == 1

def test_vote_positive_second(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    subjectA = d21.getSubject(subjectAAddr)
    subjectB = d21.getSubject(subjectBAddr)
    assert subjectA[1] == 1
    assert subjectB[1] == 1

def test_vote_positive_third(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    [subjectAAddr, subjectBAddr, subjectCAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x8a97940b"):
        d21.votePositive(subjectCAddr, {"from": accounts[10]})

def test_vote_positive_after_deadline(d21, accounts):
    d21.addSubject("a")
    subjectAddr = d21.getSubjects()[0]
    d21.addVoter(accounts[10], {"from": accounts[0]})
    brownie.chain.sleep(7 * 24 * 60 * 60)
    brownie.chain.mine()
    with brownie.reverts("typed error: 0x7a19ed05"):
        d21.votePositive(subjectAddr, {"from": accounts[10]})

def test_vote_positive_without_registration(d21, accounts):
    d21.addSubject("a")
    subjectAddr = d21.getSubjects()[0]
    with brownie.reverts("typed error: 0xd4e876ef"):
        d21.votePositive(subjectAddr, {"from": accounts[10]})

def test_vote_positive_for_unregistred_subject(d21, accounts):
    d21.addVoter(accounts[10], {"from": accounts[0]})
    with brownie.reverts("typed error: 0xcff887c5"):
        d21.votePositive(accounts[1], {"from": accounts[10]})

def test_vote_positive_twice_for_the_same_subject(d21, accounts):
    d21.addSubject("a")
    subjectAddr = d21.getSubjects()[0]
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x26519dd5"):
        d21.votePositive(subjectAddr, {"from": accounts[10]})

def test_vote_negative(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    [subjectAAddr, subjectBAddr, subjectCAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    d21.voteNegative(subjectCAddr, {"from": accounts[10]})
    subjectC = d21.getSubject(subjectCAddr)
    assert subjectC[1] == -1

def test_vote_negative_after_deadline(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    [subjectAAddr, subjectBAddr, subjectCAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    brownie.chain.sleep(7 * 24 * 60 * 60)
    brownie.chain.mine()
    with brownie.reverts("typed error: 0x7a19ed05"):
        d21.voteNegative(subjectCAddr, {"from": accounts[10]})

def test_vote_negative_without_registration(d21, accounts):
    d21.addSubject("a")
    subjectAddr = d21.getSubjects()[0]
    with brownie.reverts("typed error: 0xd4e876ef"):
        d21.voteNegative(subjectAddr, {"from": accounts[10]})

def test_vote_negative_for_unregistred_subject(d21, accounts):
    d21.addVoter(accounts[10], {"from": accounts[0]})
    with brownie.reverts("typed error: 0xcff887c5"):
        d21.voteNegative(accounts[1], {"from": accounts[10]})

def test_vote_negative_for_an_already_voted_for_subject_1(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x26519dd5"):
        d21.voteNegative(subjectAAddr, {"from": accounts[10]})

def test_vote_negative_for_an_already_voted_for_subject_2(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x26519dd5"):
        d21.voteNegative(subjectBAddr, {"from": accounts[10]})

def test_vote_negative_twice(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    d21.addSubject("d", {"from": accounts[4]})
    [
        subjectAAddr,
        subjectBAddr,
        subjectCAddr,
        subjectDAddr
    ] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    d21.voteNegative(subjectCAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0xb51b19df"):
        d21.voteNegative(subjectDAddr, {"from": accounts[10]})

def test_vote_negative_without_positive(d21, accounts):
    d21.addSubject("a")
    subjectAddr = d21.getSubjects()[0]
    d21.addVoter(accounts[10], {"from": accounts[0]})
    with brownie.reverts("typed error: 0x94cb94b2"):
        d21.voteNegative(subjectAddr, {"from": accounts[10]})

def test_vote_negative_without_two_positives(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x94cb94b2"):
        d21.voteNegative(subjectBAddr, {"from": accounts[10]})

def test_vote_positive_after_negative(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    d21.addSubject("d", {"from": accounts[4]})
    [
        subjectAAddr,
        subjectBAddr,
        subjectCAddr,
        subjectDAddr
    ] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    d21.voteNegative(subjectCAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x8a97940b"):
        d21.votePositive(subjectDAddr, {"from": accounts[10]})

def test_add_already_added_subject_with_votes(d21, accounts):
    d21.addSubject("a")
    subject = d21.getSubjects()[0]
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subject, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x2f2eb0c9"):
        d21.addSubject("a")

def test_add_already_added_voter_with_first_vote(d21, accounts):
    d21.addSubject("a")
    subject = d21.getSubjects()[0]
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subject, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x7c722b56"):
        d21.addVoter(accounts[10], {"from": accounts[0]})

def test_add_already_added_voter_with_second_vote(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x7c722b56"):
        d21.addVoter(accounts[10], {"from": accounts[0]})

def test_add_already_added_voter_with_third_vote(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    [subjectAAddr, subjectBAddr, subjectCAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    d21.voteNegative(subjectCAddr, {"from": accounts[10]})
    with brownie.reverts("typed error: 0x7c722b56"):
        d21.addVoter(accounts[10], {"from": accounts[0]})

def test_get_init_remaining_time(d21):
    t = d21.getRemainingTime()
    assert t == 7 * 24 * 60 * 60

def test_get_remaining_time_after_a_day(d21):
    brownie.chain.sleep(24 * 60 * 60)
    brownie.chain.mine()
    t = d21.getRemainingTime()
    tt = 6 * 24 * 60 * 60
    assert tt - 1000 < t < tt + 1000

def test_get_remaining_time_after_a_week(d21):
    brownie.chain.sleep(7 * 24 * 60 * 60)
    brownie.chain.mine()
    t = d21.getRemainingTime()
    assert t == 0

def test_get_remaining_time_after_more_than_a_week(d21):
    brownie.chain.sleep(8 * 24 * 60 * 60)
    brownie.chain.mine()
    t = d21.getRemainingTime()
    assert t == 0

def test_get_results_three_non_negative_subjects(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    [subjectAAddr, subjectBAddr, subjectCAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.addVoter(accounts[11], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectCAddr, {"from": accounts[10]})
    d21.votePositive(subjectCAddr, {"from": accounts[11]})
    res = d21.getResults()
    assert len(res) == 3
    assert res[0][0] == "c" and res[0][1] == 2
    assert res[1][0] == "a" and res[1][1] == 1
    assert res[2][0] == "b" and res[2][1] == 0

def test_get_results_three_subjects(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    d21.addSubject("c", {"from": accounts[3]})
    [subjectAAddr, subjectBAddr, subjectCAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.addVoter(accounts[11], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    d21.votePositive(subjectCAddr, {"from": accounts[10]})
    d21.voteNegative(subjectBAddr, {"from": accounts[10]})
    d21.votePositive(subjectCAddr, {"from": accounts[11]})
    res = d21.getResults()
    assert len(res) == 3
    assert res[0][0] == "c" and res[0][1] == 2
    assert res[1][0] == "a" and res[1][1] == 1
    assert res[2][0] == "b" and res[2][1] == -1

def test_get_results_no_subjects(d21):
    res = d21.getResults()
    assert len(res) == 0

def test_get_results_one_subject(d21, accounts):
    d21.addSubject("a")
    res = d21.getResults()
    assert len(res) == 1

def test_get_results_two_subjects_ordered(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectAAddr, {"from": accounts[10]})
    res = d21.getResults()
    assert len(res) == 2
    assert res[0][0] == "a" and res[0][1] == 1
    assert res[1][0] == "b" and res[1][1] == 0

def test_get_results_two_subjects_reverse_ordered(d21, accounts):
    d21.addSubject("a", {"from": accounts[1]})
    d21.addSubject("b", {"from": accounts[2]})
    [subjectAAddr, subjectBAddr] = d21.getSubjects()
    d21.addVoter(accounts[10], {"from": accounts[0]})
    d21.votePositive(subjectBAddr, {"from": accounts[10]})
    res = d21.getResults()
    assert len(res) == 2
    assert res[0][0] == "b" and res[0][1] == 1
    assert res[1][0] == "a" and res[1][1] == 0

def test_complex_scenario(d21, accounts):
    subjects = [
        {"name": "a", "addr": accounts[1], "votes": 0},
        {"name": "b", "addr": accounts[2], "votes": 5},
        {"name": "c", "addr": accounts[3], "votes": -2},
        {"name": "d", "addr": accounts[4], "votes": 2},
        {"name": "e", "addr": accounts[5], "votes": 3},
        {"name": "f", "addr": accounts[6], "votes": 1},
        {"name": "g", "addr": accounts[7], "votes": 8},
        {"name": "h", "addr": accounts[8], "votes": -3},
        {"name": "i", "addr": accounts[9], "votes": -1}
    ]
    positiveVotes = [
        [accounts[10], subjects[0]],
        [accounts[10], subjects[1]],
        [accounts[11], subjects[8]],
        [accounts[12], subjects[7]],
        [accounts[11], subjects[6]],
        [accounts[13], subjects[5]],
        [accounts[13], subjects[1]],
        [accounts[14], subjects[1]],
        [accounts[14], subjects[6]],
        [accounts[15], subjects[1]],
        [accounts[15], subjects[6]],
        [accounts[16], subjects[1]],
        [accounts[16], subjects[6]],
        [accounts[17], subjects[6]],
        [accounts[18], subjects[4]],
        [accounts[0], subjects[3]],
        [accounts[8], subjects[6]],
        [accounts[8], subjects[3]],
        [accounts[9], subjects[6]],
        [accounts[0], subjects[4]],
        [accounts[19], subjects[4]],
        [accounts[19], subjects[6]],
    ]
    negativeVotes = [
        [accounts[10], subjects[7]],
        [accounts[11], subjects[7]],
        [accounts[13], subjects[7]],
        [accounts[14], subjects[7]],
        [accounts[15], subjects[0]],
        [accounts[16], subjects[8]],
        [accounts[8], subjects[8]],
        [accounts[0], subjects[2]],
        [accounts[19], subjects[2]],
    ]
    for subject in subjects:
        d21.addSubject(subject["name"], {"from": subject["addr"]})
    for i in range(0, 15):
        with brownie.reverts("dev: OnlyOwner"):
            d21.addVoter(accounts[i], {"from": accounts[i + 1]})
    for i in range(8, 25):
        d21.addVoter(accounts[i], {"from": accounts[0]})
    d21.addVoter(accounts[0], {"from": accounts[0]})
    for voterAddr, subject in positiveVotes:
        d21.votePositive(subject["addr"], {"from": voterAddr})
    for voterAddr, subject in negativeVotes:
        d21.voteNegative(subject["addr"], {"from": voterAddr})
    res = d21.getResults()
    sortedSubjects = sorted(subjects, key=lambda subject: int(subject["votes"]),
        reverse=True)
    assert len(res) == len(sortedSubjects)
    for index, subject in enumerate(sortedSubjects):
        assert (
            res[index][0] == subject["name"] and
            res[index][1] == subject["votes"]
        )
    brownie.chain.sleep(7 * 24 * 60 * 60)
    brownie.chain.mine()
    with brownie.reverts("typed error: 0x7a19ed05"):
        d21.votePositive(subjects[0]["addr"], {"from": accounts[9]})
    res2 = d21.getResults()
    assert len(res2) == len(sortedSubjects)
    for index, subject in enumerate(sortedSubjects):
        assert (
            res2[index][0] == subject["name"] and
            res2[index][1] == subject["votes"]
        )
